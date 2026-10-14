import pandas as pd
import requests
import json

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/aquaculture"
CERT_FILE = r"your file path here"
KEY_FILE  = r"your file path here"

# =========================
# LOAD CSV INTO A FLAT DICT
# =========================
df = pd.read_csv(CSV_FILE, header=0)
flat = dict(zip(df["key"], df["value"]))

# =========================
# SAFE VALUE HELPERS
# =========================
def f(key, default=0.0):
    val = flat.get(key, default)
    try:
        return float(val)
    except:
        return default

def b(key, default=False):
    val = flat.get(key, "false" if not default else "true")
    return str(val).strip().lower() in ["true", "yes", "1"]

def s(key, default=""):
    return str(flat.get(key, default)).strip().strip('"')

# =========================
# BUILD REFRIGERANTS LIST (optional, repeating block)
# e.g. enterprises_0_refrigerants_0_refrigerant / charge size
# Defaults to a single empty entry matching the API sample if none present in CSV
# =========================
def build_refrigerants(prefix):
    items = []
    k = 0
    while f"{prefix}refrigerants_{k}_refrigerant" in flat:
        rprefix = f"{prefix}refrigerants_{k}_"
        items.append({
            "refrigerant": s(rprefix + "refrigerant", "HFC-23"),
            "chargeSize":  f(rprefix + "charge size"),
        })
        k += 1
    if not items:
        items.append({"refrigerant": "HFC-23", "chargeSize": 0})
    return items

# =========================
# BUILD BAIT LIST (optional, repeating block)
# e.g. enterprises_0_bait_0_type / purchased tonnes / additional ingredients / emissions intensity
# =========================
def build_bait(prefix):
    items = []
    k = 0
    while f"{prefix}bait_{k}_type" in flat:
        bprefix = f"{prefix}bait_{k}_"
        items.append({
            "type":                  s(bprefix + "type", "Whole Sardines"),
            "purchasedTonnes":       f(bprefix + "purchased tonnes"),
            "additionalIngredients": f(bprefix + "additional ingredients"),
            "emissionsIntensity":    f(bprefix + "emissions intensity"),
        })
        k += 1
    if not items:
        items.append({
            "type": "Whole Sardines",
            "purchasedTonnes": 0,
            "additionalIngredients": 0,
            "emissionsIntensity": 0,
        })
    return items

# =========================
# BUILD CUSTOM BAIT LIST (optional, repeating block)
# e.g. enterprises_0_custom bait_0_purchased tonnes / emissions intensity
# =========================
def build_custom_bait(prefix):
    items = []
    k = 0
    while f"{prefix}custom bait_{k}_purchased tonnes" in flat:
        cprefix = f"{prefix}custom bait_{k}_"
        items.append({
            "purchasedTonnes":    f(cprefix + "purchased tonnes"),
            "emissionsIntensity": f(cprefix + "emissions intensity"),
        })
        k += 1
    if not items:
        items.append({"purchasedTonnes": 0, "emissionsIntensity": 0})
    return items

# =========================
# BUILD FREIGHT LIST (optional, repeating block) — shared by inbound/outbound
# e.g. enterprises_0_inbound freight_0_type / total km tonnes
#      enterprises_0_outbound freight_0_type / total km tonnes
# =========================
def build_freight(prefix, direction):
    items = []
    k = 0
    while f"{prefix}{direction} freight_{k}_type" in flat:
        fprefix = f"{prefix}{direction} freight_{k}_"
        items.append({
            "type":          s(fprefix + "type", "Truck"),
            "totalKmTonnes": f(fprefix + "total km tonnes"),
        })
        k += 1
    if not items:
        items.append({"type": "Truck", "totalKmTonnes": 0})
    return items

# =========================
# BUILD FLUID WASTE LIST (optional, repeating block)
# e.g. enterprises_0_fluid waste_0_fluid waste kl / fluid waste treatment type /
#      average inlet cod / average outlet cod / flared combusted fraction
# =========================
def build_fluid_waste(prefix):
    items = []
    k = 0
    while f"{prefix}fluid waste_{k}_fluid waste kl" in flat:
        wprefix = f"{prefix}fluid waste_{k}_"
        items.append({
            "fluidWasteKl":            f(wprefix + "fluid waste kl"),
            "fluidWasteTreatmentType": s(wprefix + "fluid waste treatment type", "Managed Aerobic"),
            "averageInletCOD":         f(wprefix + "average inlet cod"),
            "averageOutletCOD":        f(wprefix + "average outlet cod"),
            "flaredCombustedFraction": f(wprefix + "flared combusted fraction"),
        })
        k += 1
    if not items:
        items.append({
            "fluidWasteKl": 0,
            "fluidWasteTreatmentType": "Managed Aerobic",
            "averageInletCOD": 0,
            "averageOutletCOD": 0,
            "flaredCombustedFraction": 0,
        })
    return items

# =========================
# BUILD FUEL BLOCK
# e.g. enterprises_0_fuel_transport fuel_0_type / amount litres
#      enterprises_0_fuel_stationary fuel_0_type / amount litres
#      enterprises_0_fuel_natural gas
# =========================
def build_fuel(prefix):
    fprefix = f"{prefix}fuel_"

    transport_fuel = []
    k = 0
    while f"{fprefix}transport fuel_{k}_type" in flat:
        tprefix = f"{fprefix}transport fuel_{k}_"
        transport_fuel.append({
            "type":         s(tprefix + "type", "petrol"),
            "amountLitres": f(tprefix + "amount litres"),
        })
        k += 1
    if not transport_fuel:
        transport_fuel.append({"type": "petrol", "amountLitres": 0})

    stationary_fuel = []
    k = 0
    while f"{fprefix}stationary fuel_{k}_type" in flat:
        sprefix = f"{fprefix}stationary fuel_{k}_"
        stationary_fuel.append({
            "type":         s(sprefix + "type", "petrol"),
            "amountLitres": f(sprefix + "amount litres"),
        })
        k += 1
    if not stationary_fuel:
        stationary_fuel.append({"type": "petrol", "amountLitres": 0})

    return {
        "transportFuel":  transport_fuel,
        "stationaryFuel": stationary_fuel,
        "naturalGas":     f(fprefix + "natural gas"),
    }

# =========================
# BUILD SOLID WASTE BLOCK
# e.g. enterprises_0_solid waste_sent offsite tonnes / onsite composting tonnes
# =========================
def build_solid_waste(prefix):
    wprefix = f"{prefix}solid waste_"
    return {
        "sentOffsiteTonnes":      f(wprefix + "sent offsite tonnes"),
        "onsiteCompostingTonnes": f(wprefix + "onsite composting tonnes"),
    }

# =========================
# BUILD ENTERPRISES LIST
# =========================
enterprises = []
i = 0
while f"enterprises_{i}_id" in flat:
    prefix = f"enterprises_{i}_"

    enterprises.append({
        "id":                       s(prefix + "id"),
        "state":                    s(prefix + "state"),
        "productionSystem":         s(prefix + "production system"),
        "totalHarvestKg":           f(prefix + "total harvest kg"),
        "refrigerants":             build_refrigerants(prefix),
        "bait":                     build_bait(prefix),
        "customBait":               build_custom_bait(prefix),
        "inboundFreight":           build_freight(prefix, "inbound"),
        "outboundFreight":          build_freight(prefix, "outbound"),
        "totalCommercialFlightsKm": f(prefix + "total commercial flights km"),
        "electricityRenewable":     f(prefix + "electricity renewable"),
        "electricityUse":           f(prefix + "electricity use"),
        "electricitySource":        s(prefix + "electricity source", "State Grid"),
        "fuel":                     build_fuel(prefix),
        "fluidWaste":               build_fluid_waste(prefix),
        "solidWaste":               build_solid_waste(prefix),
        "carbonOffsets":            f(prefix + "carbon offsets"),
    })
    i += 1

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