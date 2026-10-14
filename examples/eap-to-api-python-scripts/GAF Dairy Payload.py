import json
import warnings

import openpyxl
import requests

warnings.simplefilter("ignore")

# =========================
# CONFIG
# =========================
XLSX_PATH = r"your file path here"
CERT_PATH = r"your file path here"
KEY_PATH  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/dairy"

# =========================
# LOOKUPS
# =========================
STATE_LOOKUP = {
    1: "act",
    2: "nsw",
    3: "tas",
    4: "wa_sw",
    5: "sa",
    6: "vic",
    7: "qld",
    8: "nt",
    9: "wa_nw",
}

PRODUCTION_SYSTEM_LOOKUP = {
    1: "Irrigated Pasture",
    2: "Non-irrigated Pasture",
    3: "Irrigated Crop",
    4: "Non-irrigated Crop",
}

TRUCK_LOOKUP = {
    1: "4 Deck Trailer",
    2: "6 Deck Trailer",
    3: "B-Double",
}

# =========================
# HELPERS
# =========================
def num(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def text(value, default=""):
    if value is None:
        return default
    return str(value).strip()

def lookup_code(table, value, default=""):
    try:
        return table.get(int(num(value, -1)), default)
    except (TypeError, ValueError):
        return default

def yes_no(value):
    return int(num(value, 2)) == 1

# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
DI  = wb["Data input"]
VEG = wb["Data input - vegetation"]

def di(coord):
    return DI[coord].value

# =========================
# SEASONS
# =========================
SEASON_OFFSET = {
    "spring": 0,
    "summer": 1,
    "autumn": 2,
    "winter": 3,
}
SEASONS = ["autumn", "winter", "spring", "summer"]

# =========================
# ANIMAL CLASSES
# =========================
CLASS_COLUMNS = {
    "milkingCows":   "D",
    "heifersGt1":    "E",
    "heifersLt1":    "F",
    "dairyBullsGt1": "G",
    "dairyBullsLt1": "H",
}

ROW_HEAD       = 12
ROW_LIVEWEIGHT = 18
ROW_LWG        = 24
ROW_CP         = 30
ROW_DMD        = 36
ROW_MILK       = 42

def build_class(col):
    block = {}
    for season, offset in SEASON_OFFSET.items():
        block[season] = {
            "head":                   num(di(f"{col}{ROW_HEAD + offset}")),
            "liveweight":             num(di(f"{col}{ROW_LIVEWEIGHT + offset}")),
            "liveweightGain":         num(di(f"{col}{ROW_LWG + offset}")),
            "crudeProtein":           num(di(f"{col}{ROW_CP + offset}")),
            "dryMatterDigestibility": num(di(f"{col}{ROW_DMD + offset}")),
            "milkProduction":         num(di(f"{col}{ROW_MILK + offset}")),
        }
    return {season: block[season] for season in SEASONS}

classes = {name: build_class(col) for name, col in CLASS_COLUMNS.items()}

# =========================
# AREAS
# =========================
areas = {
    "croppedDryland":           num(di("D49")),
    "croppedIrrigated":         num(di("F49")),
    "improvedPastureDryland":   num(di("D50")),
    "improvedPastureIrrigated": num(di("F50")),
}

# =========================
# FERTILISER
# =========================
fertiliser = {
    "singleSuperphosphate": num(di("D73")),
    "pastureDryland":       num(di("D67")),
    "pastureIrrigated":     num(di("F67")),
    "cropsDryland":         num(di("D66")),
    "cropsIrrigated":       num(di("F66")),
    "otherFertilisers": [
        {
            "otherType":      text(di("C68"), "Monoammonium phosphate (MAP)"),
            "otherDryland":   num(di("D68")),
            "otherIrrigated": num(di("F68")),
        }
    ],
}

ROW_N_CROPS   = 53
ROW_N_PASTURE = 60

seasonal_fertiliser = {}
for season in SEASONS:
    offset = SEASON_OFFSET[season]
    seasonal_fertiliser[season] = {
        "cropsIrrigated":   num(di(f"F{ROW_N_CROPS + offset}")),
        "cropsDryland":     num(di(f"D{ROW_N_CROPS + offset}")),
        "pastureIrrigated": num(di(f"F{ROW_N_PASTURE + offset}")),
        "pastureDryland":   num(di(f"D{ROW_N_PASTURE + offset}")),
    }

# =========================
# MANURE MANAGEMENT
# =========================
def build_manure_management(row):
    return {
        "pasture":          num(di(f"C{row}")),
        "anaerobicLagoon":  num(di(f"D{row}")),
        "sumpAndDispersal": num(di(f"E{row}")),
        "drainToPaddocks":  num(di(f"F{row}")),
        "solidStorage":     num(di(f"G{row}")),
    }

ROW_MANURE_MILKERS = 97
ROW_MANURE_OTHER   = 98

# =========================
# VEGETATION
# =========================
VEG_BLOCK_START  = 2
VEG_BLOCK_STRIDE = 7

def build_vegetation():
    blocks = []
    row = VEG_BLOCK_START
    while row <= VEG.max_row:
        state = text(VEG[f"D{row}"].value)
        if not state:
            break
        area = num(VEG[f"D{row + 4}"].value)
        age  = num(VEG[f"D{row + 5}"].value)
        if area > 0:
            blocks.append({
                "vegetation": {
                    "region":      text(VEG[f"D{row + 1}"].value),
                    "treeSpecies": text(VEG[f"D{row + 2}"].value),
                    "soil":        text(VEG[f"D{row + 3}"].value),
                    "area":        area,
                    "age":         age,
                },
                "dairyProportion": [1],
            })
        row += VEG_BLOCK_STRIDE

    if not blocks:
        blocks.append({
            "vegetation": {
                "region":      "South West",
                "treeSpecies": "Mixed species (Environmental Plantings)",
                "soil":        "Loams & Clays",
                "area":        0,
                "age":         0,
            },
            "dairyProportion": [0],
        })
    return blocks

vegetation = build_vegetation()

# =========================
# BUILD PAYLOAD
# =========================
payload = {
    "id":               "",
    "state":            lookup_code(STATE_LOOKUP, di("E3")),
    "rainfallAbove600": yes_no(di("E7")),
    "productionSystem": lookup_code(PRODUCTION_SYSTEM_LOOKUP, di("E5")),
    "dairy": [
        {
            "id":                   "",
            "classes":              classes,
            "limestone":            num(di("D70")),
            "limestoneFraction":    num(di("D71")),
            "fertiliser":           fertiliser,
            "seasonalFertiliser":   seasonal_fertiliser,
            "areas":                areas,
            "diesel":               num(di("D79")),
            "petrol":               num(di("D80")),
            "lpg":                  num(di("D81")),
            "electricityRenewable": num(di("D78")),
            "electricityUse":       num(di("D77")),
            "grainFeed":            num(di("D82")),
            "hayFeed":              num(di("D84")),
            "cottonseedFeed":       num(di("D83")),
            "herbicide":            num(di("D85")),
            "herbicideOther":       num(di("D86")),
            "manureManagementMilkingCows":    build_manure_management(ROW_MANURE_MILKERS),
            "manureManagementOtherDairyCows": build_manure_management(ROW_MANURE_OTHER),
            "emissionsAllocationToRedMeatProduction": num(di("D94")),
            "truckType":                 lookup_code(TRUCK_LOOKUP, di("D91"), "4 Deck Trailer"),
            "distanceCattleTransported": num(di("D89")),
        }
    ],
    "vegetation": vegetation,
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
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("\n=== RESPONSE ===")
print("Status:", response.status_code)
print(response.text)