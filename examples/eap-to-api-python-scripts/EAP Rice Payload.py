import pandas as pd
import requests
import json

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/rice"
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
# BUILD CROPS LIST
# =========================
crops = []
i = 0
while f"crops_{i}_area sown" in flat:
    prefix = f"crops_{i}_"
    crops.append({
        "id":                          s(prefix + "id"),
        "state":                       s(prefix + "state"),
        "averageRiceYield":            f(prefix + "average rice yield"),
        "areaSown":                    f(prefix + "area sown"),
        "growingSeasonDays":           f(prefix + "growing season days"),
        "waterRegimeType":             s(prefix + "water regime type"),
        "waterRegimeSubType":          s(prefix + "water regime sub type"),
        "ricePreseasonFloodingPeriod": s(prefix + "rice preseason flooding period"),
        "ureaApplication":             f(prefix + "urea application"),
        "nonUreaNitrogen":             f(prefix + "non urea nitrogen"),
        "ureaAmmoniumNitrate":         f(prefix + "urea ammonium nitrate"),
        "phosphorusApplication":       f(prefix + "phosphorus application"),
        "potassiumApplication":        f(prefix + "potassium application"),
        "sulfurApplication":           f(prefix + "sulfur application"),
        "fractionOfAnnualCropBurnt":   f(prefix + "fraction of annual crop burnt"),
        "herbicideUse":                f(prefix + "herbicide use"),
        "glyphosateOtherHerbicideUse": f(prefix + "glyphosate other herbicide use"),
        "electricityAllocation":       f(prefix + "electricity allocation"),
        "limestone":                   f(prefix + "limestone"),
        "limestoneFraction":           f(prefix + "limestone fraction"),
        "dieselUse":                   f(prefix + "diesel use"),
        "petrolUse":                   f(prefix + "petrol use"),
        "lpg":                         f(prefix + "lpg"),
    })
    i += 1

# =========================
# BUILD VEGETATION LIST
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
        "vegetation": {
            "age":         f(vprefix + "vegetation_age"),
            "area":        f(vprefix + "vegetation_area"),
            "region":      s(vprefix + "vegetation_region"),
            "soil":        s(vprefix + "vegetation_soil"),
            "treeSpecies": s(vprefix + "vegetation_tree species"),
        },
        "allocationToCrops": allocs,
    })
    j += 1

# Repeating arrays must never be empty - default to a single zeroed entry
if not vegetation:
    vegetation.append({
        "vegetation": {
            "age":         0.0,
            "area":        0.0,
            "region":      "South West",
            "soil":        "Loams & Clays",
            "treeSpecies": "Mixed species (Environmental Plantings)",
        },
        "allocationToCrops": [0.0] * max(i, 1),
    })

# =========================
# BUILD FULL PAYLOAD
# =========================
payload = {
    "state":               s("state"),
    "electricityUse":      f("electricity use"),
    "electricityRenewable":f("electricity renewable"),
    "crops":               crops,
    "vegetation":          vegetation,
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