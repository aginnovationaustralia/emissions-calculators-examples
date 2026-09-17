
import json
import warnings
 
import openpyxl
import requests
 
# openpyxl DrawingML / data-validation extension warnings are harmless here
warnings.simplefilter("ignore")
 
# =========================
# CONFIG
# =========================
# Filename copied EXACTLY as it appears on disk (spaces + full stops, no underscores)
XLSX_PATH = r"your path here"
CERT_PATH = r"your path here"
KEY_PATH  = r"your path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/deer"
 
# =========================
# LOOKUPS
# =========================
# Region code entered in 'Data input'!D3 -> API state enum string.
# Codes/names come from the workbook's own state table ('Electricity' sheet, R/S/T cols).
#   1 ACT | 2 NSW | 3 Tas | 4 SW WA | 5 SA | 6 Vic | 7 Qld | 8 NT | 9 NW WA
# NOTE: wa_sw / wa_nw remain UNCONFIRMED with AIA across all scripts - flagged for verification.
STATE_LOOKUP = {
    1: "act",
    2: "nsw",
    3: "tas",
    4: "wa_sw",   # SW WA  <<< UNCONFIRMED ENUM
    5: "sa",
    6: "vic",
    7: "qld",
    8: "nt",
    9: "wa_nw",   # NW WA  <<< UNCONFIRMED ENUM
}
 
# Valid 'otherType' fertiliser strings (from Agricultural Soils!B120:C125 N-content table).
# Passed through verbatim from the workbook cell; listed here for reference/validation.
VALID_OTHER_FERTILISERS = {
    "Monoammonium phosphate (MAP)",
    "Diammonium Phosphate (DAP)",
    "Urea",
    "Urea-Ammonium Nitrate (UAN)",
    "Ammonium Nitrate (AN)",
    "Calcium Ammonium Nitrate (CAN)",
}
 
# =========================
# HELPERS
# =========================
def num(value):
    """Coerce a cell value to float; blanks / non-numeric -> 0.0."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
 
def yes_no(value):
    """'Data input' Yes/No cells are coded 1=Yes, 2=No (workbook: IF(cell=2,No,Yes))."""
    return num(value) != 2
 
def normalize_enum(text, fallback):
    """Trim/validate an enum string; fall back to a valid default if blank/unknown."""
    if text is None:
        return fallback
    s = str(text).strip()
    return s if s else fallback
 
# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
di = wb["Data input"]
 
def v(coord):
    """Read a raw cell value from the 'Data input' sheet."""
    return di[coord].value
 
# =========================
# ANIMAL CLASSES  >>> ENTERPRISE-SPECIFIC
# =========================
# API class name -> 'Data input' column letter for that class (None = no column in this GAF).
# Column headers (row 7/14): D=Bucks, E=Breeding does, F=Other does, G=Fawn,
#                            H=Trade bucks, I=Trade does.
# The API also carries tradeOtherDoes and tradeFawn, which have no cell in this workbook.
CLASS_COLUMNS = {
    "bucks":         "D",
    "tradeBucks":    "H",
    "breedingDoes":  "E",
    "tradeDoes":     "I",
    "otherDoes":     "F",
    "tradeOtherDoes": None,   # no column in this GAF -> zeroed
    "fawn":          "G",
    "tradeFawn":     None,    # no column in this GAF -> zeroed
}
 
# Row map for each class column  >>> ENTERPRISE-SPECIFIC
ROW_SPRING        = 8    # Livestock numbers - Spring
ROW_SUMMER        = 9    # Livestock numbers - Summer
ROW_AUTUMN        = 10   # Livestock numbers - Autumn
ROW_WINTER        = 11   # Livestock numbers - Winter
ROW_PURCH_HEAD    = 15   # No. head purchased
ROW_PURCH_WEIGHT  = 16   # Purchase weight (LW/hd)
ROW_HEAD_SOLD     = 20   # No. head sold
ROW_SALE_WEIGHT   = 21   # Sale weight (LW/hd)
 
 
def build_class(col):
    """Build one animal-class block. col=None -> fully zeroed (class absent from GAF)."""
    if col is None:
        return {
            "autumn": {"head": 0},
            "winter": {"head": 0},
            "spring": {"head": 0},
            "summer": {"head": 0},
            "headSold": 0,
            "saleWeight": 0,
            # Never send an empty array: single zeroed purchase entry as fallback.
            "purchases": [{"head": 0, "purchaseWeight": 0}],
        }
    return {
        "autumn": {"head": num(v(f"{col}{ROW_AUTUMN}"))},
        "winter": {"head": num(v(f"{col}{ROW_WINTER}"))},
        "spring": {"head": num(v(f"{col}{ROW_SPRING}"))},
        "summer": {"head": num(v(f"{col}{ROW_SUMMER}"))},
        "headSold": num(v(f"{col}{ROW_HEAD_SOLD}")),
        "saleWeight": num(v(f"{col}{ROW_SALE_WEIGHT}")),
        "purchases": [
            {
                "head": num(v(f"{col}{ROW_PURCH_HEAD}")),
                "purchaseWeight": num(v(f"{col}{ROW_PURCH_WEIGHT}")),
            }
        ],
    }
 
 
classes = {name: build_class(col) for name, col in CLASS_COLUMNS.items()}
 
# =========================
# FERTILISER  >>> ENTERPRISE-SPECIFIC
# =========================
# D45/F45 = Urea to Pasture (Dryland/Irrigated); D46/F46 = Urea to Crops (Dryland/Irrigated)
# C47/D47/F47 = Other N fertiliser (type / Dryland / Irrigated); D49 = Single Superphosphate
other_type = normalize_enum(v("C47"), fallback="Monoammonium phosphate (MAP)")
 
fertiliser = {
    "singleSuperphosphate": num(v("D49")),
    "pastureDryland":  num(v("D45")),
    "pastureIrrigated": num(v("F45")),
    "cropsDryland":    num(v("D46")),
    "cropsIrrigated":  num(v("F46")),
    # Never send an empty array: always at least one otherFertilisers entry.
    "otherFertilisers": [
        {
            "otherType": other_type,
            "otherDryland":  num(v("D47")),
            "otherIrrigated": num(v("F47")),
        }
    ],
}
 
# =========================
# DEER ENTERPRISE BLOCK  >>> ENTERPRISE-SPECIFIC
# =========================
deer = {
    "id": "",
    "classes": classes,
    "limestone": num(v("D50")),          # Limestone applied to soils (total for farm)
    "limestoneFraction": num(v("D51")),  # Fraction (0 to 1)
    "fertiliser": fertiliser,
    "diesel": num(v("D56")),
    "petrol": num(v("D57")),
    "lpg": num(v("D58")),
    "electricitySource": "State Grid",
    "electricityRenewable": num(v("D55")),  # % from renewable source
    "electricityUse": num(v("D54")),        # Annual Electricity Use (State Grid) - cell used by the tool
    # NB: 'Data input'!D59 (a second "Annual Electricity Use" = 2000 in the sample) is not
    #     referenced by any calc sheet; the tool uses D54. Confirm with AIA if D59 should feed in.
    "grainFeed": num(v("D60")),
    "hayFeed": num(v("D61")),
    "herbicide": num(v("D62")),        # Paraquat/Diquat/Glyphosate (kg a.i.)
    "herbicideOther": num(v("D63")),   # other herbicides/pesticides (kg a.i.)
    "doesFawning": {                   # Proportion of does fawning (rows 29-32)
        "spring": num(v("D29")),
        "summer": num(v("D30")),
        "autumn": num(v("D31")),
        "winter": num(v("D32")),
    },
    "seasonalFawning": {               # Seasonal fawning rates (rows 35-38)
        "spring": num(v("D35")),
        "summer": num(v("D36")),
        "autumn": num(v("D37")),
        "winter": num(v("D38")),
    },
}
 
# =========================
# TOP-LEVEL PAYLOAD
# =========================
region_code = int(num(v("D3")))
state_enum = STATE_LOOKUP.get(region_code)
if state_enum is None:
    raise ValueError(f"Unrecognised region code in 'Data input'!D3: {region_code!r}")
 
payload = {
    "id": "",
    "state": state_enum,
    "rainfallAbove600": yes_no(v("D5")),
    "deers": [deer],
    # Vegetation/tree sequestration: the AIA reference schema sends "vegetation": []
    # and does NOT expose the vegetation object shape, so it cannot be populated here.
    # This sample workbook DOES have tree data (Data summary shows -22.50 t CO2e sequestration),
    # so the API's net figure will exclude that until AIA provides the vegetation sub-schema.
    "vegetation": [],
}
 
# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW (not yet sent)")
print("=" * 25)
print(json.dumps(payload, indent=2))
print("=" * 25)
 
# =========================
# POST (mTLS)
# =========================
headers = {"Content-Type": "application/json"}
 
response = requests.post(
    API_URL,
    headers=headers,
    data=json.dumps(payload),
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)
 
print("=" * 25)
print(f"HTTP {response.status_code}")
print("=" * 25)
print(response.text)