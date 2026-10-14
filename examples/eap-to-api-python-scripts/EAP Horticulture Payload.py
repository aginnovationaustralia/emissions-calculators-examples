import pandas as pd
import requests
import json

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/horticulture"
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

def b(key):
    val = flat.get(key, "false")
    return str(val).strip().lower() in ["true", "yes", "1"]

def s(key, default=""):
    return str(flat.get(key, default)).strip().strip('"')

# =========================
# BUILD REFRIGERANTS (per crop)
# Repeating array - never empty; default to a single zeroed entry.
# =========================
def build_refrigerants(crop_prefix):
    refrigerants = []
    r = 0
    while (crop_prefix + f"refrigerants_{r}_refrigerant") in flat:
        rprefix = crop_prefix + f"refrigerants_{r}_"
        refrigerants.append({
            "refrigerant": s(rprefix + "refrigerant"),
            "chargeSize":  f(rprefix + "charge size"),
        })
        r += 1
    if not refrigerants:
        refrigerants.append({
            "refrigerant": "HFC-23",
            "chargeSize":  0.0,
        })
    return refrigerants

# =========================
# BUILD CROPS LIST
# =========================
crops = []
i = 0
while f"crops_{i}_area sown" in flat:
    prefix = f"crops_{i}_"
    crops.append({
        "id":                        s(prefix + "id"),
        "type":                      s(prefix + "type"),
        "averageYield":              f(prefix + "average yield"),
        "areaSown":                  f(prefix + "area sown"),
        "ureaApplication":           f(prefix + "urea application"),
        "nonUreaNitrogen":           f(prefix + "non urea nitrogen"),
        "ureaAmmoniumNitrate":       f(prefix + "urea ammonium nitrate"),
        "phosphorusApplication":     f(prefix + "phosphorus application"),
        "potassiumApplication":      f(prefix + "potassium application"),
        "sulfurApplication":         f(prefix + "sulfur application"),
        "rainfallAbove600":          b(prefix + "rainfall above 600"),
        "fractionOfAnnualCropBurnt": f(prefix + "fraction of annual crop burnt"),
        "herbicideUse":              f(prefix + "herbicide use"),
        "glyphosateOtherHerbicideUse": f(prefix + "glyphosate other herbicide use"),
        "electricityAllocation":     f(prefix + "electricity allocation"),
        "limestone":                 f(prefix + "limestone"),
        "limestoneFraction":         f(prefix + "limestone fraction"),
        "dieselUse":                 f(prefix + "diesel use"),
        "petrolUse":                 f(prefix + "petrol use"),
        "lpg":                       f(prefix + "lpg"),
        "refrigerants":              build_refrigerants(prefix),
    })
    i += 1

# =========================
# BUILD VEGETATION LIST
# allocationToCrops has one entry per crop, in crop order.
# =========================
vegetation = []
j = 0
while f"vegetation_{j}_vegetation_area" in flat:
    vprefix = f"vegetation_{j}_"
    allocs = []
    for k in range(i):
        alloc_key = f"vegetation_{j}_allocation to crops_{k}"
        allocs.append(f(alloc_key))
    vegetation.append({
        "id": s(vprefix + "id"),
        "vegetation": {
            "region":      s(vprefix + "vegetation_region"),
            "treeSpecies": s(vprefix + "vegetation_tree species"),
            "soil":        s(vprefix + "vegetation_soil"),
            "area":        f(vprefix + "vegetation_area"),
            "age":         f(vprefix + "vegetation_age"),
        },
        "allocationToCrops": allocs,
    })
    j += 1

# Repeating arrays must never be empty - default to a single zeroed entry
if not vegetation:
    vegetation.append({
        "id": "",
        "vegetation": {
            "region":      "South West",
            "treeSpecies": "Mixed species (Environmental Plantings)",
            "soil":        "Loams & Clays",
            "area":        0.0,
            "age":         0.0,
        },
        "allocationToCrops": [0.0] * max(i, 1),
    })

# =========================
# BUILD FULL PAYLOAD
# =========================
payload = {
    "id":                   "",
    "state":                s("state"),
    "crops":                crops,
    "electricityRenewable": f("electricity renewable"),
    "electricityUse":       f("electricity use"),
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
    headers=headers,
    data=json.dumps(payload),
    cert=(CERT_FILE, KEY_FILE),
    verify=True,
)

print("\n=== API RESPONSE ===")
print("Status:", response.status_code)
print(response.text)
