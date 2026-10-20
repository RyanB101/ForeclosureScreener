"""Exercise the full screen on a tiny fixture with the network sources stubbed."""

import pandas as pd
import pytest

from screener import screen, sources

MASTER = pd.DataFrame({
    "Auction ID": [1, 2, 3, 4],
    "Address (OPA style)": ["1 A ST", "2 B ST", "3 C ST", "4 D ST"],
    "ZIP": [19148, 19148, 19148, 19140],
    "Sale risk": ["Normal", "Elevated", "Normal", "Normal"],
    "Minimum bid": [20_000, 1, 300_000, 15_000],
    "$1 placeholder": ["N", "Y", "N", "N"],
    "Debt amount": [150_000, 200_000, 400_000, 100_000],
    "Min bid / debt": [20_000 / 150_000, None, 0.75, 0.15],
})
PARCELS = pd.DataFrame({"Auction ID": [1, 2, 3, 4], "OPA": [11, 22, 33, 44],
                        "ZIP": [19148, 19148, 19148, 19140]})


def opa_rows():
    return pd.DataFrame({
        "parcel_number": ["000000011", "000000022", "000000033", "000000044"],
        "category_code_description": ["SINGLE FAMILY", "MULTI FAMILY", "SINGLE FAMILY", "INDUSTRIAL"],
        "total_livable_area": [1200, 1800, 1000, 5000],
        "total_area": [900, 2500, 700, 6000],
        "year_built": [1925, 1915, 1950, 1960],
        "number_stories": [2, 3, 2, 1],
        "zoning": ["RSA5", "RM1", "RSA5", "I2"],
        "market_value": [180_000, 250_000, 200_000, 300_000],
        "exterior_condition": [4, 6, 3, 4],
        "interior_condition": [None, None, 4, None],
        "homestead_exemption": [0, 0, 80_000, 0],
        "mailing_street": ["X", "Y", "3 C ST", "Z"],
        "location": ["1 A ST", "2 B ST", "3 C ST", "4 D ST"],
        "lat": [39.93, 39.93, 39.93, 40.0], "lng": [-75.17, -75.17, -75.17, -75.13],
    })


@pytest.fixture
def stubbed(monkeypatch):
    monkeypatch.setattr(sources, "properties", lambda o: opa_rows())
    monkeypatch.setattr(sources, "violations", lambda o: pd.DataFrame({
        "opa_account_num": ["000000022", "000000022"], "violationstatus": ["OPEN", "CLOSED"],
        "violationdate": ["2026-01-01", "2025-01-01"], "violationcodetitle": ["VACANT", "WEEDS"]}))
    monkeypatch.setattr(sources, "permits", lambda o: pd.DataFrame(columns=["opa_account_num"]))
    monkeypatch.setattr(sources, "unsafe", lambda o: pd.DataFrame(columns=["opa_account_num"]))
    monkeypatch.setattr(sources, "imminently_dangerous", lambda o: None)  # source down
    monkeypatch.setattr(sources, "deeds", lambda o: None)
    monkeypatch.setattr(sources, "vacancy", lambda o: pd.DataFrame({"OPA_ID": ["000000022"]}))
    monkeypatch.setattr(sources, "flood_zones", lambda p: pd.DataFrame({"opa": p["opa"], "flood_zone": ""}))
    return pd.DataFrame({"zip": ["19148", "19140"], "n": [300, 200], "psf_med": [220.0, 80.0],
                         "psf_p75": [300.0, 110.0], "sale_to_mv": [1.1, 1.0],
                         "n_prev": [280, 210], "psf_med_prev": [210.0, 82.0]})


def run(market):
    master = MASTER.copy()
    parcels = PARCELS.copy()
    parcels["opa"] = screen.opa9(parcels["OPA"])
    parcels["ZIP"] = parcels["ZIP"].astype(str)
    master["ZIP"] = master["ZIP"].astype(str)
    par = screen.value(screen.enrich(parcels), market)
    return screen.cut(screen.score(screen.lots(master, par))).set_index("Auction ID"), par


def test_full_screen(stubbed):
    lots, par = run(stubbed)
    # Unsafe answered with no rows -> real False; imminently dangerous source down -> unknown.
    assert par["unsafe"].eq(False).all()
    assert "imminently_dangerous" not in par
    # Owner-occupied hint from homestead / mailing address.
    assert par.set_index("opa").loc["000000033", "owner_occupied_hint"]
    # $1 placeholder gets an estimated opening bid from posted lots, not $1.
    assert lots.loc[2, "floor_bid"] > 1 and "est." in lots.loc[2, "floor_bid_basis"]
    # Vacant (city flag) lot skips the ejectment months and reserve.
    assert lots.loc[2, "hold_months"] < lots.loc[1, "hold_months"]
    # Industrial: no residential value, killed on use rather than crashing the score.
    assert lots.loc[4, "list"] == "Kill" and "outside the buy box" in lots.loc[4, "kill_reason"]
    assert lots.loc[3, "list"] == "Kill" and "No margin" in lots.loc[3, "kill_reason"]
    assert lots.loc[1, "list"] == "Shortlist"
    # Money: max bid leaves exactly the $50k target at that price.
    r = lots.loc[1]
    net = r["arv"] * (1 - 0.02289 - 0.05 - 0.01)
    profit = net - r["rehab"] - r["carry"] - r["soft_costs"] - r["max_bid_flip"] * 1.015
    assert abs(profit - 50_000) < 100


def test_runs_with_every_source_down(monkeypatch):
    for name in ("properties", "violations", "permits", "unsafe", "imminently_dangerous",
                 "deeds", "vacancy", "flood_zones"):
        monkeypatch.setattr(sources, name, lambda *a: None)
    lots, _ = run(None)
    assert (lots["list"] == "Not scored").all()
