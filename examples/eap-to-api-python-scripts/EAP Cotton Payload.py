import pandas as pd
import requests
import json

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/cotton"
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
# BUILD CROPS
# Repeating array - never empty; default to a single zeroed entry.
# =========================
crops = []
i = 0
while f"crops_{i}_area sown" in flat:
    cprefix = f"crops_{i}_"
    crops.append({
        "id":                          s(cprefix + "id"),
        "state":                       s(cprefix + "state"),
        "averageCottonYield":          f(cprefix + "average cotton yield"),
        "areaSown":                    f(cprefix + "area sown"),
        "averageWeightPerBaleKg":      f(cprefix + "average weight per bale kg"),
        "cottonLintPerBaleKg":         f(cprefix + "cotton lint per bale kg"),
        "cottonSeedPerBaleKg":         f(cprefix + "cotton seed per bale kg"),
        "wastePerBaleKg":              f(cprefix + "waste per bale kg"),
        "ureaApplication":             f(cprefix + "urea application"),
        "otherFertiliserApplication":  f(cprefix + "other fertiliser application"),
        "nonUreaNitrogen":             f(cprefix + "non urea nitrogen"),
        "ureaAmmoniumNitrate":         f(cprefix + "urea ammonium nitrate"),
        "phosphorusApplication":       f(cprefix + "phosphorus application"),
        "potassiumApplication":        f(cprefix + "potassium application"),
        "sulfurApplication":           f(cprefix + "sulfur application"),
        "singleSuperPhosphate":        f(cprefix + "single super phosphate"),
        "rainfallAbove600":            b(cprefix + "rainfall above 600"),
        "herbicideUse":                f(cprefix + "herbicide use"),
        "glyphosateOtherHerbicideUse": f(cprefix + "glyphosate other herbicide use"),
        "electricityAllocation":       f(cprefix + "electricity allocation"),
        "limestone":                   f(cprefix + "limestone"),
        "limestoneFraction":           f(cprefix + "limestone fraction"),
        "dieselUse":                   f(cprefix + "diesel use"),
        "petrolUse":                   f(cprefix + "petrol use"),
        "lpg":                         f(cprefix + "lpg"),
    })
    i += 1

# Repeating arrays must never be empty - default to a single zeroed entry
if not crops:
    crops.append({
        "id":                          "",
        "state":                       s("state"),
        "averageCottonYield":          0.0,
        "areaSown":                    0.0,
        "averageWeightPerBaleKg":      0.0,
        "cottonLintPerBaleKg":         0.0,
        "cottonSeedPerBaleKg":         0.0,
        "wastePerBaleKg":              0.0,
        "ureaApplication":             0.0,
        "otherFertiliserApplication":  0.0,
        "nonUreaNitrogen":             0.0,
        "ureaAmmoniumNitrate":         0.0,
        "phosphorusApplication":       0.0,
        "potassiumApplication":        0.0,
        "sulfurApplication":           0.0,
        "singleSuperPhosphate":        0.0,
        "rainfallAbove600":            True,
        "herbicideUse":                0.0,
        "glyphosateOtherHerbicideUse": 0.0,
        "electricityAllocation":       0.0,
        "limestone":                   0.0,
        "limestoneFraction":           0.0,
        "dieselUse":                   0.0,
        "petrolUse":                   0.0,
        "lpg":                         0.0,
    })
    i = 1

# =========================
# BUILD VEGETATION
# Repeating array - never empty; default to a single zeroed entry.
# allocationToCrops carries one value per crop slot.
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
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW")
print("=" * 25)
print(json.dumps(payload, indent=2))
print("=" * 25)

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
