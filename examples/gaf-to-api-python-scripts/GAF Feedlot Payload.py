import json
import warnings

import openpyxl
import requests

warnings.simplefilter("ignore")  # openpyxl DrawingML / data-validation noise

# =========================
# CONFIG
# =========================
XLSX_PATH = r"your path here"
CERT_PATH = r"your path here"
KEY_PATH = r"your path here"
API_URL = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/feedlot"

# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
ws = wb["Data input"]
wv = wb["Data input - vegetation"]

# =========================
# SHEET LAYOUT CONSTANTS
# =========================
# --- Data input: header block ---
ROW_REGION_CODE = 8  # D8  -> numeric state/region code
ROW_SYSTEM_CODE = 10  # D10 -> numeric production system code

# --- Data input: livestock groups (4 groups x 3 stay classes) ---
GROUP_START_ROWS = [15, 28, 41, 54]  # row of "Livestock Numbers (N)" for each group
STAY_COLS = ["C", "D", "E"]  # Domestic / Export mid fed / Export long fed
# Offsets from a group's start row:
OFF_LIVESTOCK = 0
OFF_DURATION = 1
OFF_LIVEWEIGHT = 2
OFF_DAILY_INTAKE = 3
OFF_NDF = 4
OFF_ETHER = 5
OFF_DMD = 6
OFF_CRUDE_PROTEIN = 7
OFF_NITROGEN_RETENTION = 8

# --- Data input: energy / transport / feed / fertiliser ---
ROW_DIESEL = 67  # C
ROW_PETROL = 68  # C
ROW_LPG = 69  # C
ROW_ELECTRICITY_USE = 70  # C
ROW_ELECTRICITY_RENEWABLE = 71  # C
ROW_DISTANCE = 75  # C
ROW_TRUCK_CODE = 76  # C -> numeric truck type code
ROW_GRAIN = 100  # C
ROW_COTTONSEED = 101  # C
ROW_HAY = 102  # C
ROW_HERBICIDE_OTHER = 103  # C  "Herbicides/pesticides"          -> API herbicideOther
ROW_HERBICIDE = 104  # C  "Herbicide (Paraquat/Glyphosate)" -> API herbicide
ROW_UREA_PASTURE = 107  # C dryland / D irrigated
ROW_UREA_CROPS = 108  # C dryland / D irrigated
ROW_SINGLE_SUPER = 110  # C
ROW_LIMESTONE = 111  # C
ROW_LIMESTONE_FRACTION = 112  # C

# --- Data input: purchase / sale inventory ---
ROW_PURCHASE_HEAD = 82
ROW_PURCHASE_WEIGHT = 83
ROW_PURCHASE_SOURCE = 87  # C = breeding herd region, D = trade region
ROW_SALE_HEAD = 93
ROW_SALE_WEIGHT = 94

# --- Data input - vegetation: 4 stacked blocks ---
VEG_START_ROWS = [2, 12, 22, 32]  # row of "State" for each block
VEG_OFF_REGION = 1
VEG_OFF_SPECIES = 2
VEG_OFF_SOIL = 3
VEG_OFF_AREA = 4
VEG_OFF_AGE = 5
VEG_OFF_ALLOCATION = 7  # "Allocation to feedlot"
VEG_COL = "D"


# =========================
# LOOKUPS
# =========================
# >>> ENTERPRISE-SPECIFIC: region code (Data input D8) -> API state.
# Codes come from the Electricity sheet (R2:S10).
STATE_LOOKUP = {
    1: "act",
    2: "nsw",
    3: "tas",
    4: "sw wa",
    5: "sa",
    6: "vic",
    7: "qld",
    8: "nt",
    9: "nw wa",
}

# >>> ENTERPRISE-SPECIFIC: production system code (Data input D10) -> API system.
# Codes come from the Agricultural soils sheet (B8:C11).
SYSTEM_LOOKUP = {
    1: "Drylot",
    2: "Solid Storage",
    3: "Composting",
    4: "Uncovered anaerobic lagoon",
}

# >>> ENTERPRISE-SPECIFIC: truck type code (Data input C76) -> API truckType.
# Codes come from the Transport sheet (C7:D9).
TRUCK_LOOKUP = {
    1: "4 Deck Trailer",
    2: "6 Deck Trailer",
    3: "B-Double",
}

# >>> ENTERPRISE-SPECIFIC: breeder-operation purchase/sale columns (C..J on
# rows 81/92) in workbook order, mapped to their API category names.
BREEDER_COLUMNS = [
    ("C", "bullsGt1"),
    ("D", "steersLt1"),
    ("E", "steers1To2"),
    ("F", "steersGt2"),
    ("G", "cowsGt2"),
    ("H", "heifersLt1"),
    ("I", "heifers1To2"),
    ("J", "heifersGt2"),
]

# >>> ENTERPRISE-SPECIFIC: trade-cattle columns (K..M). The workbook labels
# these only as "Steers" / "Heifers" / "Steers" with no age class, because it
# just sums them for total trade liveweight. K and L are confirmed against the
# EAP export for this property; M carries no data there, so its category is an
# assumption. Change the third entry if the true class differs.
TRADE_COLUMNS = [
    ("K", "steers1To2Traded"),
    ("L", "heifers1To2Traded"),
    ("M", "steersGt2Traded"),
]

# >>> ENTERPRISE-SPECIFIC: the same three trade columns on the SALE side.
# The EAP export for this property files traded purchases under the "...Traded"
# categories but traded sales under the plain categories, so the sale mapping is
# deliberately different from TRADE_COLUMNS above. This keeps the GAF payload
# identical to the EAP payload. If the API is meant to receive traded sales as
# "...Traded", swap these for the TRADE_COLUMNS names.
SALE_TRADE_COLUMNS = [
    ("K", "steers1To2"),
    ("L", "heifers1To2"),
    ("M", "steersGt2"),
]

# Every API category, so that both blocks always emit all 16.
ALL_CATEGORIES = [c for _, c in BREEDER_COLUMNS] + [
    "bullsGt1Traded",
    "steersLt1Traded",
    "steers1To2Traded",
    "steersGt2Traded",
    "cowsGt2Traded",
    "heifersLt1Traded",
    "heifers1To2Traded",
    "heifersGt2Traded",
]

# >>> ENTERPRISE-SPECIFIC: enum defaults used when an array would otherwise be
# empty (the API rejects empty repeating arrays).
DEFAULT_PURCHASE_SOURCE = "sth NSW/VIC/sth SA"
DEFAULT_OTHER_FERTILISER = "Monoammonium phosphate (MAP)"
DEFAULT_VEG_REGION = "South West"
DEFAULT_VEG_SPECIES = "Mixed species (Environmental Plantings)"
DEFAULT_VEG_SOIL = "Loams & Clays"


# =========================
# HELPERS
# =========================
def cell(sheet, col, row):
    """Raw cell value."""
    return sheet[f"{col}{row}"].value


def num(sheet, col, row, default=0):
    """Numeric cell value, falling back to a default."""
    v = cell(sheet, col, row)
    if v is None or str(v).strip() == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def pct(sheet, col, row, default=0):
    """Workbook stores these as fractions (0.81); the API wants percent (81)."""
    return num(sheet, col, row, default) * 100


def text(sheet, col, row, default=""):
    """String cell value, falling back to a default."""
    v = cell(sheet, col, row)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip()


def lookup_code(sheet, col, row, table, label, default):
    """Decode a numeric lookup code, warning if the code is unrecognised."""
    v = cell(sheet, col, row)
    try:
        code = int(float(v))
    except (TypeError, ValueError):
        print(f"WARNING: {label} code at {col}{row} is empty or non-numeric "
              f"({v!r}); defaulting to {default!r}")
        return default
    if code not in table:
        print(f"WARNING: unknown {label} code {code} at {col}{row}; "
              f"defaulting to {default!r}")
        return default
    return table[code]


def normalize_enum(value, allowed, label, default):
    """Check a free-text workbook value against the API's allowed values."""
    if value not in allowed:
        print(f"WARNING: unexpected {label} value {value!r}; "
              f"defaulting to {default!r}")
        return default
    return value


# =========================
# BUILDERS
# =========================
def build_stays(start_row):
    """stays[] for one group — one entry per stay class with livestock > 0."""
    stays = []
    for col in STAY_COLS:
        livestock = num(ws, col, start_row + OFF_LIVESTOCK)
        if livestock <= 0:
            continue
        stays.append(
            {
                "livestock": livestock,
                "stayAverageDuration": num(ws, col, start_row + OFF_DURATION),
                "liveweight": num(ws, col, start_row + OFF_LIVEWEIGHT),
                "dryMatterDigestibility": pct(ws, col, start_row + OFF_DMD),
                "crudeProtein": pct(ws, col, start_row + OFF_CRUDE_PROTEIN),
                "nitrogenRetention": pct(ws, col, start_row + OFF_NITROGEN_RETENTION),
                "dailyIntake": num(ws, col, start_row + OFF_DAILY_INTAKE),
                "ndf": pct(ws, col, start_row + OFF_NDF),
                "etherExtract": pct(ws, col, start_row + OFF_ETHER),
            }
        )
    return stays


def default_stay():
    return {
        "livestock": 0,
        "stayAverageDuration": 0,
        "liveweight": 0,
        "dryMatterDigestibility": 0,
        "crudeProtein": 0,
        "nitrogenRetention": 0,
        "dailyIntake": 0,
        "ndf": 0,
        "etherExtract": 0,
    }


def build_groups():
    """groups[] — one entry per group carrying livestock."""
    groups = []
    for start_row in GROUP_START_ROWS:
        stays = build_stays(start_row)
        if stays:
            groups.append({"stays": stays})

    if not groups:
        groups = [{"stays": [default_stay()]}]
    return groups


def build_fertiliser():
    """fertiliser{} — the workbook has no 'other fertilisers' section, so that
    array always falls back to a single zeroed entry."""
    return {
        "singleSuperphosphate": num(ws, "C", ROW_SINGLE_SUPER),
        "pastureDryland": num(ws, "C", ROW_UREA_PASTURE),
        "pastureIrrigated": num(ws, "D", ROW_UREA_PASTURE),
        "cropsDryland": num(ws, "C", ROW_UREA_CROPS),
        "cropsIrrigated": num(ws, "D", ROW_UREA_CROPS),
        "otherFertilisers": [
            {
                "otherType": DEFAULT_OTHER_FERTILISER,
                "otherDryland": 0,
                "otherIrrigated": 0,
            }
        ],
    }


def build_purchases(breeder_source, trade_source):
    """purchases{} — every category present, populated ones from the workbook."""
    purchases = {
        c: [{"head": 0, "purchaseWeight": 0, "purchaseSource": DEFAULT_PURCHASE_SOURCE}]
        for c in ALL_CATEGORIES
    }
    for col, category in BREEDER_COLUMNS:
        head = num(ws, col, ROW_PURCHASE_HEAD)
        if head > 0:
            purchases[category] = [
                {
                    "head": head,
                    "purchaseWeight": num(ws, col, ROW_PURCHASE_WEIGHT),
                    "purchaseSource": breeder_source,
                }
            ]
    for col, category in TRADE_COLUMNS:
        head = num(ws, col, ROW_PURCHASE_HEAD)
        if head > 0:
            purchases[category] = [
                {
                    "head": head,
                    "purchaseWeight": num(ws, col, ROW_PURCHASE_WEIGHT),
                    "purchaseSource": trade_source,
                }
            ]
    return purchases


def build_sales():
    """sales{} — every category present, populated ones from the workbook."""
    sales = {c: [{"head": 0, "saleWeight": 0}] for c in ALL_CATEGORIES}
    for col, category in BREEDER_COLUMNS + SALE_TRADE_COLUMNS:
        head = num(ws, col, ROW_SALE_HEAD)
        if head > 0:
            sales[category] = [
                {
                    "head": head,
                    "saleWeight": num(ws, col, ROW_SALE_WEIGHT),
                }
            ]
    return sales


def build_vegetation():
    """vegetation[] — one entry per planting block with area > 0."""
    vegetation = []
    for start_row in VEG_START_ROWS:
        area = num(wv, VEG_COL, start_row + VEG_OFF_AREA)
        if area <= 0:
            continue
        vegetation.append(
            {
                "vegetation": {
                    "region": text(wv, VEG_COL, start_row + VEG_OFF_REGION,
                                   DEFAULT_VEG_REGION),
                    "treeSpecies": text(wv, VEG_COL, start_row + VEG_OFF_SPECIES,
                                        DEFAULT_VEG_SPECIES),
                    "soil": text(wv, VEG_COL, start_row + VEG_OFF_SOIL,
                                 DEFAULT_VEG_SOIL),
                    "area": area,
                    "age": num(wv, VEG_COL, start_row + VEG_OFF_AGE),
                },
                "feedlotProportion": [
                    num(wv, VEG_COL, start_row + VEG_OFF_ALLOCATION)
                ],
            }
        )

    if not vegetation:
        vegetation = [
            {
                "vegetation": {
                    "region": DEFAULT_VEG_REGION,
                    "treeSpecies": DEFAULT_VEG_SPECIES,
                    "soil": DEFAULT_VEG_SOIL,
                    "area": 0,
                    "age": 0,
                },
                "feedlotProportion": [0],
            }
        ]
    return vegetation


# =========================
# BUILD PAYLOAD
# =========================
state = lookup_code(ws, "D", ROW_REGION_CODE, STATE_LOOKUP, "region", "nsw")
system = lookup_code(ws, "D", ROW_SYSTEM_CODE, SYSTEM_LOOKUP, "production system", "Drylot")
truck_type = lookup_code(ws, "C", ROW_TRUCK_CODE, TRUCK_LOOKUP, "truck type", "4 Deck Trailer")

breeder_source = normalize_enum(
    text(ws, "C", ROW_PURCHASE_SOURCE, DEFAULT_PURCHASE_SOURCE),
    {"NT", "nth QLD", "sth/central QLD", "nth NSW", "sth NSW/VIC/sth SA",
     "NSW/SA pastoral zone", "sw WA", "WA pastoral", "TAS"},
    "breeder purchase source",
    DEFAULT_PURCHASE_SOURCE,
)
trade_source = normalize_enum(
    text(ws, "D", ROW_PURCHASE_SOURCE, DEFAULT_PURCHASE_SOURCE),
    {"NT", "nth QLD", "sth/central QLD", "nth NSW", "sth NSW/VIC/sth SA",
     "NSW/SA pastoral zone", "sw WA", "WA pastoral", "TAS"},
    "trade purchase source",
    DEFAULT_PURCHASE_SOURCE,
)

payload = {
    "id": "",
    "state": state,
    "feedlots": [
        {
            "id": "",
            "system": system,
            "groups": build_groups(),
            "fertiliser": build_fertiliser(),
            "purchases": build_purchases(breeder_source, trade_source),
            "sales": build_sales(),
            "diesel": num(ws, "C", ROW_DIESEL),
            "petrol": num(ws, "C", ROW_PETROL),
            "lpg": num(ws, "C", ROW_LPG),
            "electricitySource": "State Grid",
            "electricityRenewable": num(ws, "C", ROW_ELECTRICITY_RENEWABLE),
            "electricityUse": num(ws, "C", ROW_ELECTRICITY_USE),
            "grainFeed": num(ws, "C", ROW_GRAIN),
            "hayFeed": num(ws, "C", ROW_HAY),
            "cottonseedFeed": num(ws, "C", ROW_COTTONSEED),
            "herbicide": num(ws, "C", ROW_HERBICIDE),
            "herbicideOther": num(ws, "C", ROW_HERBICIDE_OTHER),
            "distanceCattleTransported": num(ws, "C", ROW_DISTANCE),
            "truckType": truck_type,
            "limestone": num(ws, "C", ROW_LIMESTONE),
            "limestoneFraction": num(ws, "C", ROW_LIMESTONE_FRACTION),
        }
    ],
    "vegetation": build_vegetation(),
}

# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW")
print("=" * 25)
print(json.dumps(payload, indent=2))
print("=" * 25)

# =========================
# POST TO API
# =========================
headers = {"Content-Type": "application/json"}

response = requests.post(
    API_URL,
    json=payload,
    headers=headers,
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("=" * 25)
print("API RESPONSE")
print("=" * 25)
print("Status code:", response.status_code)
print(response.text)
