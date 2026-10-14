import pandas as pd
import json
import requests

# =========================
# CONFIG
# =========================
CSV_FILE  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/sheep"
CERT_FILE = r"your file path here"
KEY_FILE  = r"your file path here"

# =========================
# LOAD CSV INTO FLAT DICT
# =========================
df = pd.read_csv(CSV_FILE)
flat = dict(zip(df["key"].astype(str), df["value"]))

# NOTE: the SB-GAF export also contains beef_*, crops_* and burning_* rows.
# The 3.0.2/sheep schema has no top-level keys for these, so they are
# ignored here (same as sheep rows were ignored by the beef script).

# =========================
# SAFE VALUE HELPERS
# =========================
def f(key, default=0):
    """Float value from flat dict, with fallback default."""
    try:
        v = flat.get(key, default)
        if pd.isna(v):
            return default
        return float(v)
    except (ValueError, TypeError):
        return default

def b(key, default=False):
    """Boolean value from flat dict, with fallback default."""
    v = str(flat.get(key, default)).strip().lower()
    return v in ("true", "yes", "1", "1.0")

def s(key, default=""):
    """String value from flat dict, with fallback default."""
    v = flat.get(key, default)
    if pd.isna(v):
        return default
    v = str(v).strip()
    return v if v else default

# =========================
# SHEEP CLASS NAME MAPPING
# =========================
# API field name -> CSV label (order matches the API schema)
SHEEP_CLASSES = {
    "rams":                    "rams",
    "tradeRams":               "trade rams",
    "wethers":                 "wethers",
    "tradeWethers":            "trade wethers",
    "maidenBreedingEwes":      "maiden breeding ewes",
    "tradeMaidenBreedingEwes": "trade maiden breeding ewes",
    "breedingEwes":            "breeding ewes",
    "tradeBreedingEwes":       "trade breeding ewes",
    "otherEwes":               "other ewes",
    "tradeOtherEwes":          "trade other ewes",
    "eweLambs":                "ewe lambs",
    "tradeEweLambs":           "trade ewe lambs",
    "wetherLambs":             "wether lambs",
    "tradeWetherLambs":        "trade wether lambs",
}

# =========================
# BUILDER FUNCTIONS
# =========================
def build_season(prefix):
    # "feed availability" does not exist in the SB-GAF seasonal export
    # (CP/DMD method is used instead), so feedAvailability falls back to 0.
    return {
        "head": f(f"{prefix}_head"),
        "liveweight": f(f"{prefix}_liveweight"),
        "liveweightGain": f(f"{prefix}_liveweight gain"),
        "crudeProtein": f(f"{prefix}_crude protein"),
        "dryMatterDigestibility": f(f"{prefix}_dry matter digestibility"),
        "feedAvailability": f(f"{prefix}_feed availability"),
    }

def build_purchases(prefix):
    # Purchases rows only exist for some classes, and for different classes
    # in each enterprise, so they are detected dynamically per class.
    purchases = []
    j = 0
    while f"{prefix}_purchases_{j}_head" in flat:
        purchases.append({
            "head": f(f"{prefix}_purchases_{j}_head"),
            "purchaseWeight": f(f"{prefix}_purchases_{j}_purchase weight"),
        })
        j += 1
    if not purchases:
        purchases = [{"head": 0, "purchaseWeight": 0}]
    return purchases

def build_class(prefix):
    return {
        "autumn": build_season(f"{prefix}_autumn"),
        "winter": build_season(f"{prefix}_winter"),
        "spring": build_season(f"{prefix}_spring"),
        "summer": build_season(f"{prefix}_summer"),
        "headShorn": f(f"{prefix}_head shorn"),
        "woolShorn": f(f"{prefix}_wool shorn"),
        "cleanWoolYield": f(f"{prefix}_clean wool yield"),
        "headSold": f(f"{prefix}_head sold"),
        "saleWeight": f(f"{prefix}_sale weight"),
        "purchases": build_purchases(prefix),
    }

def build_other_fertilisers(prefix):
    others = []
    j = 0
    while f"{prefix}_other fertilisers_{j}_other type" in flat:
        others.append({
            "otherType": s(f"{prefix}_other fertilisers_{j}_other type", "Monoammonium phosphate (MAP)"),
            "otherDryland": f(f"{prefix}_other fertilisers_{j}_other dryland"),
            "otherIrrigated": f(f"{prefix}_other fertilisers_{j}_other irrigated"),
        })
        j += 1
    if not others:
        others = [{
            "otherType": "Monoammonium phosphate (MAP)",
            "otherDryland": 0,
            "otherIrrigated": 0,
        }]
    return others

def build_sheep(i):
    p = f"sheep_{i}"
    classes = {}
    for api_name, csv_label in SHEEP_CLASSES.items():
        classes[api_name] = build_class(f"{p}_classes_{csv_label}")
    return {
        "id": s(f"{p}_id"),
        "classes": classes,
        "limestone": f(f"{p}_limestone"),
        "limestoneFraction": f(f"{p}_limestone fraction"),
        "fertiliser": {
            "singleSuperphosphate": f(f"{p}_fertiliser_single superphosphate"),
            "pastureDryland": f(f"{p}_fertiliser_pasture dryland"),
            "pastureIrrigated": f(f"{p}_fertiliser_pasture irrigated"),
            "cropsDryland": f(f"{p}_fertiliser_crops dryland"),
            "cropsIrrigated": f(f"{p}_fertiliser_crops irrigated"),
            "otherFertilisers": build_other_fertilisers(f"{p}_fertiliser"),
        },
        "diesel": f(f"{p}_diesel"),
        "petrol": f(f"{p}_petrol"),
        "lpg": f(f"{p}_lpg"),
        "mineralSupplementation": {
            "mineralBlock": f(f"{p}_mineral supplementation_mineral block"),
            "mineralBlockUrea": f(f"{p}_mineral supplementation_mineral block urea"),
            "weanerBlock": f(f"{p}_mineral supplementation_weaner block"),
            "weanerBlockUrea": f(f"{p}_mineral supplementation_weaner block urea"),
            "drySeasonMix": f(f"{p}_mineral supplementation_dry season mix"),
            "drySeasonMixUrea": f(f"{p}_mineral supplementation_dry season mix urea"),
        },
        "electricitySource": s(f"{p}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{p}_electricity renewable"),
        "electricityUse": f(f"{p}_electricity use"),
        "grainFeed": f(f"{p}_grain feed"),
        "hayFeed": f(f"{p}_hay feed"),
        "herbicide": f(f"{p}_herbicide"),
        "herbicideOther": f(f"{p}_herbicide other"),
        "merinoPercent": f(f"{p}_merino percent"),
        "ewesLambing": {
            "spring": f(f"{p}_ewes lambing_spring"),
            "summer": f(f"{p}_ewes lambing_summer"),
            "autumn": f(f"{p}_ewes lambing_autumn"),
            "winter": f(f"{p}_ewes lambing_winter"),
        },
        "seasonalLambing": {
            "autumn": f(f"{p}_seasonal lambing_autumn"),
            "winter": f(f"{p}_seasonal lambing_winter"),
            "spring": f(f"{p}_seasonal lambing_spring"),
            "summer": f(f"{p}_seasonal lambing_summer"),
        },
    }

def build_sheep_proportion(k):
    # One proportion entry per sheep enterprise (e.g. sheep proportion_0,
    # sheep proportion_1). The sheep schema has no beefProportion or
    # allocation-to-crops keys, so those CSV rows are ignored.
    props = []
    j = 0
    while f"vegetation_{k}_sheep proportion_{j}" in flat:
        props.append(f(f"vegetation_{k}_sheep proportion_{j}"))
        j += 1
    if not props:
        props = [0]
    return props

def build_vegetation(k):
    p = f"vegetation_{k}_vegetation"
    return {
        "vegetation": {
            "region": s(f"{p}_region", "South West"),
            "treeSpecies": s(f"{p}_tree species", "Mixed species (Environmental Plantings)"),
            "soil": s(f"{p}_soil", "Loams & Clays"),
            "area": f(f"{p}_area"),
            "age": f(f"{p}_age"),
        },
        "sheepProportion": build_sheep_proportion(k),
    }

# =========================
# BUILD PAYLOAD
# =========================
sheep = []
i = 0
while f"sheep_{i}_id" in flat:
    sheep.append(build_sheep(i))
    i += 1
if not sheep:
    sheep = [build_sheep(0)]  # fully zeroed default enterprise — never send an empty array

vegetation = []
k = 0
while f"vegetation_{k}_vegetation_region" in flat:
    vegetation.append(build_vegetation(k))
    k += 1
if not vegetation:
    vegetation = [{
        "vegetation": {
            "region": "South West",
            "treeSpecies": "Mixed species (Environmental Plantings)",
            "soil": "Loams & Clays",
            "area": 0,
            "age": 0,
        },
        "sheepProportion": [0],
    }]

payload = {
    "state": s("state", "nsw"),
    "northOfTropicOfCapricorn": b("north of tropic of capricorn"),
    "rainfallAbove600": b("rainfall above 600"),
    "sheep": sheep,
    "vegetation": vegetation,
}

# =========================
# PAYLOAD PREVIEW
# =========================
print("=== PAYLOAD PREVIEW ===")
print(json.dumps(payload, indent=2))

# =========================
# SEND TO API
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
