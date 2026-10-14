"""
EAP Wine Payload.py
=========================
EAP flat-CSV -> Environmental Accounting Platform connector for WINE / GRAPES.

Reads a two-column (key,value) EAP export via pandas, rebuilds the nested
JSON payload, and POSTs it (mTLS) to the vineyard emissions endpoint.

Commodity : Wine / grapes (vineyard side)
Source    : EAP flat-CSV export ("EAP Wine (3.0.0).csv")
Endpoint  : /calculator/3.0.2/vineyard
Pattern   : EAP flat-CSV

The EAP export is already API-shaped: leaf values are in final enum form
(e.g. "sa", "diesel", "Managed Aerobic"), so no lookup/normalise tables are
needed - only safe type coercion (f/b/s) and structural reconstruction.
=========================
"""

import json
import requests
import pandas as pd

# =========================
# CONFIG
# =========================
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/vineyard"

# >>> Single hardcoded CSV path (no glob auto-detection).
#     Copy the EXACT export filename here - spaces, fullstops and brackets
#     preserved, no substitution with underscores.  <<< CONFIRM
#     (The CSV is labelled 3.0.0; we POST to the confirmed-working 3.0.2
#      vineyard endpoint, which accepts this same field set.  >>> FLAG version)
CSV_PATH  = r"your file path here"

CERT_PEM  = r"your file path here"
CERT_KEY  = r"your file path here"

# =========================
# LOAD FLAT DICT
# =========================
df = pd.read_csv(CSV_PATH, dtype=str)
df["key"] = df["key"].str.strip()
flat = dict(zip(df["key"], df["value"]))

# =========================
# HELPERS  (safe coercion trio)
# =========================
def f(key):
    """Safe float. Missing / blank / non-numeric -> 0.0"""
    v = flat.get(key)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def b(key):
    """Safe bool. 'true'/'1'/'yes' -> True, everything else -> False"""
    v = flat.get(key)
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    return False

def s(key, default=""):
    """Safe string. Missing / NaN -> default"""
    v = flat.get(key)
    if v is None or (isinstance(v, float) and v != v):
        return default
    return str(v).strip()

# =========================
# BUILDERS  (one per structural shape; empty arrays get a zeroed default)
# =========================
def build_fuel_list(p, kind):
    """kind = 'stationary fuel' or 'transport fuel'"""
    out, j = [], 0
    while f"{p}fuel_{kind}_{j}_type" in flat:
        out.append({
            "type": s(f"{p}fuel_{kind}_{j}_type", "diesel"),
            "amountLitres": f(f"{p}fuel_{kind}_{j}_amount litres"),
        })
        j += 1
    if not out:
        out = [{"type": "diesel", "amountLitres": 0}]   # never send empty
    return out

def build_fluid_waste(p):
    out, j = [], 0
    while f"{p}fluid waste_{j}_fluid waste kl" in flat:
        out.append({
            "fluidWasteKl": f(f"{p}fluid waste_{j}_fluid waste kl"),
            "fluidWasteTreatmentType": s(f"{p}fluid waste_{j}_fluid waste treatment type", "Managed Aerobic"),
            "averageInletCOD": f(f"{p}fluid waste_{j}_average inlet cod"),
            "averageOutletCOD": f(f"{p}fluid waste_{j}_average outlet cod"),
            "flaredCombustedFraction": f(f"{p}fluid waste_{j}_flared combusted fraction"),
        })
        j += 1
    if not out:
        out = [{
            "fluidWasteKl": 0,
            "fluidWasteTreatmentType": "Managed Aerobic",
            "averageInletCOD": 0,
            "averageOutletCOD": 0,
            "flaredCombustedFraction": 0,
        }]
    return out

def build_freight(p, direction):
    """direction = 'inbound freight' or 'outbound freight' (absent in this export)"""
    out, j = [], 0
    while f"{p}{direction}_{j}_type" in flat:
        out.append({
            "type": s(f"{p}{direction}_{j}_type", "Truck"),
            "totalKmTonnes": f(f"{p}{direction}_{j}_total km tonnes"),
        })
        j += 1
    if not out:
        out = [{"type": "Truck", "totalKmTonnes": 0}]
    return out

def build_vineyard(i):
    p = f"vineyards_{i}_"
    return {
        "id": s(p + "id"),
        "state": s(p + "state", "nsw"),
        "rainfallAbove600": b(p + "rainfall above 600"),
        "irrigated": b(p + "irrigated"),
        "areaPlanted": f(p + "area planted"),
        "averageYield": f(p + "average yield"),
        "nonUreaNitrogen": f(p + "non urea nitrogen"),
        "phosphorusApplication": f(p + "phosphorus application"),
        "potassiumApplication": f(p + "potassium application"),
        "sulfurApplication": f(p + "sulfur application"),
        "ureaApplication": f(p + "urea application"),
        "ureaAmmoniumNitrate": f(p + "urea ammonium nitrate"),
        "limestone": f(p + "limestone"),
        "limestoneFraction": f(p + "limestone fraction"),
        "herbicideUse": f(p + "herbicide use"),
        "glyphosateOtherHerbicideUse": f(p + "glyphosate other herbicide use"),
        "electricityRenewable": f(p + "electricity renewable"),
        "electricityUse": f(p + "electricity use"),
        "electricitySource": s(p + "electricity source", "State Grid"),
        "fuel": {
            "transportFuel": build_fuel_list(p, "transport fuel"),
            "stationaryFuel": build_fuel_list(p, "stationary fuel"),
            "naturalGas": f(p + "fuel_natural gas"),
        },
        "fluidWaste": build_fluid_waste(p),
        "solidWaste": {
            "sentOffsiteTonnes": f(p + "solid waste_sent offsite tonnes"),
            "onsiteCompostingTonnes": f(p + "solid waste_onsite composting tonnes"),
        },
        "inboundFreight": build_freight(p, "inbound freight"),
        "outboundFreight": build_freight(p, "outbound freight"),
        "totalCommercialFlightsKm": f(p + "total commercial flights km"),
    }

def build_vegetation():
    out, k = [], 0
    while f"vegetation_{k}_vegetation_region" in flat:
        vp = f"vegetation_{k}_"
        area = f(vp + "vegetation_area")
        age  = f(vp + "vegetation_age")
        if area == 0 and age == 0:          # skip empty blocks
            k += 1
            continue
        alloc, m = [], 0
        while f"{vp}allocation to vineyards_{m}" in flat:
            alloc.append(f(f"{vp}allocation to vineyards_{m}"))
            m += 1
        if not alloc:
            alloc = [0]
        out.append({
            "vegetation": {
                "region": s(vp + "vegetation_region"),
                "treeSpecies": s(vp + "vegetation_tree species"),
                "soil": s(vp + "vegetation_soil"),
                "area": area,
                "age": age,
            },
            "allocationToVineyards": alloc,
        })
        k += 1
    if not out:                              # never send empty (none in this export)
        out = [{
            "vegetation": {
                "region": "South West",
                "treeSpecies": "Mixed species (Environmental Plantings)",
                "soil": "Loams & Clays",
                "area": 0,
                "age": 0,
            },
            "allocationToVineyards": [0],
        }]
    return out

# =========================
# ASSEMBLE PAYLOAD  (enterprise loop keyed on _id)
# =========================
vineyards, i = [], 0
while f"vineyards_{i}_id" in flat:
    vineyards.append(build_vineyard(i))
    i += 1

payload = {
    "vineyards": vineyards,
    "vegetation": build_vegetation(),
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
# POST
# =========================
print("\nPOSTing to:", API_URL)
resp = requests.post(
    API_URL,
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload),
    cert=(CERT_PEM, CERT_KEY),
    verify=True,
)
print("Status:", resp.status_code)
print(resp.text)