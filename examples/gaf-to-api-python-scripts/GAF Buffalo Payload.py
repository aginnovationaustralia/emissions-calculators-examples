
import json
import openpyxl
import requests
 
# =========================
# CONFIG
# =========================
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/buffalo"
XLSX_PATH = r"your path here"
CERT_PATH = r"your path here"
KEY_PATH  = r"your path here"
 
# =========================
# LOOKUPS  (decoded from the workbook's own reference tables)
# =========================
# Region code -> API state enum string.
# Source: 'Electricity' sheet lookup table R2:S9 (the same table the workbook
# uses to turn the 'Data input'!D3 dropdown code into a state name).
#   1=ACT 2=NSW 3=TAS 4=SW WA 5=SA 6=VIC 7=QLD 8=NT 9=NW WA
# >>> ENTERPRISE-SPECIFIC / verify: wa_sw / wa_nw enum strings are still
#     UNCONFIRMED with AIA across all scripts.
STATE_LOOKUP = {
    1: "act",
    2: "nsw",
    3: "tas",
    4: "wa_sw",   # SW WA  <-- UNCONFIRMED, flagged
    5: "sa",
    6: "vic",
    7: "qld",
    8: "nt",
    9: "wa_nw",   # NW WA  <-- UNCONFIRMED, flagged
}
 
# Rainfall question ('Data input'!D5) code -> Yes/No.
# Source: 'Agricultural Soils' sheet table D79:E80 -> 2='Yes', 1='No'.
RAINFALL_YES_CODE = 2
 
# =========================
# SAFE VALUE HELPERS
# =========================
def num(ws, coord):
    """Return a cell value as float, treating blank / non-numeric as 0.0."""
    v = ws[coord].value
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0
 
def text(ws, coord):
    """Return a cell value as a stripped string ('' if blank)."""
    v = ws[coord].value
    return str(v).strip() if v is not None else ""
 
def lookup_code(mapping, code, default=None):
    """Decode a numeric workbook code via a named lookup dict."""
    try:
        return mapping[int(code)]
    except (TypeError, ValueError, KeyError):
        return default
 
# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
di = wb["Data input"]
 
# =========================
# ANIMAL CLASSES  >>> ENTERPRISE-SPECIFIC
# =========================
# 'Data input' column letter for each schema class.
# The Buffalo GAF workbook only has six columns (no Trade steers / Trade calfs);
# those two API classes are always sent as zeroed blocks.
CLASS_COLUMNS = {
    "bulls":       "D",
    "cows":        "E",
    "steers":      "F",
    "calfs":       "G",
    "tradeBulls":  "H",
    "tradeCows":   "I",
    "tradeSteers": None,   # no column in workbook -> zeroed
    "tradeCalfs":  None,   # no column in workbook -> zeroed
}
 
# Row constants on 'Data input'  >>> ENTERPRISE-SPECIFIC
ROW_SPRING, ROW_SUMMER, ROW_AUTUMN, ROW_WINTER = 8, 9, 10, 11   # seasonal head
ROW_PURCH_HEAD, ROW_PURCH_WEIGHT             = 15, 16          # purchase inventory
ROW_SOLD_HEAD, ROW_SOLD_WEIGHT               = 20, 21          # sale inventory
 
def build_class(col):
    """Build one animal-class object. col=None -> fully zeroed block."""
    def c(row):
        return 0.0 if col is None else num(di, f"{col}{row}")
    return {
        "autumn": {"head": c(ROW_AUTUMN)},
        "winter": {"head": c(ROW_WINTER)},
        "spring": {"head": c(ROW_SPRING)},
        "summer": {"head": c(ROW_SUMMER)},
        "headSold":  c(ROW_SOLD_HEAD),
        "saleWeight": c(ROW_SOLD_WEIGHT),
        # purchases must never be an empty array: always one (zeroed) entry.
        "purchases": [{
            "head":           c(ROW_PURCH_HEAD),
            "purchaseWeight": c(ROW_PURCH_WEIGHT),
        }],
    }
 
classes = {name: build_class(col) for name, col in CLASS_COLUMNS.items()}
 
# =========================
# CALVING  >>> ENTERPRISE-SPECIFIC
# =========================
# Proportions stored as fractions (0-1), summing to 1 (cells formatted 0%).
cows_calving = {
    "spring": num(di, "D29"),
    "summer": num(di, "D30"),
    "autumn": num(di, "D31"),
    "winter": num(di, "D32"),
}
seasonal_calving = {
    "spring": num(di, "D35"),
    "summer": num(di, "D36"),
    "autumn": num(di, "D37"),
    "winter": num(di, "D38"),
}
 
# =========================
# FERTILISER  >>> ENTERPRISE-SPECIFIC
# =========================
# Urea pasture/crops entered as tonnes of urea; UAN entered as tonnes of product.
# 'Data input': pasture D45(dryland)/F45(irrigated), crops D46/F46,
#               other-N C47(name)/D47(dryland)/F47(irrigated), SSP D49.
other_type = text(di, "C47")  # e.g. "Urea-Ammonium Nitrate (UAN)"
fertiliser = {
    "singleSuperphosphate": num(di, "D49"),
    "pastureDryland":       num(di, "D45"),
    "pastureIrrigated":     num(di, "F45"),
    "cropsDryland":         num(di, "D46"),
    "cropsIrrigated":       num(di, "F46"),
    # otherFertilisers must never be empty: always one entry.
    "otherFertilisers": [{
        # >>> verify "otherType" is a valid API enum string (workbook label used).
        "otherType":     other_type,
        "otherDryland":  num(di, "D47"),
        "otherIrrigated": num(di, "F47"),
    }],
}
 
# =========================
# BUFFALO ENTERPRISE BLOCK
# =========================
buffalo = {
    "id": "",
    "classes": classes,
    "limestone":         num(di, "D50"),
    "limestoneFraction": num(di, "D51"),
    "fertiliser":        fertiliser,
    "diesel":  num(di, "D56"),
    "petrol":  num(di, "D57"),
    "lpg":     num(di, "D58"),
    "electricitySource":    "State Grid",
    # D55 is stored as a fraction (0.2 = 20%); workbook computes grid use as
    # D54*(1-D55). >>> verify whether the API expects a fraction (0.2) or a
    #     whole-number percent (20).
    "electricityRenewable": num(di, "D55"),
    "electricityUse":       num(di, "D54"),
    "grainFeed":     num(di, "D59"),
    "hayFeed":       num(di, "D60"),
    "herbicide":     num(di, "D61"),
    "herbicideOther": num(di, "D62"),
    "cowsCalving":     cows_calving,
    "seasonalCalving": seasonal_calving,
}
 
# =========================
# VEGETATION
# =========================
# The provided API schema sends "vegetation": [] and does NOT define the
# vegetation object structure. The 'Data input - vegetation' sheet of THIS
# workbook contains tree-planting data (see the flag print below), which cannot
# be sent until AIA supplies the vegetation item schema. Sending [] to match
# the documented buffalo contract exactly.
vegetation = []
 
# =========================
# PAYLOAD
# =========================
payload = {
    "state": lookup_code(STATE_LOOKUP, di["D3"].value),
    "rainfallAbove600": num(di, "D5") == RAINFALL_YES_CODE,
    "buffalos": [buffalo],
    "vegetation": vegetation,
}
 
# =========================
# DATA-ISSUE FLAGS  (read but not sent -- surfaced for the operator)
# =========================
def read_vegetation_plantings():
    """Read the 4 tree-planting blocks so omitted data is visible in preview."""
    vs = wb["Data input - vegetation"]
    blocks = [2, 9, 16, 23]  # start row of each planting block
    found = []
    for r in blocks:
        species = text(vs, f"D{r + 2}")
        area    = num(vs, f"D{r + 4}")
        age     = num(vs, f"D{r + 5}")
        if species and "no tree data" not in species.lower() and (area or age):
            found.append({
                "state":   text(vs, f"D{r}"),
                "region":  text(vs, f"D{r + 1}"),
                "species": species,
                "soilType": text(vs, f"D{r + 3}"),
                "area_ha": area,
                "age_years": age,
            })
    return found
 
# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW  ->", API_URL)
print("=" * 25)
print(json.dumps(payload, indent=2))
 
print("\n" + "=" * 25)
print("FLAGS TO CONFIRM WITH AIA (not blocking):")
print("=" * 25)
print(f"- state: region code {di['D3'].value} -> {payload['state']!r}. "
      "wa_sw / wa_nw enum strings remain UNCONFIRMED.")
print(f"- electricityRenewable sent as {buffalo['electricityRenewable']} "
      "(raw fraction). Confirm API wants fraction (0.2) vs percent (20).")
print(f"- otherFertilisers[0].otherType = {other_type!r}. "
      "Confirm this exact string is a valid API enum.")
_veg = read_vegetation_plantings()
if _veg:
    print(f"- vegetation sent as []. Workbook 'Data input - vegetation' contains "
          f"{len(_veg)} tree planting(s) that are OMITTED because the API "
          "vegetation object schema was not provided:")
    for p in _veg:
        print(f"    * {p['species']} | {p['state']}/{p['region']} | "
              f"{p['soilType']} | {p['area_ha']} ha | {p['age_years']} yrs")
    print("  (Data summary reports tree sequestration of -23.6 t CO2e, so the "
          "API net will differ until vegetation is wired in.)")
 
# =========================
# POST
# =========================
headers = {"Content-Type": "application/json"}
 
print("\n" + "=" * 25)
print("SENDING...")
print("=" * 25)
 
response = requests.post(
    API_URL,
    headers=headers,
    data=json.dumps(payload),
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)
 
print("Status:", response.status_code)
print(response.text)