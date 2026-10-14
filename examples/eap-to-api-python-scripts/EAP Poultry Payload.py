import json
import pandas as pd
import requests

# =========================
# CONFIG
# =========================
CSV_PATH  = r"your file path here"
CERT_PATH = r"your file path here"
KEY_PATH  = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/poultry"

# -------------------------------------------------------------------------
# NOTE: The sample poultry CSV supplied was a MEAT export and contained no
# layers_* keys. The LAYER flat-key names below are inferred from the API
# schema and the broiler CSV's naming convention. Verify them against a real
# combined / eggs EAP export before relying on the layer half in production -
# especially the seasonal flock keys and egg-sale sub-keys (>>> VERIFY in-code).
# The BROILER keys are taken directly from the supplied meat CSV.
# -------------------------------------------------------------------------

# =========================
# LOAD FLAT CSV
# =========================
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
flat = dict(zip(df["key"].str.strip(), df["value"]))


# =========================
# SAFE-VALUE HELPERS
# =========================
def f(key, default=0.0):
    """Float value, defaulting when key is missing or blank."""
    v = flat.get(key, "")
    if v is None or str(v).strip() == "":
        return default
    try:
        return float(str(v).strip().strip('"'))
    except ValueError:
        return default


def b(key, default=False):
    """Boolean value, defaulting when key is missing or blank."""
    v = str(flat.get(key, "")).strip().strip('"').lower()
    if v in ("true", "yes", "y", "1"):
        return True
    if v in ("false", "no", "n", "0"):
        return False
    return default


def s(key, default=""):
    """String value, defaulting when key is missing or blank."""
    v = str(flat.get(key, "")).strip().strip('"')
    return v if v else default


def default_feed():
    """Never-empty-array fallback for feed (shared by broilers and layers)."""
    return {
        "ingredients": {"wheat": 0, "barley": 0, "sorghum": 0, "soybean": 0, "millrun": 0},
        "feedPurchased": 0,
        "additionalIngredient": 0,
        "emissionIntensity": 0,
    }


def build_feed(prefix):
    """Single feed ration entry (shared by broilers and layers)."""
    return {
        "ingredients": {
            "wheat":   f(f"{prefix}_ingredients_wheat"),
            "barley":  f(f"{prefix}_ingredients_barley"),
            "sorghum": f(f"{prefix}_ingredients_sorghum"),
            "soybean": f(f"{prefix}_ingredients_soybean"),
            "millrun": f(f"{prefix}_ingredients_millrun"),
        },
        "feedPurchased":        f(f"{prefix}_feed purchased"),
        "additionalIngredient": f(f"{prefix}_additional ingredient"),
        "emissionIntensity":    f(f"{prefix}_emission intensity"),
    }


def build_purchases(prefix):
    """Head / purchase weight block (shared by broilers and layers)."""
    return {
        "head":           f(f"{prefix}_head"),
        "purchaseWeight": f(f"{prefix}_purchase weight"),
    }


# ========================================================================
# BROILER BUILDERS
# ========================================================================
def b_build_meat_class(prefix):
    """Bird class block (growers / layers / other)."""
    return {
        "birds":                  f(f"{prefix}_birds"),
        "averageStayLength50":    f(f"{prefix}_average stay length50"),
        "liveweight50":           f(f"{prefix}_liveweight50"),
        "averageStayLength100":   f(f"{prefix}_average stay length100"),
        "liveweight100":          f(f"{prefix}_liveweight100"),
        "dryMatterIntake":        f(f"{prefix}_dry matter intake"),
        "dryMatterDigestibility": f(f"{prefix}_dry matter digestibility"),
        "crudeProtein":           f(f"{prefix}_crude protein"),
        "manureAsh":              f(f"{prefix}_manure ash"),
        "nitrogenRetentionRate":  f(f"{prefix}_nitrogen retention rate"),
    }


def b_build_group(prefix):
    """Single bird group within a broiler enterprise."""
    feed = []
    k = 0
    while f"{prefix}_feed_{k}_feed purchased" in flat or f"{prefix}_feed_{k}_emission intensity" in flat:
        feed.append(build_feed(f"{prefix}_feed_{k}"))
        k += 1
    if not feed:
        feed = [default_feed()]

    return {
        "meatChickenGrowers": b_build_meat_class(f"{prefix}_meat chicken growers"),
        "meatChickenLayers":  b_build_meat_class(f"{prefix}_meat chicken layers"),
        "meatOther":          b_build_meat_class(f"{prefix}_meat other"),
        "feed": feed,
        "customFeedPurchased":         f(f"{prefix}_custom feed purchased"),
        "customFeedEmissionIntensity": f(f"{prefix}_custom feed emission intensity"),
    }


def b_default_group():
    zero_class = {
        "birds": 0, "averageStayLength50": 0, "liveweight50": 0,
        "averageStayLength100": 0, "liveweight100": 0, "dryMatterIntake": 0,
        "dryMatterDigestibility": 0, "crudeProtein": 0, "manureAsh": 0,
        "nitrogenRetentionRate": 0,
    }
    return {
        "meatChickenGrowers": dict(zero_class),
        "meatChickenLayers":  dict(zero_class),
        "meatOther":          dict(zero_class),
        "feed": [default_feed()],
        "customFeedPurchased": 0,
        "customFeedEmissionIntensity": 0,
    }


def b_build_sale(prefix):
    """Single sales entry (three bird classes)."""
    return {
        "meatChickenGrowersSales": {
            "head":       f(f"{prefix}_meat chicken growers sales_head"),
            "saleWeight": f(f"{prefix}_meat chicken growers sales_sale weight"),
        },
        "meatChickenLayers": {
            "head":       f(f"{prefix}_meat chicken layers_head"),
            "saleWeight": f(f"{prefix}_meat chicken layers_sale weight"),
        },
        "meatOther": {
            "head":       f(f"{prefix}_meat other_head"),
            "saleWeight": f(f"{prefix}_meat other_sale weight"),
        },
    }


def b_default_sale():
    return {
        "meatChickenGrowersSales": {"head": 0, "saleWeight": 0},
        "meatChickenLayers":       {"head": 0, "saleWeight": 0},
        "meatOther":               {"head": 0, "saleWeight": 0},
    }


def build_broiler(prefix):
    """Single broiler (chicken meat) enterprise."""
    groups = []
    j = 0
    while f"{prefix}_groups_{j}_meat chicken growers_birds" in flat:
        groups.append(b_build_group(f"{prefix}_groups_{j}"))
        j += 1
    if not groups:
        groups = [b_default_group()]

    sales = []
    j = 0
    while f"{prefix}_sales_{j}_meat chicken growers sales_head" in flat:
        sales.append(b_build_sale(f"{prefix}_sales_{j}"))
        j += 1
    if not sales:
        sales = [b_default_sale()]

    return {
        "id": s(f"{prefix}_id"),
        "groups": groups,
        "diesel":  f(f"{prefix}_diesel"),
        "petrol":  f(f"{prefix}_petrol"),
        "lpg":     f(f"{prefix}_lpg"),
        "electricitySource":    s(f"{prefix}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{prefix}_electricity renewable"),
        "electricityUse":       f(f"{prefix}_electricity use"),
        "hay":            f(f"{prefix}_hay"),
        "herbicide":      f(f"{prefix}_herbicide"),
        "herbicideOther": f(f"{prefix}_herbicide other"),
        "manureWasteAllocation":       f(f"{prefix}_manure waste allocation"),
        "wasteHandledDrylotOrStorage": f(f"{prefix}_waste handled drylot or storage"),
        "litterRecycled":         f(f"{prefix}_litter recycled"),
        "litterRecycleFrequency": f(f"{prefix}_litter recycle frequency"),
        "purchasedFreeRange":     f(f"{prefix}_purchased free range"),
        "meatChickenGrowersPurchases": build_purchases(f"{prefix}_meat chicken growers purchases"),
        "meatChickenLayersPurchases":  build_purchases(f"{prefix}_meat chicken layers purchases"),
        "meatOtherPurchases":          build_purchases(f"{prefix}_meat other purchases"),
        "sales": sales,
    }


# ========================================================================
# LAYER BUILDERS  (flat keys inferred - see NOTE above; >>> VERIFY)
# ========================================================================
def l_build_seasons(prefix):
    """Seasonal flock counts (autumn / winter / spring / summer)."""
    return {
        "autumn": f(f"{prefix}_autumn"),
        "winter": f(f"{prefix}_winter"),
        "spring": f(f"{prefix}_spring"),
        "summer": f(f"{prefix}_summer"),
    }


def l_build_egg_sale(prefix):
    """Egg sale block (eggs produced / average weight).  >>> VERIFY sub-key names."""
    return {
        "eggsProduced":  f(f"{prefix}_eggs produced"),
        "averageWeight": f(f"{prefix}_average weight"),
    }


def build_layer(prefix):
    """Single layer (egg) enterprise."""
    feed = []
    k = 0
    while f"{prefix}_feed_{k}_feed purchased" in flat or f"{prefix}_feed_{k}_emission intensity" in flat:
        feed.append(build_feed(f"{prefix}_feed_{k}"))
        k += 1
    if not feed:
        feed = [default_feed()]

    return {
        "id": s(f"{prefix}_id"),
        "layers":            l_build_seasons(f"{prefix}_layers"),
        "meatChickenLayers": l_build_seasons(f"{prefix}_meat chicken layers"),
        "feed": feed,
        "purchasedFreeRange": f(f"{prefix}_purchased free range"),
        "diesel":  f(f"{prefix}_diesel"),
        "petrol":  f(f"{prefix}_petrol"),
        "lpg":     f(f"{prefix}_lpg"),
        "electricitySource":    s(f"{prefix}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{prefix}_electricity renewable"),
        "electricityUse":       f(f"{prefix}_electricity use"),
        "hay":            f(f"{prefix}_hay"),
        "herbicide":      f(f"{prefix}_herbicide"),
        "herbicideOther": f(f"{prefix}_herbicide other"),
        "manureWasteAllocation":       f(f"{prefix}_manure waste allocation"),
        "wasteHandledDrylotOrStorage": f(f"{prefix}_waste handled drylot or storage"),
        "litterRecycled":         f(f"{prefix}_litter recycled"),
        "litterRecycleFrequency": f(f"{prefix}_litter recycle frequency"),
        "meatChickenLayersPurchases": build_purchases(f"{prefix}_meat chicken layers purchases"),
        "layersPurchases":            build_purchases(f"{prefix}_layers purchases"),
        "customFeedPurchased":         f(f"{prefix}_custom feed purchased"),
        "customFeedEmissionIntensity": f(f"{prefix}_custom feed emission intensity"),
        "meatChickenLayersEggSale": l_build_egg_sale(f"{prefix}_meat chicken layers egg sale"),
        "layersEggSale":            l_build_egg_sale(f"{prefix}_layers egg sale"),
    }


# ========================================================================
# VEGETATION
# ========================================================================
def build_vegetation(prefix, n_broilers, n_layers):
    """Single vegetation (tree planting) entry."""
    return {
        "vegetation": {
            "region":      s(f"{prefix}_vegetation_region", "South West"),
            "treeSpecies": s(f"{prefix}_vegetation_tree species", "Mixed species (Environmental Plantings)"),
            "soil":        s(f"{prefix}_vegetation_soil", "Loams & Clays"),
            "area":        f(f"{prefix}_vegetation_area"),
            "age":         f(f"{prefix}_vegetation_age"),
        },
        "broilersProportion": [f(f"{prefix}_broilers proportion_{i}") for i in range(n_broilers)],
        "layersProportion":   [f(f"{prefix}_layers proportion_{i}") for i in range(n_layers)],
    }


def default_vegetation(n_broilers, n_layers):
    """Never-empty-array fallback for vegetation."""
    return {
        "vegetation": {
            "region": "South West",
            "treeSpecies": "Mixed species (Environmental Plantings)",
            "soil": "Loams & Clays",
            "area": 0,
            "age": 0,
        },
        "broilersProportion": [0] * n_broilers,
        "layersProportion":   [0] * n_layers,
    }


# =========================
# BUILD PAYLOAD
# =========================
# Broiler (chicken meat) enterprises
broilers = []
i = 0
while f"broilers_{i}_id" in flat:
    broilers.append(build_broiler(f"broilers_{i}"))
    i += 1

# Layer (egg) enterprises
layers = []
i = 0
while f"layers_{i}_id" in flat:
    layers.append(build_layer(f"layers_{i}"))
    i += 1

# Vegetation - never sent as an empty array
vegetation = []
i = 0
while f"vegetation_{i}_vegetation_area" in flat:
    vegetation.append(build_vegetation(f"vegetation_{i}", len(broilers), len(layers)))
    i += 1
if not vegetation:
    vegetation = [default_vegetation(len(broilers), len(layers))]

payload = {
    "state": s("state"),
    "northOfTropicOfCapricorn": b("north of tropic of capricorn"),
    "rainfallAbove600": b("rainfall above 600"),
    "broilers": broilers,
    "layers": layers,
    "vegetation": vegetation,
}

# =========================
# PAYLOAD PREVIEW
# =========================
print("=" * 25)
print("PAYLOAD PREVIEW")
print("=" * 25)
print(json.dumps(payload, indent=2))
print("=" * 25)
print(f"Broiler enterprises: {len(broilers)}")
for idx, ent in enumerate(broilers):
    print(f"  broilers[{idx}]: {len(ent['groups'])} group(s), {len(ent['sales'])} sales entry(s)")
print(f"Layer enterprises  : {len(layers)}")
for idx, ent in enumerate(layers):
    print(f"  layers[{idx}]: {len(ent['feed'])} feed entry(s)")
print(f"Vegetation entries : {len(vegetation)}")
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