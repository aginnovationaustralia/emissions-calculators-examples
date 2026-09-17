"""
=========================
GAF Wild Fisheries Payload
=========================
Reads a completed Wild Catch Fishery GAF workbook (multi-sheet .xlsx) directly
via openpyxl, decodes it into the wildseafisheries API schema, previews the
payload, and POSTs it to AIA's mTLS-secured Emissions Calculator API.

Pattern: GAF direct-xlsx (openpyxl, data_only=True, fixed row/col constants,
single hardcoded XLSX_PATH, single zeroed default for empty repeating arrays).
"""

import json
import warnings
import openpyxl
import requests

warnings.simplefilter("ignore")  # openpyxl DrawingML / data-validation warnings are harmless

# =========================
# CONFIG
# =========================
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/wildseafisheries"
CERT_PATH = r"your path here"
KEY_PATH  = r"your path here"
# Full stops and spaces in the filename are preserved exactly as they appear on disk.
XLSX_PATH = r"your path here"

wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)

# =========================
# SHEET HANDLES  >>> ENTERPRISE-SPECIFIC
# =========================
FISH = wb["Input - Fishery"]              # state, harvest weight, refrigerants, bait
ELEC = wb["Input - Electricity & Fuel"]   # electricity + all fuel categories
TRAV = wb["Input - Travel & freight"]     # commercial flights (Scope 3)
SUMM = wb["Summary - Fishery"]            # purchased carbon offset (direct-entered value)

# =========================
# LOOKUPS  >>> ENTERPRISE-SPECIFIC
# =========================
# State display -> API enum string. Source: 'Electricity' sheet state list.
# NOTE: wa_sw / wa_nw remain UNCONFIRMED with AIA across all scripts - flagged.
STATE_LOOKUP = {
    "NSW": "nsw",
    "ACT": "act",
    "VIC": "vic", "VICTORIA": "vic",
    "QLD": "qld", "QUEENSLAND": "qld",
    "SA": "sa", "SOUTH AUSTRALIA": "sa",
    "TAS": "tas", "TASMANIA": "tas",
    "NT": "nt", "NORTHERN TERRITORY": "nt",
    "SW WA": "wa_sw", "NW WA": "wa_nw",   # <<< wa_sw / wa_nw UNCONFIRMED
    "WA": "wa_sw", "WESTERN AUSTRALIA": "wa_sw",  # WA is split SW/NW in this tool - defaulting SW
}

# Electricity source: the fishery input sheet has no source selector; the
# 'Electricity' calc sheet uses "State Grid" as the default source for this tool.
DEFAULT_ELECTRICITY_SOURCE = "State Grid"

# =========================
# SAFE VALUE HELPERS
# =========================
def f(v):
    """Safe float."""
    try:
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def s(v):
    """Safe string."""
    return "" if v is None else str(v).strip()

def is_set(v):
    """True when a cell holds a real, selected value (not blank / placeholder)."""
    if v is None:
        return False
    t = str(v).strip().lower()
    return t not in ("", "none", "n/a", "please select", "← please select", "0")

def entry_uses_direct(toggle_value):
    """A 'How do you want to enter this information?' toggle: 'Enter values directly'
    -> use the direct-entry column; 'Calculate values' -> use the estimated column."""
    return "direct" in s(toggle_value).lower()

def toggle_yes(v):
    """A 'Were X used?' master gate."""
    return s(v).lower().startswith("y")

def state_enum(display):
    key = s(display).upper()
    if key in STATE_LOOKUP:
        return STATE_LOOKUP[key]
    print(f"  [WARN] Unrecognised state {display!r} - passing through raw. Verify enum with AIA.")
    return s(display).lower()

# =========================
# ELECTRICITY  >>> ENTERPRISE-SPECIFIC
# =========================
# Toggle C6: 'Enter values directly' (C9 non-renewable + C10 renewable) vs
# 'Renewable calculator' (J9 total, J10 percent renewable).
def build_electricity():
    if entry_uses_direct(ELEC["C6"].value):
        non_renewable = f(ELEC["C9"].value)
        renewable     = f(ELEC["C10"].value)
        total_use     = non_renewable + renewable
        renewable_val = renewable                       # kWh
    else:
        total_use     = f(ELEC["J9"].value)             # total kWh
        pct           = f(ELEC["J10"].value)            # percent renewable (fraction or %)
        renewable_val = total_use * (pct / 100.0 if pct > 1 else pct)
    return total_use, renewable_val

# =========================
# FUEL (diesel / petrol / lpg)  >>> ENTERPRISE-SPECIFIC
# =========================
# The workbook has three petrol/diesel/lpg-using fuel categories, each with a
# master "Were X used?" gate and a direct/estimated entry toggle:
#   Machinery/generator : gate C15, toggle C17, petrol C20/D20, diesel C21/D21, lpg C22/D22
#   Road vehicle/loader : gate C32, toggle C34, petrol C37/D37, diesel C38/D38, lpg C39/D39
#   Marine craft        : gate C50, toggle C52, petrol C55/D55, diesel C56/D56, lpg C57/D57
# (Light aircraft uses avgas/jet only - not part of the diesel/petrol/lpg fields.)
# A category contributes 0 when its master gate is "No" - matching the workbook's
# Summary "Fuel (Scope 1)" figure.
FUEL_CATEGORIES = [
    # (gate_cell, toggle_cell, petrol_direct, petrol_est, diesel_direct, diesel_est, lpg_direct, lpg_est)
    ("C15", "C17", "C20", "D20", "C21", "D21", "C22", "D22"),  # Machinery / generator
    ("C32", "C34", "C37", "D37", "C38", "D38", "C39", "D39"),  # Road vehicle / loader
    ("C50", "C52", "C55", "D55", "C56", "D56", "C57", "D57"),  # Marine craft
]

def build_fuel_totals():
    petrol = diesel = lpg = 0.0
    for gate, toggle, p_d, p_e, d_d, d_e, l_d, l_e in FUEL_CATEGORIES:
        if not toggle_yes(ELEC[gate].value):
            continue  # section switched off - contributes nothing
        direct = entry_uses_direct(ELEC[toggle].value)
        petrol += f(ELEC[p_d].value if direct else ELEC[p_e].value)
        diesel += f(ELEC[d_d].value if direct else ELEC[d_e].value)
        lpg    += f(ELEC[l_d].value if direct else ELEC[l_e].value)
    return diesel, petrol, lpg

# =========================
# REFRIGERANTS  >>> ENTERPRISE-SPECIFIC
# =========================
# Input - Fishery rows 17-20: type in C, annual recharge in E.
def build_refrigerants():
    out = []
    for row in range(17, 21):
        rtype = FISH[f"C{row}"].value
        if is_set(rtype):
            out.append({
                "refrigerant": s(rtype),
                "annualRecharge": f(FISH[f"E{row}"].value),
            })
    if not out:  # never send an empty array
        out.append({"refrigerant": "HFC-23", "annualRecharge": 0})
    return out

# =========================
# BAIT + CUSTOM BAIT  >>> ENTERPRISE-SPECIFIC
# =========================
# Input - Fishery bait block (row header / columns):
#   amount purchased (tonnes)  row 26   Bait1 C, Bait2 D, Bait3 E, Bait4 F, Custom G
#   primary ingredient         row 27
#   % additional ingredients   row 28
#   EI of additional ingred.   row 29
#   EI of custom bait          row 30 (custom column only)
STANDARD_BAIT_COLS = ["C", "D", "E", "F"]   # Bait 1-4
CUSTOM_BAIT_COL    = "G"                     # Bait 5 (custom)

def build_bait():
    out = []
    for col in STANDARD_BAIT_COLS:
        btype = FISH[f"{col}27"].value
        purchased = f(FISH[f"{col}26"].value)
        if is_set(btype) or purchased > 0:
            out.append({
                "type": s(btype),
                "purchased": purchased,
                "additionalIngredient": f(FISH[f"{col}28"].value),
                "emissionsIntensity": f(FISH[f"{col}29"].value),
            })
    if not out:  # never send an empty array
        out.append({"type": "Fish Frames", "purchased": 0,
                    "additionalIngredient": 0, "emissionsIntensity": 0})
    return out

def build_custom_bait():
    out = []
    purchased = f(FISH[f"{CUSTOM_BAIT_COL}26"].value)
    ei        = f(FISH[f"{CUSTOM_BAIT_COL}30"].value)
    if purchased > 0 or ei > 0:
        out.append({"purchased": purchased, "emissionsIntensity": ei})
    if not out:  # never send an empty array
        out.append({"purchased": 0, "emissionsIntensity": 0})
    return out

# =========================
# FLIGHTS (Scope 3 commercial air travel)  >>> ENTERPRISE-SPECIFIC
# =========================
# Input - Travel & freight: gate C33, entry toggle C35, total km C38 (direct) / D38 (est).
# The workbook records TOTAL km across all passengers, so passengers=1 preserves the total.
def build_flights():
    out = []
    if toggle_yes(TRAV["C33"].value):
        distance = f(TRAV["C38"].value) if entry_uses_direct(TRAV["C35"].value) else f(TRAV["D38"].value)
        if distance > 0:
            out.append({"commercialFlightPassengers": 1, "totalFlightDistance": distance})
    if not out:  # never send an empty array
        out.append({"commercialFlightPassengers": 0, "totalFlightDistance": 0})
    return out

# =========================
# TRANSPORTS  >>> ENTERPRISE-SPECIFIC  <<< NEEDS AIA CONFIRMATION
# =========================
# The wildseafisheries schema's transports[] entry is {type, fuel, distance} and uses
# its own enum vocabulary (example fuel "Gasoline", not the workbook's "Petrol").
# The workbook's road-vehicle detail is already captured in the diesel/petrol/lpg
# totals above, so mapping it here as well would DOUBLE-COUNT. Until AIA confirms
# what transports[] is meant to carry, we send the schema's zeroed default entry.
def build_transports():
    return [{"type": "None", "fuel": "Gasoline", "distance": 0}]

# =========================
# ASSEMBLE ENTERPRISE
# =========================
electricity_use, electricity_renewable = build_electricity()
diesel, petrol, lpg = build_fuel_totals()

enterprise = {
    "id": "",
    "state": state_enum(FISH["C5"].value),
    "electricitySource": DEFAULT_ELECTRICITY_SOURCE,
    "electricityRenewable": electricity_renewable,          # kWh (see flag below)
    "electricityUse": electricity_use,                      # total kWh
    "totalWholeWeightCaught": f(FISH["C11"].value),        # kilograms (workbook native unit)
    "diesel": diesel,
    "petrol": petrol,
    "lpg": lpg,
    "refrigerants": build_refrigerants(),
    "transports": build_transports(),
    "flights": build_flights(),
    "bait": build_bait(),
    "custombait": build_custom_bait(),
    "carbonOffset": f(SUMM["B31"].value),                   # purchased offset (t CO2-e)
}

payload = {"enterprises": [enterprise]}

# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 60)
print("PAYLOAD PREVIEW")
print("=" * 60)
print(json.dumps(payload, indent=2))
print("=" * 60)

# =========================
# POST
# =========================
headers = {"Content-Type": "application/json"}

response = requests.post(
    API_URL,
    headers=headers,
    data=json.dumps(payload),
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("\nHTTP status:", response.status_code)
print("Response:")
print(response.text)
