import datetime as dt
import unittest

from comps import find_comps, miles, value
from zip_stats import stats

ASOF = dt.date(2026, 10, 20)


def sale(i, ppsf, dlat=0.0, sqft=1000, cat="SINGLE FAMILY", date="2026-06-01", z="19143"):
    return {"opa": str(i), "street_address": f"{i} TEST ST", "sale_date": date,
            "price": str(ppsf * sqft), "price_per_sqft": str(ppsf), "sqft": str(sqft),
            "category": cat, "lat": str(39.95 + dlat), "lng": "-75.2", "zip_code": z}


SUBJ = {"opa": "999", "location": "1 SUBJ ST", "zip_code": "19143", "category": "SINGLE FAMILY",
        "sqft": "1000", "lat": "39.95", "lng": "-75.2"}


class CompsTest(unittest.TestCase):
    def test_miles(self):
        self.assertAlmostEqual(miles(39.95, -75.2, 40.95, -75.2), 69.1, delta=0.2)

    def test_filters_and_values(self):
        sales = [sale(i, 100 + 10 * i) for i in range(10)]
        sales += [sale(50, 500, cat="MULTI FAMILY"), sale(51, 500, sqft=3000),
                  sale(52, 500, date="2024-01-01"), sale(53, 500, dlat=0.05),
                  dict(sale(54, 500), new_build="Y")]
        comps, r = find_comps(SUBJ, sales, ASOF)
        self.assertEqual(len(comps), 10)
        self.assertLessEqual(r, 0.35)
        v = value(SUBJ, sales, ASOF)
        self.assertEqual(v["ppsf_median"], 145)
        self.assertLess(v["as_is_value"], v["market_value_est"])
        self.assertLess(v["market_value_est"], v["arv"])
        self.assertEqual(v["confidence"], "High")

    def test_radius_widens(self):
        sales = [sale(i, 150, dlat=0.009) for i in range(6)]  # ~0.62 mi away
        _, r = find_comps(SUBJ, sales, ASOF)
        self.assertAlmostEqual(r, 0.62, delta=0.02)

    def test_zip_stats_yoy(self):
        rows = [sale(1, 100, date="2026-05-01"), sale(2, 100, date="2025-05-01")]
        rows[0]["price"], rows[1]["price"] = "110000", "100000"
        s = stats(rows, ASOF)[0]
        self.assertEqual(s["price_yoy_pct"], 10.0)


if __name__ == "__main__":
    unittest.main()
