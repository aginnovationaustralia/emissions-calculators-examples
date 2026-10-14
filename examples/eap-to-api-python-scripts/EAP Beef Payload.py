import pandas as pd
import requests
import json

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/beef"
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

SEASONS = ["autumn", "winter", "spring", "summer"]

# =========================
# BUILD A SEASONAL CLASS BLOCK
# e.g. beef_0_classes_bulls gt1_autumn_head
# =========================
def build_class(prefix, class_name):
    block = {}
    for season in SEASONS:
        cprefix = f"{prefix}classes_{class_name}_{season}_"
        block[season] = {
            "head":                   f(cprefix + "head"),
            "liveweight":             f(cprefix + "liveweight"),
            "liveweightGain":         f(cprefix + "liveweight gain", default=1.0),
            "crudeProtein":           f(cprefix + "crude protein"),
            "dryMatterDigestibility": f(cprefix + "dry matter digestibility"),
        }
    block["headSold"]   = f(f"{prefix}classes_{class_name}_head sold")
    block["saleWeight"] = f(f"{prefix}classes_{class_name}_sale weight")
    block["purchases"]  = build_purchases(prefix, class_name)
    return block

# =========================
# BUILD PURCHASES LIST FOR A CLASS (optional, repeating block)
# e.g. beef_0_classes_bulls gt1_purchases_0_head / purchase weight / purchase source
# Defaults to a single empty entry matching the API sample if none present in CSV
# =========================
def build_purchases(prefix, class_name):
    purchases = []
    k = 0
    while f"{prefix}classes_{class_name}_purchases_{k}_head" in flat:
        pprefix = f"{prefix}classes_{class_name}_purchases_{k}_"
        purchases.append({
            "head":           f(pprefix + "head"),
            "purchaseWeight": f(pprefix + "purchase weight"),
            "purchaseSource": s(pprefix + "purchase source", "Dairy origin"),
        })
        k += 1
    if not purchases:
        purchases.append({
            "head":           0,
            "purchaseWeight": 0,
            "purchaseSource": "Dairy origin",
        })
    return purchases

# =========================
# BUILD OTHER FERTILISERS LIST (optional, repeating block)
# e.g. beef_0_fertiliser_other fertilisers_0_other type / other dryland / other irrigated
# Defaults to a single empty entry matching the API sample if none present in CSV
# =========================
def build_other_fertilisers(prefix):
    others = []
    k = 0
    while f"{prefix}fertiliser_other fertilisers_{k}_other type" in flat:
        oprefix = f"{prefix}fertiliser_other fertilisers_{k}_"
        others.append({
            "otherType":      s(oprefix + "other type", "Monoammonium phosphate (MAP)"),
            "otherDryland":   f(oprefix + "other dryland"),
            "otherIrrigated": f(oprefix + "other irrigated"),
        })
        k += 1
    if not others:
        others.append({
            "otherType":      "Monoammonium phosphate (MAP)",
            "otherDryland":   0,
            "otherIrrigated": 0,
        })
    return others

# =========================
# BUILD COWS CALVING BLOCK
# e.g. beef_0_cows calving_autumn
# =========================
def build_cows_calving(prefix):
    cprefix = f"{prefix}cows calving_"
    return {season: f(cprefix + season) for season in SEASONS}

# =========================
# BUILD MINERAL SUPPLEMENTATION BLOCK
# e.g. beef_0_mineral supplementation_mineral block
# =========================
def build_mineral_supplementation(prefix):
    mprefix = f"{prefix}mineral supplementation_"
    return {
        "mineralBlock":      f(mprefix + "mineral block"),
        "mineralBlockUrea":  f(mprefix + "mineral block urea"),
        "weanerBlock":       f(mprefix + "weaner block"),
        "weanerBlockUrea":   f(mprefix + "weaner block urea"),
        "drySeasonMix":      f(mprefix + "dry season mix"),
        "drySeasonMixUrea":  f(mprefix + "dry season mix urea"),
    }

# =========================
# BUILD BEEF LIST
# (CSV currently only ever has a single beef_0_ block, but loop is kept
#  generic in case multiple blocks are ever supplied)
# =========================
beef = []
i = 0
while f"beef_{i}_id" in flat:
    prefix = f"beef_{i}_"

    beef.append({
        "id": s(prefix + "id"),
        "classes": {
            "bullsGt1":          build_class(prefix, "bulls gt1"),
            "bullsGt1Traded":    build_class(prefix, "bulls gt1 traded"),
            "steersLt1":         build_class(prefix, "steers lt1"),
            "steersLt1Traded":   build_class(prefix, "steers lt1 traded"),
            "steers1To2":        build_class(prefix, "steers1 to2"),
            "steers1To2Traded":  build_class(prefix, "steers1 to2 traded"),
            "steersGt2":         build_class(prefix, "steers gt2"),
            "steersGt2Traded":   build_class(prefix, "steers gt2 traded"),
            "cowsGt2":           build_class(prefix, "cows gt2"),
            "cowsGt2Traded":     build_class(prefix, "cows gt2 traded"),
            "heifersLt1":        build_class(prefix, "heifers lt1"),
            "heifersLt1Traded":  build_class(prefix, "heifers lt1 traded"),
            "heifers1To2":       build_class(prefix, "heifers1 to2"),
            "heifers1To2Traded": build_class(prefix, "heifers1 to2 traded"),
            "heifersGt2":        build_class(prefix, "heifers gt2"),
            "heifersGt2Traded":  build_class(prefix, "heifers gt2 traded"),
        },
        "limestone":         f(prefix + "limestone"),
        "limestoneFraction": f(prefix + "limestone fraction"),
        "fertiliser": {
            "singleSuperphosphate": f(prefix + "fertiliser_single superphosphate"),
            "pastureDryland":       f(prefix + "fertiliser_pasture dryland"),
            "pastureIrrigated":     f(prefix + "fertiliser_pasture irrigated"),
            "cropsDryland":         f(prefix + "fertiliser_crops dryland"),
            "cropsIrrigated":       f(prefix + "fertiliser_crops irrigated"),
            "otherFertilisers":     build_other_fertilisers(prefix),
        },
        "diesel":               f(prefix + "diesel"),
        "petrol":                f(prefix + "petrol"),
        "lpg":                   f(prefix + "lpg"),
        "electricitySource":     s(prefix + "electricity source", "State Grid"),
        "electricityRenewable":  f(prefix + "electricity renewable"),
        "electricityUse":        f(prefix + "electricity use"),
        "grainFeed":             f(prefix + "grain feed"),
        "hayFeed":               f(prefix + "hay feed"),
        "cottonseedFeed":        f(prefix + "cottonseed feed"),
        "herbicide":             f(prefix + "herbicide"),
        "herbicideOther":        f(prefix + "herbicide other"),
        "mineralSupplementation": build_mineral_supplementation(prefix),
        "cowsCalving":           build_cows_calving(prefix),
    })
    i += 1

# =========================
# BUILD BURNING LIST
# e.g. burning_0_fuel, burning_0_allocation to beef_0
# (CSV currently has none defined beyond burning_0 — list stays empty if no rows present)
# =========================
burning = []
j = 0
while f"burning_{j}_fuel" in flat:
    bprefix = f"burning_{j}_"
    allocations = []
    k = 0
    while f"burning_{j}_allocation to beef_{k}" in flat:
        allocations.append(f(f"burning_{j}_allocation to beef_{k}"))
        k += 1
    if not allocations:
        allocations = [0]
    burning.append({
        "burning": {
            "fuel":              s(bprefix + "fuel"),
            "season":            s(bprefix + "season"),
            "patchiness":        s(bprefix + "patchiness"),
            "rainfallZone":      s(bprefix + "rainfall zone"),
            "yearsSinceLastFire": f(bprefix + "years since last fire"),
            "fireScarArea":      f(bprefix + "fire scar area"),
            "vegetation":        s(bprefix + "vegetation"),
        },
        "allocationToBeef": allocations,
    })
    j += 1

# =========================
# BUILD VEGETATION LIST
# e.g. vegetation_0_vegetation_area, vegetation_0_beef proportion_0
# (CSV currently has none — list stays empty if no rows present)
# =========================
vegetation = []
m = 0
while f"vegetation_{m}_vegetation_area" in flat:
    vprefix = f"vegetation_{m}_"
    proportions = []
    k = 0
    while f"vegetation_{m}_beef proportion_{k}" in flat:
        proportions.append(f(f"vegetation_{m}_beef proportion_{k}"))
        k += 1
    if not proportions:
        proportions = [0]
    vegetation.append({
        "vegetation": {
            "region":      s(vprefix + "vegetation_region"),
            "treeSpecies": s(vprefix + "vegetation_tree species"),
            "soil":        s(vprefix + "vegetation_soil"),
            "area":        f(vprefix + "vegetation_area"),
            "age":         f(vprefix + "vegetation_age"),
        },
        "allocationToBeef": proportions,
    })
    m += 1

# =========================
# BUILD FULL PAYLOAD
# =========================
payload = {
    "state":                      s("state"),
    "northOfTropicOfCapricorn":   b("north of tropic of capricorn"),
    "rainfallAbove600":           b("rainfall above 600"),
    "beef":                       beef,
    "burning":                    burning,
    "vegetation":                 vegetation,
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