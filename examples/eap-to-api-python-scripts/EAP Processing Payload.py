"""
EAP Processing Payload.py
=========================
Connects a completed *Processing* module CSV export from the Environmental
Accounting Platform (EAP) front end to the AIA Emissions Calculator API
(processing endpoint, v3.0.2).

Pattern: EAP flat-CSV. A two-column key/value export is loaded via pandas into
a flat dict, then walked with while-loops over the underscore-delimited key
paths. Field segments themselves can contain spaces (e.g. "electricity use");
the underscore is the path delimiter, spaces are part of a segment name.

Source export : Processing EAP 3.0.0.csv   (key,value two-column CSV)
Endpoint      : POST /calculator/3.0.2/processing
Auth          : mTLS (.pem client cert + .key file), verify=True
"""

import json
import pandas as pd
import requests

# =========================
# CONFIG
# =========================
# >>> CSV filename copied EXACTLY as it appears on disk — spaces and full
#     stops preserved, NO underscore substitution.
CSV_PATH  = r"your file path here"
CERT_PATH = r"your file path here"
KEY_PATH  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/processing"

# =========================
# LOAD FLAT CSV
# =========================
df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
flat = dict(zip(df["key"].astype(str).str.strip(), df["value"]))

# =========================
# SAFE COERCION HELPERS
# =========================
def num(key, default=0):
    """Safe numeric from the flat dict; returns int when whole, else float."""
    if key not in flat:
        return default
    v = flat[key]
    if v is None or str(v).strip() == "":
        return default
    try:
        fv = float(v)
    except (ValueError, TypeError):
        return default
    return int(fv) if fv.is_integer() else fv

def text(key, default=""):
    """Safe string from the flat dict."""
    if key not in flat:
        return default
    v = flat[key]
    if v is None:
        return default
    v = str(v).strip()
    return v if v != "" else default

# =========================
# REPEATING-ARRAY BUILDERS
# Never send an empty array — each builder falls back to a single
# zeroed-but-valid entry so the API always receives a well-formed list.
# =========================
def build_fuel(base):
    """
    Build a fuel list (transport OR stationary).
      base e.g. 'products_0_fuel_stationary fuel'
      keys   : {base}_{i}_type , {base}_{i}_amount litres
    >>> FLAG: transport-fuel rows are absent from this sample export, so the
        transport key spellings mirror the confirmed stationary-fuel spellings.
    """
    out = []
    i = 0
    while f"{base}_{i}_type" in flat or f"{base}_{i}_amount litres" in flat:
        out.append({
            "type": text(f"{base}_{i}_type", "petrol"),
            "amountLitres": num(f"{base}_{i}_amount litres"),
        })
        i += 1
    if not out:
        out.append({"type": "petrol", "amountLitres": 0})
    return out

def build_refrigerants(base):
    """
    base e.g. 'products_0_refrigerants'
    keys   : {base}_{i}_refrigerant , {base}_{i}_charge size
    """
    out = []
    i = 0
    while f"{base}_{i}_refrigerant" in flat or f"{base}_{i}_charge size" in flat:
        out.append({
            "refrigerant": text(f"{base}_{i}_refrigerant", "HFC-23"),
            "chargeSize": num(f"{base}_{i}_charge size"),
        })
        i += 1
    if not out:
        out.append({"refrigerant": "HFC-23", "chargeSize": 0})
    return out

def build_fluid_waste(base):
    """
    base e.g. 'products_0_fluid waste'
    >>> FLAG: this sample export contains no fluid-waste rows, so the exact EAP
        key spellings below are INFERRED from the schema and the export's naming
        convention. Verify against a real export that includes fluid waste.
    keys : {base}_{i}_fluid waste kl
           {base}_{i}_fluid waste treatment type
           {base}_{i}_average inlet cod
           {base}_{i}_average outlet cod
           {base}_{i}_flared combusted fraction
    """
    out = []
    i = 0
    while (f"{base}_{i}_fluid waste kl" in flat
           or f"{base}_{i}_fluid waste treatment type" in flat):
        out.append({
            "fluidWasteKl": num(f"{base}_{i}_fluid waste kl"),
            "fluidWasteTreatmentType": text(f"{base}_{i}_fluid waste treatment type", "Managed Aerobic"),
            "averageInletCOD": num(f"{base}_{i}_average inlet cod"),
            "averageOutletCOD": num(f"{base}_{i}_average outlet cod"),
            "flaredCombustedFraction": num(f"{base}_{i}_flared combusted fraction"),
        })
        i += 1
    if not out:
        out.append({
            "fluidWasteKl": 0,
            "fluidWasteTreatmentType": "Managed Aerobic",
            "averageInletCOD": 0,
            "averageOutletCOD": 0,
            "flaredCombustedFraction": 0,
        })
    return out

# =========================
# BUILD PRODUCTS
# =========================
def build_products():
    products = []
    p = 0
    while f"products_{p}_id" in flat:
        pre = f"products_{p}_"
        products.append({
            "id": text(pre + "id"),
            "product": {
                "unit": text(pre + "product_unit"),
                "amountMadePerYear": num(pre + "product_amount made per year"),
            },
            # >>> FLAG: electricityRenewable — confirm the units the API expects
            #     (fraction 0-1 vs percent 0-100). Passed through as exported.
            "electricityRenewable": num(pre + "electricity renewable"),
            "electricityUse": num(pre + "electricity use"),
            "electricitySource": text(pre + "electricity source", "State Grid"),
            "fuel": {
                "transportFuel": build_fuel(pre + "fuel_transport fuel"),
                "stationaryFuel": build_fuel(pre + "fuel_stationary fuel"),
                "naturalGas": num(pre + "fuel_natural gas"),
            },
            "refrigerants": build_refrigerants(pre + "refrigerants"),
            "fluidWaste": build_fluid_waste(pre + "fluid waste"),
            "solidWaste": {
                "sentOffsiteTonnes": num(pre + "solid waste_sent offsite tonnes"),
                "onsiteCompostingTonnes": num(pre + "solid waste_onsite composting tonnes"),
            },
            "purchasedCO2": num(pre + "purchased co2"),
            "carbonOffsets": num(pre + "carbon offsets"),
        })
        p += 1
    return products

# =========================
# ASSEMBLE PAYLOAD
# =========================
# >>> FLAG: WA sub-region enums (wa_sw / wa_nw) remain unconfirmed. If a WA
#     export ever emits a sub-region code in "state", confirm the accepted
#     string with AIA before submitting.
payload = {
    "state": text("state"),
    "products": build_products(),
}

if not payload["products"]:
    print("WARNING: no products found in the CSV — nothing to submit.")

# =========================
# PREVIEW + POST
# =========================
print("=== Payload preview ===")
print(json.dumps(payload, indent=2))

resp = requests.post(
    API_URL,
    json=payload,
    headers={"Content-Type": "application/json"},
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("\n=== API response ===")
print("Status:", resp.status_code)
print(resp.text)