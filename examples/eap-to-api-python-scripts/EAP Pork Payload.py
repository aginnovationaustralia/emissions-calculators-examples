import json
import pandas as pd
import requests

# =========================
# CONFIG
# =========================
CSV_PATH = r"your file path here"
CERT_PATH = r"your file path here"
KEY_PATH = r"your file path here"
API_URL = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/pork"

# =========================
# LOAD FLAT CSV
# =========================
df = pd.read_csv(CSV_PATH)
flat = dict(zip(df["key"].astype(str).str.strip(), df["value"]))


# =========================
# SAFE VALUE HELPERS
# =========================
def f(key, default=0.0):
    """Float value for a flat key."""
    v = flat.get(key, default)
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return default
    try:
        return float(str(v).strip().strip('"'))
    except ValueError:
        return default


def b(key, default=False):
    """Boolean value for a flat key."""
    v = flat.get(key, default)
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    return str(v).strip().strip('"').lower() in ("true", "yes", "1", "y")


def s(key, default=""):
    """String value for a flat key."""
    v = flat.get(key, default)
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    return str(v).strip().strip('"')


def to_camel(label):
    """Convert a flat-CSV label ('whey powder') to an API key ('wheyPowder')."""
    parts = str(label).strip().split()
    if not parts:
        return ""
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


# =========================
# ENTERPRISE-SPECIFIC LOOKUPS
# =========================
# CSV class label -> API class key
PORK_CLASSES = {
    "sows": "sows",
    "boars": "boars",
    "gilts": "gilts",
    "suckers": "suckers",
    "weaners": "weaners",
    "growers": "growers",
    "slaughter pigs": "slaughterPigs",
}

SEASONS = ["spring", "summer", "autumn", "winter"]

DEFAULT_OTHER_FERTILISER = {
    "otherType": "Monoammonium phosphate (MAP)",
    "otherDryland": 0,
    "otherIrrigated": 0,
}

DEFAULT_VEGETATION = {
    "vegetation": {
        "region": "South West",
        "treeSpecies": "Mixed species (Environmental Plantings)",
        "soil": "Loams & Clays",
        "area": 0,
        "age": 0,
    },
    "allocatedProportion": [0],
}


# =========================
# BUILDERS
# =========================
def build_manure(prefix):
    """prefix = pork_{i}_classes_{cls}_manure"""
    manure = {}
    for season in SEASONS:
        manure[season] = {
            "outdoorSystems": f(f"{prefix}_{season}_outdoor systems"),
            "coveredAnaerobicPond": f(f"{prefix}_{season}_covered anaerobic pond"),
            "uncoveredAnaerobicPond": f(f"{prefix}_{season}_uncovered anaerobic pond"),
            "deepLitter": f(f"{prefix}_{season}_deep litter"),
            "undefinedSystem": f(f"{prefix}_{season}_undefined system"),
        }
    return manure


def build_purchases(prefix):
    """prefix = pork_{i}_classes_{cls}_purchases — never returns an empty array."""
    purchases = []
    k = 0
    while f"{prefix}_{k}_head" in flat or f"{prefix}_{k}_purchase weight" in flat:
        purchases.append(
            {
                "head": f(f"{prefix}_{k}_head"),
                "purchaseWeight": f(f"{prefix}_{k}_purchase weight"),
            }
        )
        k += 1
    if not purchases:
        purchases.append({"head": 0, "purchaseWeight": 0})
    return purchases


def build_class(prefix):
    """prefix = pork_{i}_classes_{cls}"""
    return {
        "autumn": f(f"{prefix}_autumn"),
        "winter": f(f"{prefix}_winter"),
        "spring": f(f"{prefix}_spring"),
        "summer": f(f"{prefix}_summer"),
        "headSold": f(f"{prefix}_head sold"),
        "saleWeight": f(f"{prefix}_sale weight"),
        "purchases": build_purchases(f"{prefix}_purchases"),
        "manure": build_manure(f"{prefix}_manure"),
    }


def build_fertiliser(prefix):
    """prefix = pork_{i}_fertiliser"""
    others = []
    k = 0
    while f"{prefix}_other fertilisers_{k}_other type" in flat:
        others.append(
            {
                "otherType": s(f"{prefix}_other fertilisers_{k}_other type"),
                "otherDryland": f(f"{prefix}_other fertilisers_{k}_other dryland"),
                "otherIrrigated": f(f"{prefix}_other fertilisers_{k}_other irrigated"),
            }
        )
        k += 1
    if not others:
        others.append(dict(DEFAULT_OTHER_FERTILISER))

    return {
        "singleSuperphosphate": f(f"{prefix}_single superphosphate"),
        "pastureDryland": f(f"{prefix}_pasture dryland"),
        "pastureIrrigated": f(f"{prefix}_pasture irrigated"),
        "cropsDryland": f(f"{prefix}_crops dryland"),
        "cropsIrrigated": f(f"{prefix}_crops irrigated"),
        "otherFertilisers": others,
    }


def build_ingredients(prefix):
    """prefix = pork_{i}_feed products_{j}_ingredients
    Ingredient names are read straight from the CSV keys, so any ingredient
    present in the export is carried through without needing a fixed list."""
    ingredients = {}
    for key in flat:
        if key.startswith(prefix + "_"):
            label = key[len(prefix) + 1:]
            ingredients[to_camel(label)] = f(key)
    return ingredients


def build_feed_products(prefix):
    """prefix = pork_{i}_feed products — never returns an empty array."""
    feed_products = []
    j = 0
    while f"{prefix}_{j}_feed purchased" in flat:
        feed_products.append(
            {
                "feedPurchased": f(f"{prefix}_{j}_feed purchased"),
                "additionalIngredients": f(f"{prefix}_{j}_additional ingredients"),
                "emissionsIntensity": f(f"{prefix}_{j}_emissions intensity"),
                "ingredients": build_ingredients(f"{prefix}_{j}_ingredients"),
            }
        )
        j += 1
    if not feed_products:
        feed_products.append(
            {
                "feedPurchased": 0,
                "additionalIngredients": 0,
                "emissionsIntensity": 0,
                "ingredients": {"wheat": 0},
            }
        )
    return feed_products


def build_pork(i):
    prefix = f"pork_{i}"
    return {
        "id": s(f"{prefix}_id"),
        "classes": {
            api_key: build_class(f"{prefix}_classes_{csv_label}")
            for csv_label, api_key in PORK_CLASSES.items()
        },
        "limestone": f(f"{prefix}_limestone"),
        "limestoneFraction": f(f"{prefix}_limestone fraction"),
        "fertiliser": build_fertiliser(f"{prefix}_fertiliser"),
        "diesel": f(f"{prefix}_diesel"),
        "petrol": f(f"{prefix}_petrol"),
        "lpg": f(f"{prefix}_lpg"),
        "electricitySource": s(f"{prefix}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{prefix}_electricity renewable"),
        "electricityUse": f(f"{prefix}_electricity use"),
        "herbicide": f(f"{prefix}_herbicide"),
        "herbicideOther": f(f"{prefix}_herbicide other"),
        "beddingHayBarleyStraw": f(f"{prefix}_bedding hay barley straw"),
        "feedProducts": build_feed_products(f"{prefix}_feed products"),
    }


def build_vegetation():
    """Never returns an empty array."""
    vegetation = []
    i = 0
    while f"vegetation_{i}_vegetation_region" in flat:
        prefix = f"vegetation_{i}"

        proportions = []
        k = 0
        while f"{prefix}_allocated proportion_{k}" in flat:
            proportions.append(f(f"{prefix}_allocated proportion_{k}"))
            k += 1
        if not proportions:
            proportions = [0]

        vegetation.append(
            {
                "vegetation": {
                    "region": s(f"{prefix}_vegetation_region", "South West"),
                    "treeSpecies": s(
                        f"{prefix}_vegetation_tree species",
                        "Mixed species (Environmental Plantings)",
                    ),
                    "soil": s(f"{prefix}_vegetation_soil", "Loams & Clays"),
                    "area": f(f"{prefix}_vegetation_area"),
                    "age": f(f"{prefix}_vegetation_age"),
                },
                "allocatedProportion": proportions,
            }
        )
        i += 1

    if not vegetation:
        vegetation.append(json.loads(json.dumps(DEFAULT_VEGETATION)))
    return vegetation


# =========================
# BUILD PAYLOAD
# =========================
pork_entries = []
i = 0
while f"pork_{i}_id" in flat:
    pork_entries.append(build_pork(i))
    i += 1

payload = {
    "id": s("id"),
    "state": s("state"),
    "rainfallAbove600": b("rainfall above 600"),
    "pork": pork_entries,
    "vegetation": build_vegetation(),
}

# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW")
print("=" * 25)
print(json.dumps(payload, indent=2))
print("=" * 25)
print(f"Pork enterprises: {len(pork_entries)}")
print(f"Vegetation entries: {len(payload['vegetation'])}")
print("=" * 25)

# =========================
# POST TO API
# =========================
headers = {"Content-Type": "application/json"}

response = requests.post(
    API_URL,
    headers=headers,
    json=payload,
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("=" * 25)
print("API RESPONSE")
print("=" * 25)
print(f"Status code: {response.status_code}")
print(response.text)
