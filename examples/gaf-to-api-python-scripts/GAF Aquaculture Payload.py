import openpyxl
import requests
import json

# =========================
# CONFIG
# =========================
# >>> ENTERPRISE-SPECIFIC: path to the completed G-GAF workbook
XLSX_FILE = r"your path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/aquaculture"
CERT_FILE = r"your path here"
KEY_FILE  = r"your path here"

# >>> ENTERPRISE-SPECIFIC: sheet names inside the G-GAF workbook
FARM_SHEET   = "Input - Farm"
ELEC_SHEET   = "Input - Electricity & Fuel"
WASTE_SHEET  = "Input - Waste & Outputs"
TRAVEL_SHEET = "Input - Travel & freight"

# =========================
# LOAD WORKBOOK
# =========================
wb = openpyxl.load_workbook(XLSX_FILE, data_only=True)
ws_farm   = wb[FARM_SHEET]
ws_elec   = wb[ELEC_SHEET]
ws_waste  = wb[WASTE_SHEET]
ws_travel = wb[TRAVEL_SHEET]

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

def is_set(value):
    """True if a dropdown/text cell holds a real selection (not blank,
    'None', or an unfilled '<- Please select' placeholder)."""
    if value is None:
        return False
    v = str(value).strip().lower()
    return v not in ("", "none", "please select", "\u2190 please select")

# =========================
# >>> ENTERPRISE-SPECIFIC: ENUM NORMALISATION
# Unlike the Grains workbook (which stores crop type/production system/
# state as numeric codes needing a lookup table), this aquaculture
# workbook stores plain text labels directly. The wording/casing of those
# labels doesn't always match the API's expected enum strings, so we
# normalise the ones we've been able to confirm against a live submission.
# Anything not in a map falls back to a Title Case guess and prints a
# warning, so an unfamiliar fuel/freight type on a future workbook is easy
# to spot rather than silently sent wrong.
# =========================
FUEL_TYPE_MAP = {
    "petrol":                        "petrol",              # unconfirmed
    "diesel":                        "diesel",               # confirmed
    "liquefied petroleum gas (lpg)": "lpg",                  # confirmed
    "fuel oil":                      "fuel oil",             # unconfirmed
    "ethanol":                       "ethanol",              # unconfirmed
    "biodiesel":                     "biodiesel",            # unconfirmed
    "renewable diesel":              "renewable diesel",     # unconfirmed
    "other biofuels":                "other biofuels",       # unconfirmed
    "liquified natural gas (lng)":   "lng",                  # unconfirmed
}

FREIGHT_TYPE_MAP = {
    "transport in truck":   "Truck",                 # confirmed
    "rail":                 "Rail",                  # unconfirmed
    "long haul flight":     "Long Haul Flight",      # unconfirmed
    "medium haul flight":   "Medium Haul Flight",    # unconfirmed
    "small container ship": "Small Container Ship",  # unconfirmed
    "large container ship": "Large Container Ship",  # unconfirmed
}

TREATMENT_TYPE_MAP = {
    "unmanaged aerobic treatment": "Unmanaged Aerobic",  # confirmed
    "managed aerobic treatment":   "Managed Aerobic",    # unconfirmed
}

def normalize_enum(raw_value, table, label):
    key = str(raw_value).strip().lower()
    if key in table:
        return table[key]
    print(f"WARNING: unrecognised {label}: {raw_value!r} (using Title Case fallback)")
    return key.replace("treatment", "").strip().title()

# =========================
# FARM-LEVEL FIELDS
# >>> ENTERPRISE-SPECIFIC: fixed row/column positions in "Input - Farm"
# =========================
STATE_CELL = (5, 3)  # row 5, col C - "Region in Australia where operation is"

farm_state = s(ws_farm.cell(*STATE_CELL).value).lower()

# =========================
# >>> ENTERPRISE-SPECIFIC: ENTERPRISE (PRODUCTION SYSTEM) BLOCKS
# The workbook supports up to two production systems, each a fixed block
# of rows in "Input - Farm". Block two omits the "Region" sub-section
# that block one has, so the row numbers differ between blocks and are
# listed explicitly rather than derived from a shared offset.
# =========================
ENTERPRISE_VALUE_COL = 3  # column C - holds name / production system / harvest kg

ENTERPRISE_BLOCKS = [
    {   # Production system one
        "name_row": 9, "prod_system_row": 10, "harvest_kg_row": 11,
        "refrigerant_rows": [17, 18, 19, 20],
        "feed_tonnes_row": 26, "feed_type_row": 27,
        "feed_pct_row": 28, "feed_ei_row": 29, "feed_custom_ei_row": 30,
    },
    {   # Production system two
        "name_row": 36, "prod_system_row": 37, "harvest_kg_row": 38,
        "refrigerant_rows": [44, 45, 46, 47],
        "feed_tonnes_row": 53, "feed_type_row": 54,
        "feed_pct_row": 55, "feed_ei_row": 56, "feed_custom_ei_row": 57,
    },
]

REFRIGERANT_TYPE_COL     = 3  # column C
REFRIGERANT_RECHARGE_COL = 5  # column E
FEED_COLUMNS       = [3, 4, 5, 6]  # Feed 1-4, columns C-F
CUSTOM_FEED_COLUMN = 7             # Feed 5 (custom), column G

# =========================
# BUILD REFRIGERANTS FOR AN ENTERPRISE BLOCK
# e.g. "Refrigerant 1".."Refrigerant 4" rows, type + annual recharge
# =========================
def build_refrigerants(block):
    items = []
    for row in block["refrigerant_rows"]:
        rtype = s(ws_farm.cell(row=row, column=REFRIGERANT_TYPE_COL).value)
        if not is_set(rtype):
            continue
        items.append({
            "refrigerant": rtype,
            "chargeSize":  f(ws_farm.cell(row=row, column=REFRIGERANT_RECHARGE_COL).value),
        })
    if not items:
        items.append({"refrigerant": "HFC-23", "chargeSize": 0})
    return items

# =========================
# BUILD BAIT + CUSTOM BAIT FOR AN ENTERPRISE BLOCK
# Feed 1-4 (columns C-F) are standard bait entries; Feed 5 (column G) is
# always the custom-blend entry, mapped separately to customBait.
# =========================
def build_bait_and_custom(block):
    bait = []
    for col in FEED_COLUMNS:
        ftype = s(ws_farm.cell(row=block["feed_type_row"], column=col).value)
        if not is_set(ftype):
            continue
        bait.append({
            "type":                  ftype,
            "purchasedTonnes":       f(ws_farm.cell(row=block["feed_tonnes_row"], column=col).value),
            "additionalIngredients": f(ws_farm.cell(row=block["feed_pct_row"], column=col).value),
            "emissionsIntensity":    f(ws_farm.cell(row=block["feed_ei_row"], column=col).value),
        })
    if not bait:
        bait.append({
            "type": "Whole Sardines", "purchasedTonnes": 0,
            "additionalIngredients": 0, "emissionsIntensity": 0,
        })

    custom = []
    custom_tonnes = ws_farm.cell(row=block["feed_tonnes_row"], column=CUSTOM_FEED_COLUMN).value
    if custom_tonnes is not None:
        custom.append({
            "purchasedTonnes":    f(custom_tonnes),
            "emissionsIntensity": f(ws_farm.cell(row=block["feed_custom_ei_row"], column=CUSTOM_FEED_COLUMN).value),
        })
    if not custom:
        custom.append({"purchasedTonnes": 0, "emissionsIntensity": 0})

    return bait, custom

# =========================
# ELECTRICITY (farm-wide - not split per production system)
# >>> ENTERPRISE-SPECIFIC: fixed row positions in "Input - Electricity & Fuel"
# Each field has both a direct-entry and an estimated-entry column; column F
# always holds the workbook's own resolved value, so we just read that.
# =========================
RESOLVED_COL = 6  # column F

ELEC_NONRENEWABLE_ROW = 9
ELEC_RENEWABLE_ROW    = 10

electricity_nonrenewable = f(ws_elec.cell(row=ELEC_NONRENEWABLE_ROW, column=RESOLVED_COL).value)
electricity_renewable    = f(ws_elec.cell(row=ELEC_RENEWABLE_ROW, column=RESOLVED_COL).value)
electricity_use          = electricity_nonrenewable + electricity_renewable

# =========================
# FUEL (farm-wide)
# Machinery/generator fuel -> stationaryFuel
# Road vehicle + marine craft fuel -> transportFuel (summed by fuel type)
# =========================
STATIONARY_FUEL_ROWS = {
    "petrol": 20, "diesel": 21, "liquefied petroleum gas (lpg)": 22,
    "ethanol": 23, "biodiesel": 24, "renewable diesel": 25,
    "other biofuels": 26, "liquified natural gas (lng)": 27,
}
NATURAL_GAS_ROW = 28

ROAD_VEHICLE_FUEL_ROWS = {
    "petrol": 37, "diesel": 38, "liquefied petroleum gas (lpg)": 39,
    "fuel oil": 40, "ethanol": 41, "biodiesel": 42,
    "renewable diesel": 43, "other biofuels": 44, "liquified natural gas (lng)": 45,
}

MARINE_CRAFT_FUEL_ROWS = {
    "petrol": 55, "diesel": 56, "liquefied petroleum gas (lpg)": 57,
    "fuel oil": 58, "ethanol": 59, "biodiesel": 60,
    "renewable diesel": 61, "other biofuels": 62, "liquified natural gas (lng)": 63,
}

def read_fuel_rows(row_map):
    result = {}
    for label, row in row_map.items():
        litres = f(ws_elec.cell(row=row, column=RESOLVED_COL).value)
        if litres:
            mapped = FUEL_TYPE_MAP.get(label, label)
            result[mapped] = result.get(mapped, 0) + litres
    return result

stationary_fuel = read_fuel_rows(STATIONARY_FUEL_ROWS)
transport_fuel  = read_fuel_rows(ROAD_VEHICLE_FUEL_ROWS)
for fuel_type, litres in read_fuel_rows(MARINE_CRAFT_FUEL_ROWS).items():
    transport_fuel[fuel_type] = transport_fuel.get(fuel_type, 0) + litres

natural_gas = f(ws_elec.cell(row=NATURAL_GAS_ROW, column=RESOLVED_COL).value)

def to_fuel_list(fuel_dict, default_type="petrol"):
    items = [{"type": t, "amountLitres": amt} for t, amt in fuel_dict.items()]
    if not items:
        items.append({"type": default_type, "amountLitres": 0})
    return items

fuel_block = {
    "transportFuel":  to_fuel_list(transport_fuel),
    "stationaryFuel": to_fuel_list(stationary_fuel),
    "naturalGas":     natural_gas,
}

# =========================
# WASTE (farm-wide)
# >>> ENTERPRISE-SPECIFIC: fixed row positions in "Input - Waste & Outputs"
# =========================
WASTE_RESOLVED_COL = 5  # column E

FLUID_WASTE_USED_ROW = 5
FLUID_WASTE_KL_ROW   = 7
TREATMENT_TYPE_ROW   = 9
INLET_COD_ROW        = 10
OUTLET_COD_ROW       = 11
FLARED_FRACTION_ROW  = 12
OFFSITE_TONNES_ROW   = 19
COMPOST_TONNES_ROW   = 20

fluid_waste_used = yes_no(ws_waste.cell(row=FLUID_WASTE_USED_ROW, column=3).value)

if fluid_waste_used:
    fluid_waste = [{
        "fluidWasteKl":            f(ws_waste.cell(row=FLUID_WASTE_KL_ROW, column=WASTE_RESOLVED_COL).value),
        "fluidWasteTreatmentType": normalize_enum(
            ws_waste.cell(row=TREATMENT_TYPE_ROW, column=WASTE_RESOLVED_COL).value,
            TREATMENT_TYPE_MAP, "fluid waste treatment type"
        ),
        "averageInletCOD":         f(ws_waste.cell(row=INLET_COD_ROW, column=WASTE_RESOLVED_COL).value),
        "averageOutletCOD":        f(ws_waste.cell(row=OUTLET_COD_ROW, column=WASTE_RESOLVED_COL).value),
        "flaredCombustedFraction": f(ws_waste.cell(row=FLARED_FRACTION_ROW, column=WASTE_RESOLVED_COL).value),
    }]
else:
    fluid_waste = [{
        "fluidWasteKl": 0, "fluidWasteTreatmentType": "Managed Aerobic",
        "averageInletCOD": 0, "averageOutletCOD": 0, "flaredCombustedFraction": 0,
    }]

solid_waste = {
    "sentOffsiteTonnes":      f(ws_waste.cell(row=OFFSITE_TONNES_ROW, column=WASTE_RESOLVED_COL).value),
    "onsiteCompostingTonnes": f(ws_waste.cell(row=COMPOST_TONNES_ROW, column=WASTE_RESOLVED_COL).value),
}

# =========================
# FREIGHT + COMMERCIAL FLIGHTS (farm-wide)
# >>> ENTERPRISE-SPECIFIC: fixed row positions in "Input - Travel & freight"
# =========================
OUTBOUND_FREIGHT_ROWS = {  # Freight - Post farm (downstream)
    "transport in truck": 10, "rail": 11, "long haul flight": 12,
    "medium haul flight": 13, "small container ship": 14, "large container ship": 15,
}
INBOUND_FREIGHT_ROWS = {  # Freight - Pre farm (upstream)
    "transport in truck": 24, "rail": 25, "long haul flight": 26,
    "medium haul flight": 27, "small container ship": 28, "large container ship": 29,
}
TOTAL_FLIGHTS_KM_ROW = 38

def read_freight_rows(row_map):
    items = []
    for label, row in row_map.items():
        val = f(ws_travel.cell(row=row, column=RESOLVED_COL).value)
        if val:
            items.append({
                "type":          FREIGHT_TYPE_MAP.get(label, label.title()),
                "totalKmTonnes": val,
            })
    if not items:
        items.append({"type": "Truck", "totalKmTonnes": 0})
    return items

outbound_freight = read_freight_rows(OUTBOUND_FREIGHT_ROWS)
inbound_freight  = read_freight_rows(INBOUND_FREIGHT_ROWS)
total_flights_km = f(ws_travel.cell(row=TOTAL_FLIGHTS_KM_ROW, column=RESOLVED_COL).value)

# =========================
# BUILD ENTERPRISES LIST
# Electricity, fuel, waste, and freight are farm-wide in this workbook and
# are applied to every populated enterprise block.
# =========================
enterprises = []
for block in ENTERPRISE_BLOCKS:
    name = s(ws_farm.cell(row=block["name_row"], column=ENTERPRISE_VALUE_COL).value)
    if not is_set(name):
        continue  # unpopulated production-system block

    production_system = s(ws_farm.cell(row=block["prod_system_row"], column=ENTERPRISE_VALUE_COL).value).title()
    bait, custom_bait = build_bait_and_custom(block)

    enterprises.append({
        "id":                       "",
        "state":                    farm_state,
        "productionSystem":         production_system,
        "totalHarvestKg":           f(ws_farm.cell(row=block["harvest_kg_row"], column=ENTERPRISE_VALUE_COL).value),
        "refrigerants":             build_refrigerants(block),
        "bait":                     bait,
        "customBait":               custom_bait,
        "inboundFreight":           inbound_freight,
        "outboundFreight":          outbound_freight,
        "totalCommercialFlightsKm": total_flights_km,
        "electricityRenewable":     electricity_renewable,
        "electricityUse":           electricity_use,
        "electricitySource":        "State Grid",
        "fuel":                     fuel_block,
        "fluidWaste":               fluid_waste,
        "solidWaste":               solid_waste,
        "carbonOffsets":            0,
    })

if not enterprises:
    raise ValueError("No populated enterprise blocks found in 'Input - Farm'.")

# =========================
# BUILD FULL PAYLOAD
# =========================
payload = {
    "enterprises": enterprises,
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
