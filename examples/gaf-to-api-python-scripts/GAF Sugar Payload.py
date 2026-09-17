import openpyxl
import requests
import json

# =========================
# CONFIG
# =========================
# >>> ENTERPRISE-SPECIFIC: path to the completed Sugar GAF workbook
XLSX_FILE = r"your path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/sugar"
CERT_FILE = r"your path here"
KEY_FILE  = r"your path here"

# >>> ENTERPRISE-SPECIFIC: sheet names inside the Sugar GAF workbook
CROPS_SHEET      = "Data input - crops"
VEGETATION_SHEET = "Data input - vegetation"

# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_FILE, data_only=True)
ws_crops = wb[CROPS_SHEET]
ws_veg   = wb[VEGETATION_SHEET]

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
    return str(value).strip().lower() == "yes"

# =========================
# >>> ENTERPRISE-SPECIFIC: LOOKUP TABLES
# The Sugar GAF workbook stores farm region as a numeric code (same
# Electricity!R2:S10 table used across the GAF workbooks). Production
# system is stored as free text on the crops sheet ("Sugar Cane"), so it
# is normalised to the API's exact enum casing rather than code-decoded.
#   - Farm region/state -> 'Electricity'!R2:S10
# =========================

# NOTE: WA is split into two rainfall sub-regions in the workbook
# (SW WA / NW WA) but both resolve to the same API state code "wa".
STATE_LOOKUP = {
    1: "act",
    2: "nsw",
    3: "tas",
    4: "wa",   # SW WA
    5: "sa",
    6: "vic",
    7: "qld",
    8: "nt",
    9: "wa",   # NW WA
}

# API productionSystem accepts exactly:
#   "Non-irrigated crop" | "Irrigated crop" | "Sugar cane" | "Cotton" | "Horticulture"
# The workbook writes "Sugar Cane" (capital C), so map to the exact casing.
PRODUCTION_SYSTEM_LOOKUP = {
    "non-irrigated crop": "Non-irrigated crop",
    "irrigated crop":     "Irrigated crop",
    "sugar cane":         "Sugar cane",
    "sugarcane":          "Sugar cane",
    "cotton":             "Cotton",
    "horticulture":       "Horticulture",
}

def lookup_code(code_value, table, label):
    try:
        code = int(f(code_value))
    except (TypeError, ValueError):
        code = None
    if code not in table:
        print(f"WARNING: unrecognised {label} code: {code_value!r}")
        return ""
    return table[code]

def production_system(value):
    key = s(value).lower()
    if key not in PRODUCTION_SYSTEM_LOOKUP:
        print(f"WARNING: unrecognised production system: {value!r}")
        return ""
    return PRODUCTION_SYSTEM_LOOKUP[key]

# =========================
# FARM-LEVEL FIELDS
# =========================
# >>> ENTERPRISE-SPECIFIC: fixed row/column positions in "Data input - crops"
REGION_CODE_CELL       = (2, 3)   # row 2, col C
ELECTRICITY_USE_CELL   = (23, 3)  # row 23, col C
ELECTRICITY_RENEW_CELL = (24, 3)  # row 24, col C

farm_state = lookup_code(ws_crops.cell(*REGION_CODE_CELL).value, STATE_LOOKUP, "region")

# =========================
# BUILD CROPS LIST
# Crop slots run across columns C, D, E, F, G... in "Data input - crops".
# We loop until we hit a blank column (Production System row = crop present).
# The Sugar GAF is a single vertical crop, so in practice this yields one crop.
# >>> ENTERPRISE-SPECIFIC: row numbers for each field within a crop column
# =========================
ROW_PRODUCTION_SYSTEM     = 5    # text "Sugar Cane" (also the crop-present check)
ROW_AVG_CANE_YIELD        = 6
ROW_PERCENT_MILLED_YIELD  = 7    # CCS fraction, e.g. 0.12  (see NOTE on units below)
ROW_AREA_SOWN             = 10
ROW_NON_UREA_NITROGEN     = 11
ROW_UREA_APPLICATION      = 12
ROW_UREA_AMMONIUM_NITRATE = 13
ROW_PHOSPHORUS            = 14
ROW_POTASSIUM             = 15
ROW_SULFUR                = 16
ROW_LIMESTONE             = 17
ROW_LIMESTONE_FRACTION    = 18
ROW_FRACTION_CROP_BURNT   = 19
ROW_DIESEL                = 20
ROW_PETROL                = 21
ROW_LPG                   = 22
ROW_HERBICIDE_USE         = 25
ROW_GLYPHOSATE_OTHER      = 26

# >>> ENTERPRISE-SPECIFIC constants NOT captured in the Sugar workbook:
#  - rainfallAbove600: the 'notes' tab states all sugar cane is assumed to sit
#    in a >600mm rainfall zone, so this is a fixed True (no input cell exists).
#  - electricityAllocation: no per-crop allocation cell; with a single cane crop
#    100% of farm electricity allocates to it.
RAINFALL_ABOVE_600     = True
ELECTRICITY_ALLOCATION = 1.0

FIRST_CROP_COLUMN = 3  # column C

crops = []
col = FIRST_CROP_COLUMN
while ws_crops.cell(row=ROW_PRODUCTION_SYSTEM, column=col).value is not None:
    crops.append({
        "id":                          "",
        "state":                       farm_state,
        "productionSystem":            production_system(ws_crops.cell(row=ROW_PRODUCTION_SYSTEM, column=col).value),
        "averageCaneYield":            f(ws_crops.cell(row=ROW_AVG_CANE_YIELD, column=col).value),
        "percentMilledCaneYield":      f(ws_crops.cell(row=ROW_PERCENT_MILLED_YIELD, column=col).value),
        "areaSown":                    f(ws_crops.cell(row=ROW_AREA_SOWN, column=col).value),
        "nonUreaNitrogen":             f(ws_crops.cell(row=ROW_NON_UREA_NITROGEN, column=col).value),
        "ureaApplication":             f(ws_crops.cell(row=ROW_UREA_APPLICATION, column=col).value),
        "ureaAmmoniumNitrate":         f(ws_crops.cell(row=ROW_UREA_AMMONIUM_NITRATE, column=col).value),
        "phosphorusApplication":       f(ws_crops.cell(row=ROW_PHOSPHORUS, column=col).value),
        "potassiumApplication":        f(ws_crops.cell(row=ROW_POTASSIUM, column=col).value),
        "sulfurApplication":           f(ws_crops.cell(row=ROW_SULFUR, column=col).value),
        "rainfallAbove600":            RAINFALL_ABOVE_600,
        "fractionOfAnnualCropBurnt":   f(ws_crops.cell(row=ROW_FRACTION_CROP_BURNT, column=col).value),
        "herbicideUse":                f(ws_crops.cell(row=ROW_HERBICIDE_USE, column=col).value),
        "glyphosateOtherHerbicideUse": f(ws_crops.cell(row=ROW_GLYPHOSATE_OTHER, column=col).value),
        "electricityAllocation":       ELECTRICITY_ALLOCATION,
        "limestone":                   f(ws_crops.cell(row=ROW_LIMESTONE, column=col).value),
        "limestoneFraction":           f(ws_crops.cell(row=ROW_LIMESTONE_FRACTION, column=col).value),
        "dieselUse":                   f(ws_crops.cell(row=ROW_DIESEL, column=col).value),
        "petrolUse":                   f(ws_crops.cell(row=ROW_PETROL, column=col).value),
        "lpg":                         f(ws_crops.cell(row=ROW_LPG, column=col).value),
    })
    col += 1

num_crop_slots = len(crops)

# =========================
# BUILD VEGETATION LIST
# The vegetation sheet repeats a block for each vegetation entry:
#   State / Region / Species of Tree / Soil Type / Area of Trees / Age of Trees
#   then one "Allocation to crop" row per crop slot, in the same order
#   as the crop columns above (C, D, E, F, G...).
# Blocks are detected by scanning the label column for "State" rather than
# assuming a fixed row spacing, so this is robust to layout drift.
# >>> ENTERPRISE-SPECIFIC: in the Sugar workbook labels sit in column B and
#     values in column D (grains used C / E).
# =========================
LABEL_COL       = 2  # column B holds the row labels within a vegetation block
VALUE_COL       = 4  # column D holds the corresponding values
ALLOC_VALUE_COL = 4  # column D holds the allocation fraction

vegetation = []
row = 1
max_row = ws_veg.max_row
while row <= max_row:
    label = ws_veg.cell(row=row, column=LABEL_COL).value
    if label != "State":
        row += 1
        continue

    region_row  = row + 1
    species_row = row + 2
    soil_row    = row + 3
    area_row    = row + 4
    age_row     = row + 5
    alloc_start_row = row + 7  # one blank row separates Age from the allocations

    area = f(ws_veg.cell(row=area_row, column=VALUE_COL).value)
    age  = f(ws_veg.cell(row=age_row, column=VALUE_COL).value)

    # Skip empty template blocks (the Sugar workbook ships with pre-filled
    # zero-area placeholder blocks). >>> if you want them submitted, drop this.
    if area == 0 and age == 0:
        row = alloc_start_row + num_crop_slots
        continue

    allocations = []
    for k in range(num_crop_slots):
        allocations.append(f(ws_veg.cell(row=alloc_start_row + k, column=ALLOC_VALUE_COL).value))

    vegetation.append({
        "vegetation": {
            "age":         age,
            "area":        area,
            "region":      s(ws_veg.cell(row=region_row, column=VALUE_COL).value),
            "soil":        s(ws_veg.cell(row=soil_row, column=VALUE_COL).value),
            "treeSpecies": s(ws_veg.cell(row=species_row, column=VALUE_COL).value),
        },
        "allocationToCrops": allocations,
    })

    row = alloc_start_row + num_crop_slots  # jump past this block

# =========================
# BUILD FULL PAYLOAD
# NOTE: the /sugar schema has NO top-level "id" (grains does), and sugar crops
# use averageCaneYield + percentMilledCaneYield with no "type" field.
# =========================
payload = {
    "state":                farm_state,
    "crops":                crops,
    "electricityRenewable": f(ws_crops.cell(*ELECTRICITY_RENEW_CELL).value),
    "electricityUse":       f(ws_crops.cell(*ELECTRICITY_USE_CELL).value),
    "vegetation":           vegetation,
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