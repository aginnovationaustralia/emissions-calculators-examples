 
import json
import requests
import openpyxl
 
# =========================
# CONFIG
# =========================
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/goat"
CERT_FILE = r"your path here"
KEY_FILE  = r"your path here"
XLSX_PATH = r"your path here"
 
# =========================
# LOAD WORKBOOK
# =========================
# data_only=True so we read cached cell VALUES, not formulas. The harmless
# DrawingML / data-validation UserWarnings openpyxl emits do not affect reads.
wb      = openpyxl.load_workbook(XLSX_PATH, data_only=True)
ws      = wb["Data input"]
ws_veg  = wb["Data input - vegetation"]
 
# =========================
# SAFE VALUE HELPERS
# =========================
def f(worksheet, cell, default=0.0):
    """Read a cell as float; blanks / non-numeric fall back to default."""
    v = worksheet[cell].value
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default
 
def b(value):
    """Coerce a truthy workbook value to a JSON bool."""
    return bool(value)
 
def s(worksheet, cell, default=""):
    """Read a cell as a stripped string; blanks fall back to default."""
    v = worksheet[cell].value
    if v is None:
        return default
    return str(v).strip()
 
def is_set(worksheet, cell):
    """True if a numeric cell holds a non-zero value."""
    return f(worksheet, cell) not in (0, 0.0)
 
def yes_no(worksheet, cell):
    """Decode a Yes/No (or 1/0) workbook cell to a bool."""
    v = s(worksheet, cell).lower()
    if v in ("yes", "y", "true", "1", "1.0"):
        return True
    if v in ("no", "n", "false", "0", "0.0"):
        return False
    # Numeric fallback: any non-zero number reads as True.
    return is_set(worksheet, cell)
 
def normalize_enum(value, lookup, label, fallback):
    """Map a workbook label to an API enum string via a lookup dict."""
    key = str(value).strip().lower()
    if key in lookup:
        return lookup[key]
    print(f"[warn] Unrecognised {label} '{value}' - defaulting to '{fallback}'")
    return fallback
 
# =========================
# LOOKUPS
# =========================
# Data input!E5 holds the region as plain text (e.g. "Vic"), so we map the label
# straight to the API enum. (Electricity!R2:T10 also codes these numerically, but
# the text label is authoritative here so no lookup_code() is required.)
# >>> FLAG: wa_sw / wa_nw remain unconfirmed across all scripts.
STATE_LOOKUP = {
    "nsw": "nsw", "new south wales": "nsw",
    "vic": "vic", "victoria": "vic",
    "qld": "qld", "queensland": "qld",
    "sa": "sa",  "south australia": "sa",
    "wa": "wa",  "western australia": "wa",
    "sw wa": "wa_sw", "nw wa": "wa_nw",
    "tas": "tas", "tasmania": "tas",
    "nt": "nt",  "northern territory": "nt",
    "act": "act", "australian capital territory": "act",
}
 
# =========================
# CLASS LAYOUT  >>> ENTERPRISE-SPECIFIC
# =========================
# Livestock-number / purchase / sale columns run D..L on the "Data input" sheet.
# The 9 workbook columns are mapped to the 12 API goat classes below; the 3 API
# classes with no workbook column are sent zeroed (col = None).
CLASS_COLUMNS = {
    "bucksBilly":                     "D",   # D  Bucks/Billy
    "wethers":                        "E",   # E  Wethers
    "maidenBreedingDoesNannies":      "F",   # F  Maiden Breeding does/Nannies
    "breedingDoesNannies":            "G",   # G  Breeding does/Nannies
    "otherDoesCulledFemales":         "H",   # H  Other does/Culled females
    "kids":                           "I",   # I  Kids
    "tradeBucks":                     "J",   # J  Trade bucks
    "tradeOtherDoesCulledFemales":    "K",   # K  Trade does  >>> FLAG (target class)
    "tradeWethers":                   "L",   # L  Trade wethers
    "tradeMaidenBreedingDoesNannies": None,  # no workbook column -> zeroed
    "tradeBreedingDoesNannies":       None,  # no workbook column -> zeroed
    "tradeKids":                      None,  # no workbook column -> zeroed
}
 
# Fixed row references on "Data input"  >>> ENTERPRISE-SPECIFIC
ROW_SPRING           = 11   # Livestock numbers - Spring (head)
ROW_SUMMER           = 12   # Livestock numbers - Summer (head)
ROW_AUTUMN           = 13   # Livestock numbers - Autumn (head)
ROW_WINTER           = 14   # Livestock numbers - Winter (head)
ROW_PURCH_HEAD       = 18   # Purchase inventory - No. head purchased
ROW_PURCH_WEIGHT     = 19   # Purchase inventory - Purchase weight (LW/hd)
ROW_HEAD_SOLD        = 23   # Sale inventory - No. head sold
ROW_SALE_WEIGHT      = 24   # Sale inventory - Sale weight (LW/hd)
ROW_HEAD_SHORN       = 31   # Wool inventory - Number shorn
ROW_WOOL_SHORN       = 32   # Wool inventory - Wool shorn kg/head
ROW_CLEAN_WOOL_YIELD = 35   # Wool inventory - Clean wool yield (%)
 
def build_class(col):
    """Build one goat class block. col=None yields a fully zeroed class."""
    if col is None:
        return {
            "autumn": {"head": 0}, "winter": {"head": 0},
            "spring": {"head": 0}, "summer": {"head": 0},
            "headSold": 0, "saleWeight": 0,
            "headShorn": 0, "woolShorn": 0, "cleanWoolYield": 0,
            # Never send an empty array - one zeroed purchase entry as fallback.
            "purchases": [{"head": 0, "purchaseWeight": 0}],
        }
 
    def cell(row):
        return f"{col}{row}"
 
    return {
        "autumn": {"head": f(ws, cell(ROW_AUTUMN))},
        "winter": {"head": f(ws, cell(ROW_WINTER))},
        "spring": {"head": f(ws, cell(ROW_SPRING))},
        "summer": {"head": f(ws, cell(ROW_SUMMER))},
        "headSold":       f(ws, cell(ROW_HEAD_SOLD)),
        "saleWeight":     f(ws, cell(ROW_SALE_WEIGHT)),
        "headShorn":      f(ws, cell(ROW_HEAD_SHORN)),
        "woolShorn":      f(ws, cell(ROW_WOOL_SHORN)),        # kg/head (greasy = shorn x this)
        "cleanWoolYield": f(ws, cell(ROW_CLEAN_WOOL_YIELD)),  # >>> FLAG raw % (65), not 0.65
        # One purchase entry per class (never an empty array).
        "purchases": [{
            "head":           f(ws, cell(ROW_PURCH_HEAD)),
            "purchaseWeight": f(ws, cell(ROW_PURCH_WEIGHT)),
        }],
    }
 
# =========================
# FERTILISER  >>> ENTERPRISE-SPECIFIC
# =========================
# Dryland = col D, Irrigated = col F.
#   Row 61  Urea Fertiliser Pasture   -> pasture{Dryland,Irrigated}
#   Row 62  Urea Fertiliser Crops     -> crops{Dryland,Irrigated}
#   Row 63  Other N fertiliser (DAP)  -> otherFertilisers[0]
#   Row 65  Single Superphosphate     -> singleSuperphosphate
def build_fertiliser():
    return {
        "singleSuperphosphate": f(ws, "D65"),
        "pastureDryland":       f(ws, "D61"),
        "pastureIrrigated":     f(ws, "F61"),
        "cropsDryland":         f(ws, "D62"),
        "cropsIrrigated":       f(ws, "F62"),
        # Never an empty array. otherType is read verbatim from C63.
        # >>> FLAG confirm "Diammonium Phosphate (DAP)" is an accepted API enum.
        "otherFertilisers": [{
            "otherType":     s(ws, "C63", "Diammonium Phosphate (DAP)"),
            "otherDryland":  f(ws, "D63"),
            "otherIrrigated": f(ws, "F63"),
        }],
    }
 
# =========================
# MINERAL SUPPLEMENTATION  >>> ENTERPRISE-SPECIFIC
# =========================
# Do NOT swap these: col F = tonnes of product, col D = % urea (matches GAF Sheep).
# The F column sums to the "total tonnes" total (F58), confirming F = amount.
def build_mineral():
    return {
        "mineralBlock":      f(ws, "F55"),
        "mineralBlockUrea":  f(ws, "D55"),
        "weanerBlock":       f(ws, "F56"),
        "weanerBlockUrea":   f(ws, "D56"),
        "drySeasonMix":      f(ws, "F57"),
        "drySeasonMixUrea":  f(ws, "D57"),
    }
 
# =========================
# GOAT ENTERPRISE
# =========================
def build_goat():
    classes = {name: build_class(col) for name, col in CLASS_COLUMNS.items()}
    return {
        "id": "",
        "classes": classes,
        "limestone":         f(ws, "D66"),   # Limestone applied - total for farm
        "limestoneFraction": f(ws, "D67"),   # Fraction (0 to 1)
        "fertiliser":        build_fertiliser(),
        "diesel":            f(ws, "D72"),
        "petrol":            f(ws, "D73"),
        "lpg":               f(ws, "D74"),
        "mineralSupplementation": build_mineral(),
        "electricitySource":    "State Grid",
        "electricityRenewable": f(ws, "D71"),   # >>> FLAG raw value (0.1)
        # Row 70 "Annual Electricity Use (State Grid)" is the value that flows to
        # the calc (grid 900 kWh @ 0.77 = 0.693 t Scope 2). Row 75 (2000 kWh) is
        # an unused duplicate and is deliberately NOT read.
        "electricityUse":       f(ws, "D70"),
        "grainFeed":            f(ws, "D76"),
        "hayFeed":              f(ws, "D77"),
        "herbicide":            f(ws, "D78"),
        "herbicideOther":       f(ws, "D79"),
    }
 
# =========================
# VEGETATION  >>> ENTERPRISE-SPECIFIC
# =========================
# Blocks stack vertically on "Data input - vegetation", 7 rows apart, values in
# col D. Per block: State(+0) Region(+1) Species(+2) Soil(+3) Area(+4) Age(+5).
# >>> FLAG: the supplied goat schema showed "vegetation": [] with no object. The
# object below follows the confirmed GAF Sheep shape (region/treeSpecies/soil/
# area/age). The workbook has no per-enterprise proportion cell for goats, so
# goatProportion defaults to [1] (all trees attributed to the single enterprise).
# Confirm the field name and default with AIA.
VEG_BLOCK_START_ROWS = [2, 9, 16, 23]
 
def build_vegetation(start):
    return {
        "vegetation": {
            "region":      s(ws_veg, f"D{start + 1}", "South West"),
            "treeSpecies": s(ws_veg, f"D{start + 2}", "Mixed species (Environmental Plantings)"),
            "soil":        s(ws_veg, f"D{start + 3}", "Loams & Clays"),
            "area":        f(ws_veg, f"D{start + 4}"),
            "age":         f(ws_veg, f"D{start + 5}"),
        },
        "goatProportion": [1],  # >>> FLAG inferred (see block comment above)
    }
 
# =========================
# BUILD PAYLOAD
# =========================
goats = [build_goat()]
 
# Only send blocks that actually carry trees (area or age set). A zero/zero block
# sequesters nothing and only adds enum risk.
vegetation = []
for start in VEG_BLOCK_START_ROWS:
    if is_set(ws_veg, f"D{start + 4}") or is_set(ws_veg, f"D{start + 5}"):
        vegetation.append(build_vegetation(start))
 
if not vegetation:  # never send an empty array
    vegetation = [{
        "vegetation": {
            "region": "South West",
            "treeSpecies": "Mixed species (Environmental Plantings)",
            "soil": "Loams & Clays",
            "area": 0,
            "age": 0,
        },
        "goatProportion": [0],
    }]
 
payload = {
    "id": "",
    "state": normalize_enum(s(ws, "E5"), STATE_LOOKUP, "state", "vic"),
    "rainfallAbove600": yes_no(ws, "E7"),
    "goats": goats,
    "vegetation": vegetation,
}
 
# =========================
# PAYLOAD PREVIEW
# =========================
print("=== PAYLOAD PREVIEW ===")
print(json.dumps(payload, indent=2))
 
# =========================
# SEND TO API
# =========================
headers = {"Content-Type": "application/json"}
 
response = requests.post(
    API_URL,
    json=payload,
    headers=headers,
    cert=(CERT_FILE, KEY_FILE),
    verify=True,
)
 
print("\n=== RESPONSE ===")
print("Status:", response.status_code)
print(response.text)