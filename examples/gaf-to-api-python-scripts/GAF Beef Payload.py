import openpyxl
import requests
import json

# =========================
# CONFIG
# =========================
# >>> ENTERPRISE-SPECIFIC: path to the completed SB-GAF (seasonal) workbook
XLSX_FILE = r"your path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/beef"
CERT_FILE = r"your path here"
KEY_FILE  = r"your path here"

# >>> ENTERPRISE-SPECIFIC: sheet names inside the SB-GAF workbook
BEEF_SHEET       = "Data input - beef"
VEGETATION_SHEET = "Data input - vegetation"

# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_FILE, data_only=True)
ws_beef = wb[BEEF_SHEET]
ws_veg  = wb[VEGETATION_SHEET]

# =========================
# SAFE VALUE HELPERS
# =========================
def f(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def s(value, default=""):
    if value is None:
        return default
    return str(value).strip().strip('"')

def yes_no(value):
    return str(value).strip().lower() in ["yes", "true", "1"]

def cell(ws, row, col):
    return ws.cell(row=row, column=col).value

# =========================
# >>> ENTERPRISE-SPECIFIC: LOOKUP TABLES
# The SB-GAF workbook stores the farm region as a human-readable label in
# "Data input - beef"!D6 (e.g. "SW WA"), with a numeric code alongside in
# E6. We map the LABEL to the beef API state string, since the label is
# unambiguous and present in the completed workbook. WA is split into two
# rainfall sub-regions (SW WA / NW WA) which map to distinct API codes.
# =========================
STATE_LOOKUP = {
    "nsw":    "nsw",
    "act":    "act",
    "vic":    "vic",
    "qld":    "qld",
    "sa":     "sa",
    "sw wa":  "wa_sw",
    "nw wa":  "wa_nw",
    "tas":    "tas",
    "nt":     "nt",
}

def lookup_state(label):
    key = s(label).lower()
    if key not in STATE_LOOKUP:
        print(f"WARNING: unrecognised region label: {label!r}")
        return ""
    return STATE_LOOKUP[key]

# Normalise savannah-burning dropdown labels to the API's lowercase enums.
# (The workbook uses Title Case and misspells "Coarse" as "Course".)
def norm_enum(value):
    v = s(value).lower()
    if v == "course":
        v = "coarse"
    return v

# =========================
# ANIMAL CLASS -> COLUMN MAP
# In "Data input - beef", each animal class occupies one column (D..N),
# with seasons/attributes running down the rows. The workbook has 11 of
# the API's 16 classes; the 5 traded classes it does not track are sent
# as zeroed defaults so the required arrays are never empty.
# =========================
# column letters: D=4, E=5, F=6, G=7, H=8, I=9, J=10, K=11, L=12, M=13, N=14
CLASS_COLUMNS = {
    "bullsGt1":         4,   # D  Bulls >1
    "steersLt1":        5,   # E  Steers <1
    "steers1To2":       6,   # F  Steers 1-2
    "steersGt2":        7,   # G  Steers >2
    "cowsGt2":          8,   # H  Cows >2
    "heifersLt1":       9,   # I  Heifers <1
    "heifers1To2":     10,   # J  Heifers 1-2
    "heifersGt2":      11,   # K  Heifers >2 (not calving)
    "steersGt2Traded": 12,   # L  Steers >2  (traded)
    "steers1To2Traded":13,   # M  Steers 1-2 (traded)
    "steersLt1Traded": 14,   # N  Steers <1  (traded)
}
# Classes present in the API schema but not tracked in this workbook layout.
CLASS_ZEROED = [
    "bullsGt1Traded",
    "cowsGt2Traded",
    "heifersLt1Traded",
    "heifers1To2Traded",
    "heifersGt2Traded",
]

# >>> ENTERPRISE-SPECIFIC: row numbers for each seasonal attribute.
# Row order within each block is Spring, Summer, Autumn, Winter.
SEASON_ROWS = {
    "spring": {"head": 13, "liveweight": 29, "liveweightGain": 35, "crudeProtein": 41, "dryMatterDigestibility": 47},
    "summer": {"head": 14, "liveweight": 30, "liveweightGain": 36, "crudeProtein": 42, "dryMatterDigestibility": 48},
    "autumn": {"head": 15, "liveweight": 31, "liveweightGain": 37, "crudeProtein": 43, "dryMatterDigestibility": 49},
    "winter": {"head": 16, "liveweight": 32, "liveweightGain": 38, "crudeProtein": 44, "dryMatterDigestibility": 50},
}
ROW_HEAD_SOLD      = 62
ROW_SALE_WEIGHT    = 63
ROW_PURCHASE_HEAD  = 54
ROW_PURCHASE_WT    = 55
ROW_PURCHASE_SRC   = 58

def build_season(col, rows):
    return {
        "head":                   f(cell(ws_beef, rows["head"], col)),
        "liveweight":             f(cell(ws_beef, rows["liveweight"], col)),
        "liveweightGain":         f(cell(ws_beef, rows["liveweightGain"], col)),
        "crudeProtein":           f(cell(ws_beef, rows["crudeProtein"], col)),
        "dryMatterDigestibility": f(cell(ws_beef, rows["dryMatterDigestibility"], col)),
    }

def build_purchases(col):
    head = f(cell(ws_beef, ROW_PURCHASE_HEAD, col))
    wt   = f(cell(ws_beef, ROW_PURCHASE_WT, col))
    src  = s(cell(ws_beef, ROW_PURCHASE_SRC, col), "Dairy origin")
    # When there is no actual purchase, fall back to the known-valid
    # "Dairy origin" enum rather than the workbook's regional source label
    # (which is unverified against the API and could trigger a 422).
    if head == 0:
        src = "Dairy origin"
    # Repeating array must never be empty: always send a single entry.
    return [{
        "head":           head,
        "purchaseWeight": wt,
        "purchaseSource": src if src else "Dairy origin",
    }]

def build_class(col):
    block = {}
    for season, rows in SEASON_ROWS.items():
        block[season] = build_season(col, rows)
    block["headSold"]   = f(cell(ws_beef, ROW_HEAD_SOLD, col))
    block["saleWeight"] = f(cell(ws_beef, ROW_SALE_WEIGHT, col))
    block["purchases"]  = build_purchases(col)
    return block

def zeroed_class():
    season_default = {
        "head": 0, "liveweight": 0, "liveweightGain": 0,
        "crudeProtein": 0, "dryMatterDigestibility": 0,
    }
    return {
        "spring": dict(season_default),
        "summer": dict(season_default),
        "autumn": dict(season_default),
        "winter": dict(season_default),
        "headSold": 0,
        "saleWeight": 0,
        "purchases": [{"head": 0, "purchaseWeight": 0, "purchaseSource": "Dairy origin"}],
    }

# =========================
# BUILD CLASSES BLOCK
# =========================
classes = {}
for class_name, col in CLASS_COLUMNS.items():
    classes[class_name] = build_class(col)
for class_name in CLASS_ZEROED:
    classes[class_name] = zeroed_class()

# =========================
# COWS CALVING  (col D = 4; Spring/Summer/Autumn/Winter down rows 71-74)
# =========================
cows_calving = {
    "spring": f(cell(ws_beef, 71, 4)),
    "summer": f(cell(ws_beef, 72, 4)),
    "autumn": f(cell(ws_beef, 73, 4)),
    "winter": f(cell(ws_beef, 74, 4)),
}

# =========================
# MINERAL SUPPLEMENTATION
# Column F (6) = tonnes of product; Column D (4) = % urea (fraction).
# rows: 77 mineral block, 78 weaner block, 79 dry season mix.
# =========================
mineral_supplementation = {
    "mineralBlock":     f(cell(ws_beef, 77, 6)),
    "mineralBlockUrea": f(cell(ws_beef, 77, 4)),
    "weanerBlock":      f(cell(ws_beef, 78, 6)),
    "weanerBlockUrea":  f(cell(ws_beef, 78, 4)),
    "drySeasonMix":     f(cell(ws_beef, 79, 6)),
    "drySeasonMixUrea": f(cell(ws_beef, 79, 4)),
}

# =========================
# FERTILISER
# Dryland values in column D (4), irrigated in column F (6).
#   row 84 Urea Pasture, row 85 Urea Crops, row 86 Other N (Ammonium Nitrate),
#   row 88 Single Superphosphate, row 89 Limestone total, row 90 Limestone fraction.
# The "other" fertiliser is sent as a single entry with a known-valid enum
# type; when its values are zero this contributes nothing to emissions.
# =========================
other_dryland   = f(cell(ws_beef, 86, 4))
other_irrigated = f(cell(ws_beef, 86, 6))
fertiliser = {
    "singleSuperphosphate": f(cell(ws_beef, 88, 4)),
    "pastureDryland":       f(cell(ws_beef, 84, 4)),
    "pastureIrrigated":     f(cell(ws_beef, 84, 6)),
    "cropsDryland":         f(cell(ws_beef, 85, 4)),
    "cropsIrrigated":       f(cell(ws_beef, 85, 6)),
    "otherFertilisers": [{
        "otherType":      "Monoammonium phosphate (MAP)",
        "otherDryland":   other_dryland,
        "otherIrrigated": other_irrigated,
    }],
}

# =========================
# BUILD SINGLE BEEF BLOCK
# =========================
beef_block = {
    "id": "",
    "classes": classes,
    "limestone":         f(cell(ws_beef, 89, 4)),
    "limestoneFraction": f(cell(ws_beef, 90, 4)),
    "fertiliser": fertiliser,
    "diesel":               f(cell(ws_beef, 95, 4)),
    "petrol":               f(cell(ws_beef, 96, 4)),
    "lpg":                  f(cell(ws_beef, 97, 4)),
    "electricitySource":    s(cell(ws_beef, 93, 3), "State Grid"),
    "electricityRenewable": f(cell(ws_beef, 94, 4)),
    "electricityUse":       f(cell(ws_beef, 98, 4)),
    "grainFeed":            f(cell(ws_beef, 99, 4)),
    "hayFeed":              f(cell(ws_beef, 101, 4)),
    "cottonseedFeed":       f(cell(ws_beef, 100, 4)),
    "herbicide":            f(cell(ws_beef, 102, 4)),
    "herbicideOther":       f(cell(ws_beef, 103, 4)),
    "mineralSupplementation": mineral_supplementation,
    "cowsCalving": cows_calving,
}

# electricitySource in the workbook reads "State Grid (Default)"; strip the
# parenthetical so it matches the API enum "State Grid".
if beef_block["electricitySource"].lower().startswith("state grid"):
    beef_block["electricitySource"] = "State Grid"

# =========================
# BUILD BURNING LIST
# Savannah burning inputs sit on the beef tab (rows 106-109). One burning
# entry is built. allocationToBeef defaults to full allocation ([1]) since
# these inputs are entered under the beef enterprise; when Fire Scar Area
# is zero this contributes nothing regardless.
# =========================
fire_scar_area = f(cell(ws_beef, 108, 9))   # I108
burning = [{
    "burning": {
        "fuel":               norm_enum(cell(ws_beef, 109, 4)),   # D109 (Course->coarse)
        "season":             norm_enum(cell(ws_beef, 106, 9)),   # I106
        "patchiness":         norm_enum(cell(ws_beef, 108, 4)),   # D108
        "rainfallZone":       norm_enum(cell(ws_beef, 106, 4)),   # D106
        "yearsSinceLastFire": f(cell(ws_beef, 107, 9)),           # I107
        "fireScarArea":       fire_scar_area,                     # I108
        "vegetation":         s(cell(ws_beef, 107, 4)),           # D107
    },
    "allocationToBeef": [1],
}]

# =========================
# BUILD VEGETATION LIST
# Read from the vegetation sheet. Each block is 10 rows: labels in column C,
# values in column D. Blocks are detected by scanning column C for "State".
# Only blocks with a non-zero Area of Trees are included; if none, the
# vegetation list is sent empty (the API accepts an empty array).
# =========================
LABEL_COL = 3  # column C
VALUE_COL = 4  # column D

vegetation = []
row = 1
max_row = ws_veg.max_row
while row <= max_row:
    if ws_veg.cell(row=row, column=LABEL_COL).value != "State":
        row += 1
        continue

    state_row   = row
    region_row  = row + 1
    species_row = row + 2
    soil_row    = row + 3
    area_row    = row + 4
    age_row     = row + 5
    alloc_row   = row + 7  # "Allocation to beef"

    area = f(ws_veg.cell(row=area_row, column=VALUE_COL).value)
    if area != 0:
        vegetation.append({
            "vegetation": {
                "age":         f(ws_veg.cell(row=age_row, column=VALUE_COL).value),
                "area":        area,
                "region":      s(ws_veg.cell(row=region_row, column=VALUE_COL).value),
                "soil":        s(ws_veg.cell(row=soil_row, column=VALUE_COL).value),
                "treeSpecies": s(ws_veg.cell(row=species_row, column=VALUE_COL).value),
            },
            "allocationToBeef": [f(ws_veg.cell(row=alloc_row, column=VALUE_COL).value)],
        })

    row = row + 10  # jump to the next block

# =========================
# FARM-LEVEL / TOP-LEVEL FIELDS
# =========================
farm_state = lookup_state(cell(ws_beef, 6, 4))          # D6 e.g. "SW WA" -> "wa_sw"
north_of_capricorn = yes_no(cell(ws_beef, 4, 13))       # M4 "No"/"Yes"
rainfall_above_600 = yes_no(cell(ws_beef, 6, 13))       # M6 "No"/"Yes"

# =========================
# BUILD FULL PAYLOAD
# =========================
payload = {
    "state":                    farm_state,
    "northOfTropicOfCapricorn": north_of_capricorn,
    "rainfallAbove600":         rainfall_above_600,
    "beef":                     [beef_block],
    "burning":                  burning,
    "vegetation":               vegetation,
}

# =========================
# PREVIEW
# =========================
print("=== PAYLOAD PREVIEW ===")
print(json.dumps(payload, indent=2))

# =========================
# SEND REQUEST
# =========================
headers = {"Content-Type": "application/json"}

response = requests.post(
    API_URL,
    json=payload,
    headers=headers,
    cert=(CERT_FILE, KEY_FILE),
    verify=True
)

print("\n=== RESPONSE ===")
print("Status:", response.status_code)
print(response.text)
