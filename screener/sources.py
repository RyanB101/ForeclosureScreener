"""Philadelphia open-data pulls, cached on disk.

Every fetch returns a DataFrame keyed by 9-digit OPA number and never raises on
a network or schema problem: it logs the failure and returns None, so the
screen still runs and the missing fields show as unknown rather than zero. An
empty frame means the source answered and nothing matched.
"""

import hashlib
import json
import logging
import time
from pathlib import Path

import pandas as pd
import requests

CARTO_SQL = "https://phl.carto.com/api/v2/sql"
# City of Philadelphia ArcGIS Online org.
PHL_ARCGIS = "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services"
FLOOD_LAYER = f"{PHL_ARCGIS}/FEMA_100_flood_Plain/FeatureServer/0/query"
VACANCY_LAYER = f"{PHL_ARCGIS}/Vacant_Indicators_Bldg/FeatureServer/0/query"
FEMA_NFHL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
log = logging.getLogger(__name__)


class Unreachable(Exception):
    pass


def _cached(key, fetch):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    data = fetch()
    path.write_text(json.dumps(data))
    return data


def _request(method, url, retries=3, **kw):
    for attempt in range(retries):
        try:
            r = requests.request(method, url, timeout=60, **kw)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ProxyError as e:
            raise Unreachable(f"{url}: blocked by network policy ({e})") from e
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))


def carto(sql):
    data = _cached(sql, lambda: _request("POST", CARTO_SQL, data={"q": sql}))
    if "error" in data:
        raise ValueError(f"Carto error: {data['error']}")
    return pd.DataFrame(data.get("rows", []))


def _in_list(opas):
    return ",".join(f"'{o}'" for o in sorted(set(opas)))


def _safe(name, fn):
    try:
        df = fn()
        log.info("%s: %d rows", name, len(df))
        return df
    except Exception as e:  # noqa: BLE001 - one bad source must not stop the screen
        log.warning("%s: not pulled (%s)", name, e)
        return None


def check_access():
    """Return {host: ok/error} for the hosts the screen needs."""
    out = {}
    for name, url in [("phl.carto.com", f"{CARTO_SQL}?q=SELECT%201"),
                      ("services.arcgis.com", f"{PHL_ARCGIS}?f=json"),
                      ("hazards.fema.gov", FEMA_NFHL.replace("/query", "?f=json"))]:
        try:
            requests.get(url, timeout=20).raise_for_status()
            out[name] = "ok"
        except requests.RequestException as e:
            out[name] = type(e).__name__
    return out


# --- Parcel-level pulls -----------------------------------------------------

def properties(opas):
    sql = (f"SELECT *, ST_Y(the_geom) AS lat, ST_X(the_geom) AS lng "
           f"FROM opa_properties_public WHERE parcel_number IN ({_in_list(opas)})")
    return _safe("opa_properties_public", lambda: carto(sql))


def violations(opas):
    sql = f"SELECT * FROM violations WHERE opa_account_num IN ({_in_list(opas)})"
    return _safe("violations", lambda: carto(sql))


def permits(opas, years=5):
    sql = (f"SELECT * FROM permits WHERE opa_account_num IN ({_in_list(opas)}) "
           f"AND permitissuedate >= now() - interval '{years} years'")
    return _safe("permits", lambda: carto(sql))


def unsafe(opas):
    sql = f"SELECT opa_account_num FROM unsafe WHERE opa_account_num IN ({_in_list(opas)})"
    return _safe("unsafe", lambda: carto(sql))


def imminently_dangerous(opas):
    sql = f"SELECT opa_account_num FROM imm_dang WHERE opa_account_num IN ({_in_list(opas)})"
    return _safe("imm_dang", lambda: carto(sql))


def deeds(opas):
    """Recorded deeds, newest first, for last arm's-length sale."""
    sql = (f"SELECT opa_account_num, document_type, display_date, total_consideration, "
           f"grantors, grantees FROM rtt_summary WHERE opa_account_num IN ({_in_list(opas)}) "
           f"AND document_type ILIKE 'DEED%' ORDER BY display_date DESC")
    return _safe("rtt_summary", lambda: carto(sql))


def _arcgis_point(url, lat, lng, fields):
    params = {"geometry": f"{lng},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "outFields": fields,
              "returnGeometry": "false", "f": "json"}
    key = url + json.dumps(params, sort_keys=True)
    data = _cached(key, lambda: _request("GET", url, params=params))
    if "error" in data:
        raise ValueError(data["error"])
    return [f["attributes"] for f in data.get("features", [])]


def flood_zones(points):
    """points: DataFrame with opa, lat, lng. Returns opa -> flood zone ('' = outside).

    Tries the city's 100-year floodplain layer first, then FEMA's NFHL for the
    zone label. Whichever answers first is used for every parcel.
    """
    def city(lat, lng):
        return "100-yr floodplain" if _arcgis_point(FLOOD_LAYER, lat, lng, "*") else ""

    def fema(lat, lng):
        hits = _arcgis_point(FEMA_NFHL, lat, lng, "FLD_ZONE")
        zone = hits[0].get("FLD_ZONE", "") if hits else ""
        return "" if zone in ("X", "D", "AREA NOT INCLUDED") else zone

    def run():
        pts = points.dropna(subset=["lat", "lng"])
        if pts.empty:
            return pd.DataFrame(columns=["opa", "flood_zone"])
        first = pts.iloc[0]
        for lookup in (city, fema):
            try:
                lookup(first.lat, first.lng)
            except Exception as e:  # noqa: BLE001
                log.info("flood source unavailable: %s", e)
                continue
            return pd.DataFrame([{"opa": p.opa, "flood_zone": lookup(p.lat, p.lng)}
                                 for p in pts.itertuples()])
        raise Unreachable("no flood source reachable")
    return _safe("flood", run)


def vacancy(opas):
    where = f"OPA_ID IN ({_in_list(opas)})"
    params = {"where": where, "outFields": "*", "returnGeometry": "false", "f": "json"}

    def run():
        data = _cached(VACANCY_LAYER + where, lambda: _request("POST", VACANCY_LAYER, data=params))
        if "error" in data:
            raise ValueError(data["error"])
        return pd.DataFrame([f["attributes"] for f in data.get("features", [])])
    return _safe("vacancy", run)


# --- Market pulls -----------------------------------------------------------

def zip_market(zips, cfg):
    """ZIP-level sale stats from OPA's last-sale fields, this year vs last year."""
    cats = ",".join(f"'{c}'" for c in cfg.MARKET_CATEGORIES)
    zl = ",".join(f"'{z}'" for z in sorted(set(zips)))
    lo, hi = cfg.MARKET_PSF_RANGE
    base = (f"FROM opa_properties_public WHERE left(zip_code,5) IN ({zl}) "
            f"AND category_code_description IN ({cats}) "
            f"AND sale_price >= {cfg.MARKET_SALE_MIN_PRICE} "
            f"AND total_livable_area >= {cfg.MARKET_MIN_AREA} "
            f"AND sale_price / total_livable_area BETWEEN {lo} AND {hi}")

    def window(start, end, suffix):
        sql = (f"SELECT left(zip_code,5) AS zip, count(*) AS n{suffix}, "
               f"percentile_cont(0.5) WITHIN GROUP (ORDER BY sale_price / total_livable_area) AS psf_med{suffix}, "
               f"percentile_cont(0.75) WITHIN GROUP (ORDER BY sale_price / total_livable_area) AS psf_p75{suffix}, "
               f"percentile_cont(0.5) WITHIN GROUP (ORDER BY sale_price / NULLIF(market_value,0)) AS sale_to_mv{suffix} "
               f"{base} AND sale_date >= now() - interval '{start} months' "
               f"AND sale_date < now() - interval '{end} months' GROUP BY 1")
        return carto(sql)

    def run():
        cur = window(12, 0, "")
        prev = window(24, 12, "_prev")
        return cur.merge(prev, on="zip", how="left") if len(cur) else cur
    return _safe("zip_market", run)
