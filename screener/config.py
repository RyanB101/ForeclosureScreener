"""Buy box, cost assumptions and scoring weights.

Cost figures come from the sale-rules brief (sale-rules/philly-sheriff-sale-rules.md
in the project files). Everything here is a first-pass screening assumption, not
underwriting: the underwriting thread replaces these with property-level numbers.
"""

# --- Buy box (ryan) ---------------------------------------------------------
FLIP_PROFIT_TARGET = 50_000          # $ profit on a flip
VALUE_ADD_CASH_YIELD = 0.12          # yearly return on cash for a hold
IDEAL_ALL_IN_CEILING = 300_000       # bid + rehab, ideal flip size
MAX_CASH = 1_000_000                 # hard ceiling, total capital

# --- Sheriff sale costs (rules brief, sections 3 and 10) --------------------
BUYERS_PREMIUM = 0.015               # of the price, on top of the bid
SALE_FEES = 70                       # two $35 fees
LEGAL_PER_LOT = 3_750                # petition to compel deed and/or ejectment
OCCUPIED_RESERVE = 7_500             # cash for keys or ejectment when not shown vacant

# --- Hold timeline (months) -------------------------------------------------
MONTHS_TO_DEED = 12                  # base case, 9 to 15
MONTHS_REHAB_AND_SALE = 6
MONTHS_EJECTMENT = 4                 # added when the property may be occupied

# --- Carry ------------------------------------------------------------------
RE_TAX_RATE = 0.013998               # Philadelphia real estate tax, of market value
INSURANCE_PER_MONTH = 250            # vacant-property policy
UTILITIES_SECURING_PER_MONTH = 150

# --- Exit costs on a flip ---------------------------------------------------
SELL_TRANSFER_TAX = 0.02289          # seller half of 4.578%
SELL_COMMISSION = 0.05
SELL_OTHER = 0.01

# --- Rehab (interior unseen) ------------------------------------------------
# $ per livable sq ft by condition band, Philadelphia rowhome scale.
REHAB_PSF = {"light": 40, "medium": 65, "heavy": 95, "gut": 130}
REHAB_MIN = 25_000
REHAB_CONTINGENCY = 0.15             # we can't see inside
# OPA exterior/interior condition code -> band. Higher codes are worse
# (6 = vacant, 7 = sealed / structurally compromised).
CONDITION_BAND = {1: "light", 2: "light", 3: "light", 4: "medium", 5: "heavy", 6: "gut", 7: "gut"}
DEFAULT_BAND = "heavy"               # no condition on record

# --- Value estimate ---------------------------------------------------------
MARKET_SALE_MIN_PRICE = 25_000       # drop nominal / family transfers
MARKET_PSF_RANGE = (15, 1_000)
MARKET_MIN_AREA = 400
MARKET_CATEGORIES = ("SINGLE FAMILY", "MULTI FAMILY")
# $1 placeholder lots: estimate the lender's opening bid as this quantile of
# min bid / debt across lots that have a real bid posted.
PLACEHOLDER_BID_QUANTILE = 0.75

# --- Value-add hold (only when a rent file is supplied) ---------------------
HOLD_EXPENSE_RATIO = 0.40            # vacancy, taxes, insurance, repairs, mgmt

# --- Scoring ----------------------------------------------------------------
WEIGHTS = {"financial": 0.40, "physical": 0.20, "market": 0.20, "upside": 0.20}
ELEVATED_SALE_RISK_PENALTY = 8
WATCH_PENALTY = 4
SHORTLIST_SIZE = 25                  # roughly half of lots get postponed or stayed
BENCH_SIZE = 25

KILL_CATEGORIES = ("INDUSTRIAL", "SPECIAL PURPOSE", "GARAGE - RESIDENTIAL", "GARAGE - COMMERCIAL")
# Zoning that allows more units than a single-family rowhome.
MULTI_UNIT_ZONES = ("RM", "RMX", "CMX", "IRMX")
FLOOD_ZONES_HIGH_RISK = ("A", "AE", "AO", "AH", "VE", "V")
