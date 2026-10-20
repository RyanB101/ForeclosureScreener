"""Enrich the auction list, estimate value, score and cut to a shortlist."""

import logging

import numpy as np
import pandas as pd

from . import config as C
from . import sources

log = logging.getLogger(__name__)

OPEN_STATUSES = ("OPEN",)


def ok(df):
    return df is not None and len(df) > 0


def truthy(v):
    return bool(v) if v is not None and pd.notna(v) else False


def opa9(s):
    return s.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(9)


def load(master_csv, parcels_csv):
    master = pd.read_csv(master_csv)
    parcels = pd.read_csv(parcels_csv)
    parcels["opa"] = opa9(parcels["OPA"])
    for df in (master, parcels):
        df["ZIP"] = df["ZIP"].astype(str).str.zfill(5)
    return master, parcels


# --- Enrichment -------------------------------------------------------------

def _num(df, col):
    return pd.to_numeric(df[col], errors="coerce") if col in df else np.nan


def _status_open(df):
    # violationstatus is per violation; casestatus stays "IN VIOLATION" while
    # any violation on the case is open, so it overcounts.
    if "violationstatus" not in df:
        return pd.Series(False, index=df.index)
    return df["violationstatus"].astype(str).str.upper().isin(OPEN_STATUSES)


def enrich(parcels):
    opas = parcels["opa"].tolist()
    out = parcels[["Auction ID", "opa", "ZIP"]].copy()

    props = sources.properties(opas)
    if ok(props):
        props["opa"] = opa9(props["parcel_number"])
        keep = {
            "category_code_description": "property_type",
            "building_code_description": "building_type",
            "total_livable_area": "livable_sqft",
            "total_area": "lot_sqft",
            "frontage": "frontage",
            "depth": "depth",
            "year_built": "year_built",
            "number_stories": "stories",
            "number_of_bedrooms": "beds",
            "number_of_bathrooms": "baths",
            "zoning": "zoning",
            "market_value": "opa_market_value",
            "sale_date": "opa_last_sale_date",
            "sale_price": "opa_last_sale_price",
            "exterior_condition": "exterior_condition",
            "interior_condition": "interior_condition",
            "owner_1": "owner_1",
            "owner_2": "owner_2",
            "mailing_street": "mailing_street",
            "location": "opa_location",
            "homestead_exemption": "homestead_exemption",
            "lat": "lat",
            "lng": "lng",
        }
        props = props[["opa"] + [c for c in keep if c in props]].rename(columns=keep)
        out = out.merge(props, on="opa", how="left")
        for col in ("livable_sqft", "lot_sqft", "year_built", "opa_market_value", "opa_last_sale_price",
                    "exterior_condition", "interior_condition", "homestead_exemption", "beds", "stories"):
            if col in out:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        out["year_built"] = out["year_built"].where(out["year_built"] > 1700) if "year_built" in out else np.nan
        # Owner likely lives there: homestead exemption, or tax bills go to the property itself.
        hs = out.get("homestead_exemption", pd.Series(0, index=out.index)).fillna(0) > 0
        same = (out.get("mailing_street", pd.Series("", index=out.index)).fillna("").str.upper().str.strip()
                == out.get("opa_location", pd.Series("", index=out.index)).fillna("").str.upper().str.strip())
        out["owner_occupied_hint"] = hs | same
    out["opa_matched"] = out["property_type"].notna() if "property_type" in out else False

    viol = sources.violations(opas)
    if ok(viol):
        viol["opa"] = opa9(viol["opa_account_num"])
        viol["open"] = _status_open(viol)
        date_col = next((c for c in ("violationdate", "casecreateddate") if c in viol), None)
        agg = viol.groupby("opa").agg(violations_total=("opa", "size"), violations_open=("open", "sum"))
        if date_col:
            agg["violation_latest"] = viol.groupby("opa")[date_col].max().str[:10]
        title = next((c for c in ("violationcodetitle", "violationdescription") if c in viol), None)
        if title:
            agg["open_violation_titles"] = (viol[viol["open"]].groupby("opa")[title]
                                            .apply(lambda s: "; ".join(sorted(set(map(str, s)))[:4])))
        out = out.merge(agg.reset_index(), on="opa", how="left")

    perm = sources.permits(opas)
    if ok(perm):
        perm["opa"] = opa9(perm["opa_account_num"])
        agg = perm.groupby("opa").agg(permits_5yr=("opa", "size"))
        if "permitissuedate" in perm:
            agg["permit_latest"] = perm.groupby("opa")["permitissuedate"].max().str[:10]
        desc = next((c for c in ("typeofwork", "permitdescription", "approvedscopeofwork") if c in perm), None)
        if desc:
            agg["permit_types"] = perm.groupby("opa")[desc].apply(lambda s: "; ".join(sorted(set(map(str, s)))[:3]))
        out = out.merge(agg.reset_index(), on="opa", how="left")

    for name, fn in (("unsafe", sources.unsafe), ("imminently_dangerous", sources.imminently_dangerous)):
        df = fn(opas)
        if df is not None:
            out[name] = out["opa"].isin(set(opa9(df["opa_account_num"])) if len(df) else set())

    deeds = sources.deeds(opas)
    if ok(deeds):
        deeds["opa"] = opa9(deeds["opa_account_num"])
        deeds["total_consideration"] = pd.to_numeric(deeds["total_consideration"], errors="coerce")
        arm = deeds[deeds["total_consideration"] >= C.MARKET_SALE_MIN_PRICE]
        last = arm.groupby("opa").first()[["display_date", "total_consideration", "grantees"]]
        last.columns = ["last_deed_date", "last_deed_price", "last_deed_grantee"]
        last["last_deed_date"] = last["last_deed_date"].astype(str).str[:10]
        out = out.merge(last.reset_index(), on="opa", how="left")

    vac = sources.vacancy(opas)
    if ok(vac):
        id_col = next(c for c in vac.columns if c.upper() == "OPA_ID")
        out["vacancy_indicator"] = out["opa"].isin(set(opa9(vac[id_col])))
    if "lat" in out:
        flood = sources.flood_zones(out[["opa", "lat", "lng"]])
        if ok(flood):
            out = out.merge(flood, on="opa", how="left")

    for col in ("violations_total", "violations_open", "permits_5yr"):
        if col in out and "property_type" in out:
            out[col] = out[col].fillna(0).where(out["opa_matched"])
    return out


# --- Valuation and costs ----------------------------------------------------

def band(row):
    codes = [row.get("exterior_condition"), row.get("interior_condition")]
    codes = [int(c) for c in codes if pd.notna(c) and c > 0]
    if truthy(row.get("imminently_dangerous")) or truthy(row.get("unsafe")):
        return "gut"
    found = C.CONDITION_BAND.get(max(codes), C.DEFAULT_BAND) if codes else C.DEFAULT_BAND
    order = list(C.REHAB_PSF)
    year = row.get("year_built")
    if pd.notna(year) and year < 1980:
        found = max(found, C.BLIND_MIN_BAND_BEFORE_1980, key=order.index)
    return found


def value(par, market, comps=None):
    """Quick same-ZIP value, replaced per parcel by sold-comp values when given.

    comps: one row per OPA with as_is_value and arv (Market and comps thread).
    """
    p = _zip_value(par, market)
    p["value_source"] = np.where(p["arv"].notna(), "same-ZIP OPA sales", None)
    if comps is not None and len(comps):
        c = comps.copy()
        c["opa"] = opa9(c["opa"])
        c = c[c["arv"].notna()].set_index("opa")
        hit = p["opa"].isin(c.index)
        for col in ("as_is_value", "arv"):
            p.loc[hit, col] = p.loc[hit, "opa"].map(c[col])
        p.loc[hit, "value_source"] = "sold comps"
        p["comp_confidence"] = p["opa"].map(c["confidence"]) if "confidence" in c else None
        p["comp_count"] = p["opa"].map(c["comp_count"]) if "comp_count" in c else None
        p["arv"] = np.fmax(p["arv"], p["as_is_value"])
    if "zip_p75_price" in p:
        cap = p["zip_p75_price"] * C.ARV_CAP_X_ZIP_P75
        p["arv_capped"] = p["arv"] > cap
        p["arv"] = p["arv"].where(~p["arv_capped"], cap)
        p["as_is_value"] = np.fmin(p["as_is_value"], p["arv"])
    return p


def _zip_value(par, market):
    p = par.copy()
    if not ok(market) or "opa_market_value" not in p:
        for col in ("as_is_value", "arv", "rehab"):
            p[col] = np.nan
        p["condition_band"] = None
        return p
    p = p.merge(market.rename(columns={"zip": "ZIP"}), on="ZIP", how="left")
    p["condition_band"] = p.apply(band, axis=1)
    area = p["livable_sqft"].where(p["livable_sqft"] > 0)
    est_mv = p["opa_market_value"] * p["sale_to_mv"]
    discount = p["condition_band"].map({"light": 1.0, "medium": 0.9, "heavy": 0.75, "gut": 0.6})
    est_psf = area * p["psf_med"] * discount
    residential = p["property_type"].fillna("").str.startswith(C.RESIDENTIAL)
    p["as_is_value"] = pd.concat([est_mv, est_psf], axis=1).mean(axis=1).where(residential)
    p["arv"] = np.fmax(area * p["psf_p75"], p["as_is_value"])
    psf = p["condition_band"].map(C.REHAB_PSF)
    p["rehab"] = (np.fmax(area * psf, C.REHAB_MIN) * (1 + C.REHAB_CONTINGENCY)).where(area.notna(), 0)
    p["arv"] = p["arv"].where(area.notna(), p["as_is_value"]).where(residential)
    return p


def lots(master, par, rents=None, underwriting=None):
    """Roll parcels up to one row per auction lot and run the money."""
    m = master.copy()
    posted = m[(m["$1 placeholder"] == "N") & m["Min bid / debt"].notna()]
    ratio = posted["Min bid / debt"].quantile(C.PLACEHOLDER_BID_QUANTILE)
    placeholder = m["$1 placeholder"] == "Y"
    m["floor_bid"] = np.where(placeholder, (m["Debt amount"] * ratio).round(-2), m["Minimum bid"])
    m["floor_bid_basis"] = np.where(placeholder, f"est. {ratio:.0%} of debt (bid not posted)", "posted minimum")

    sums = par.groupby("Auction ID")[[c for c in ("opa_market_value", "as_is_value", "arv", "rehab",
                                                   "livable_sqft", "lot_sqft", "violations_open",
                                                   "violations_total", "permits_5yr") if c in par]].sum(min_count=1)
    first = par.groupby("Auction ID").first()
    firsts = [c for c in first.columns if c not in sums.columns and c not in ("ZIP",)]
    lot = sums.join(first[firsts])
    for flag in ("unsafe", "imminently_dangerous", "owner_occupied_hint", "vacancy_indicator"):
        if flag in par:
            lot[flag] = par.groupby("Auction ID")[flag].apply(lambda s: bool(s.fillna(False).astype(bool).any()))
    m = m.merge(lot.reset_index(), on="Auction ID", how="left")
    if "arv" not in m or m["arv"].isna().all():
        return m

    may_be_occupied = ~col(m, "vacancy_indicator", False).fillna(False).astype(bool)
    m["hold_months"] = C.MONTHS_TO_DEED + C.MONTHS_REHAB_AND_SALE + np.where(may_be_occupied, C.MONTHS_EJECTMENT, 0)
    monthly = m["opa_market_value"].fillna(0) * C.RE_TAX_RATE / 12 + C.INSURANCE_PER_MONTH + C.UTILITIES_SECURING_PER_MONTH
    m["carry"] = (monthly * m["hold_months"]).round(-2)
    m["soft_costs"] = C.LEGAL_PER_LOT + C.SALE_FEES + np.where(may_be_occupied, C.OCCUPIED_RESERVE, 0)
    net_sale = m["arv"] * (1 - C.SELL_TRANSFER_TAX - C.SELL_COMMISSION - C.SELL_OTHER)
    costs_ex_bid = m["rehab"] + m["carry"] + m["soft_costs"]
    m["max_bid_flip"] = ((net_sale - costs_ex_bid - C.FLIP_PROFIT_TARGET) / (1 + C.BUYERS_PREMIUM)).round(-2)
    m["profit_at_floor"] = (net_sale - costs_ex_bid - m["floor_bid"] * (1 + C.BUYERS_PREMIUM)).round(-2)
    m["all_in_at_floor"] = (m["floor_bid"] * (1 + C.BUYERS_PREMIUM) + m["rehab"] + m["carry"] + m["soft_costs"]).round(-2)
    m["headroom"] = m["max_bid_flip"] - m["floor_bid"]

    if rents is not None and len(rents):
        r = rents.copy()
        r["ZIP"] = r["zip"].astype(str).str.zfill(5)
        m = m.merge(r[["ZIP", "rent_per_unit"]], on="ZIP", how="left")
        units = np.where(m["property_type"].fillna("").str.contains("MULTI"), 2, 1)
        noi = m["rent_per_unit"] * C.HOLD_RENT_FACTOR * units * 12 * (1 - C.HOLD_EXPENSE_RATIO)
        m["max_bid_hold"] = ((noi / C.VALUE_ADD_CASH_YIELD - costs_ex_bid) / (1 + C.BUYERS_PREMIUM)).round(-2)
        m["cash_yield_at_floor"] = noi / m["all_in_at_floor"]

    if underwriting is not None and len(underwriting):
        # Cross-check from the underwriting model (heavier blind rehab, stricter
        # return test). Shown next to ours, not used in the score.
        u = underwriting.rename(columns={"auction_id": "Auction ID", "best_exit": "uw_best_exit",
                                         "max_bid": "uw_max_bid"})
        m = m.merge(u[["Auction ID", "uw_best_exit", "uw_max_bid"]], on="Auction ID", how="left")
    return m


# --- Scoring ----------------------------------------------------------------

def col(m, name, default=np.nan):
    return m[name] if name in m else pd.Series(default, index=m.index)


def _pct(s):
    return s.rank(pct=True).fillna(0.5) * 100


def score(m):
    if "headroom" not in m:
        m["kill_reason"] = "public-record data not pulled"
        return m
    plays = [c for c in ("max_bid_flip", "max_bid_hold") if c in m]
    best_bid = m[plays].max(axis=1)
    m["best_max_bid"] = best_bid
    m["best_play"] = m[plays].idxmax(axis=1).map({"max_bid_flip": "Flip", "max_bid_hold": "Hold"})
    m["all_in_at_max_bid"] = (best_bid.clip(lower=0) * (1 + C.BUYERS_PREMIUM) + m["rehab"]
                              + m["carry"] + m["soft_costs"]).round(-2)
    m["max_bid_to_as_is"] = (best_bid / m["as_is_value"]).round(2)
    lo, hi = C.FINANCIAL_SCALE
    strength = ((m["max_bid_to_as_is"] - lo) / (hi - lo)).clip(0, 1)
    fit = np.select([m["all_in_at_max_bid"] <= ceiling for ceiling, _ in C.SIZE_FIT],
                    [mult for _, mult in C.SIZE_FIT], 0.4)
    m["score_financial"] = (strength * 100 * fit).round(1)

    phys = pd.Series(70.0, index=m.index)
    worst = pd.concat([col(m, "exterior_condition"), col(m, "interior_condition")], axis=1).max(axis=1)
    phys += worst.map({1: 15, 2: 15, 3: 15, 4: 5, 5: -10, 6: -20, 7: -35}).fillna(-5)
    phys += np.select([m["year_built"] >= 1980, m["year_built"] < 1900], [5, -5], 0)
    phys -= (col(m, "violations_open", 0).fillna(0) * 5).clip(upper=25)
    phys -= np.where(col(m, "unsafe", False).fillna(False).astype(bool), 20, 0)
    phys += np.where(col(m, "permits_5yr", 0).fillna(0) > 0, 5, 0)
    if "flood_zone" in m:
        phys -= np.where(m["flood_zone"].fillna("").str.len() > 0, 15, 0)
    m["score_physical"] = phys.clip(0, 100).round(1)

    trend = (m["psf_med"] / m["psf_med_prev"] - 1)
    m["zip_psf_trend"] = trend.round(3)
    m["score_market"] = (0.5 * _pct(m["n"]) + 0.3 * _pct(trend) + 0.2 * _pct(m["psf_med"])).round(1)

    zoning = m["zoning"].fillna("").str.upper()
    more_units = zoning.str.startswith(C.MULTI_UNIT_ZONES)
    spread = ((m["arv"] - m["as_is_value"]) / m["arv"]).clip(0, 0.6)
    roomy = (m["lot_sqft"] > 1.5 * m["livable_sqft"] / m["stories"].fillna(2).clip(lower=1))
    multi = m["property_type"].fillna("").str.contains("MULTI|MIXED|APARTMENT")
    m["score_upside"] = (spread / 0.6 * 60 + more_units * 15 + roomy * 10 + multi * 15).clip(0, 100).round(1)

    penalty = np.select([m["Sale risk"] == "Elevated", m["Sale risk"] == "Watch"],
                        [C.ELEVATED_SALE_RISK_PENALTY, C.WATCH_PENALTY], 0)
    w = C.WEIGHTS
    m["score_total"] = (w["financial"] * m["score_financial"] + w["physical"] * m["score_physical"]
                        + w["market"] * m["score_market"] + w["upside"] * m["score_upside"] - penalty).round(1)
    m["kill_reason"] = m.apply(kill_reason, axis=1)
    return m


def kill_reason(r):
    ptype = str(r.get("property_type") or "").upper()
    if not truthy(r.get("opa_matched")):
        return "No OPA record matched; check the address before spending time on it"
    if ptype in C.KILL_CATEGORIES:
        return f"Property type outside the buy box ({ptype.title()})"
    if truthy(r.get("imminently_dangerous")):
        return "L&I imminently dangerous: demolition risk"
    if pd.isna(r.get("arv")):
        if ptype not in C.RESIDENTIAL:
            return f"{ptype.title() or 'Unknown use'}: no residential comps, needs its own valuation"
        return "No value estimate (no living area on record or no nearby sales)"
    if r["all_in_at_floor"] > C.MAX_CASH:
        return f"All-in at the opening bid ${r['all_in_at_floor']:,.0f} is over the $1M cash ceiling"
    if r["best_max_bid"] < r["floor_bid"]:
        return (f"No margin: max bid ${r['best_max_bid']:,.0f} is below the opening bid "
                f"${r['floor_bid']:,.0f} ({r['floor_bid_basis']})")
    if r["max_bid_to_as_is"] < C.OUTBID_SHARE_OF_AS_IS:
        return (f"Likely outbid: max bid ${r['best_max_bid']:,.0f} is only {r['max_bid_to_as_is']:.0%} "
                f"of as-is value ${r['as_is_value']:,.0f}")
    return ""


def cut(m):
    if "score_total" not in m:
        m["list"] = "Not scored"
        return m
    alive = m[m["kill_reason"] == ""].sort_values("score_total", ascending=False)
    m["rank"] = pd.Series(range(1, len(alive) + 1), index=alive.index)
    m["list"] = np.select(
        [m["rank"] <= C.SHORTLIST_SIZE, m["rank"] <= C.SHORTLIST_SIZE + C.BENCH_SIZE, m["kill_reason"] != ""],
        ["Shortlist", "Bench", "Kill"], "Pass")
    return m
