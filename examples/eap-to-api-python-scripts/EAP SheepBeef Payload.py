"""
EAP Emissions Calculator - COMBINED SHEEP + BEEF submission
Flat-CSV / EAP pattern.

Reads a single flat key-value CSV export containing both the sheep and beef
enterprises for one business, builds the nested combined payload, and POSTs it
to the AIA EAP Emissions Calculator API over mTLS.
"""

import json
import pandas as pd
import requests

# =========================
# CONFIG
# =========================

CSV_PATH = r"your file path here"
API_URL   = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.0/sheepbeef"
CERT_PATH = r"your file path here"
KEY_PATH = r"your file path here"

# =========================
# SCHEMA DEFAULTS
# =========================
# Values the EAP CSV export does not carry but the schema exposes.
# >>> ENTERPRISE-SPECIFIC - review per business.

# Beef purchases carry a purchaseSource enum; the CSV export omits purchases
# entirely when there are none. Used only for zeroed fallback entries.
DEFAULT_PURCHASE_SOURCE = "Dairy origin"

# Fallback enums for zeroed placeholder entries (never-empty-array rule).
DEFAULT_OTHER_FERTILISER = "Monoammonium phosphate (MAP)"
DEFAULT_BURNING = {
    "fuel": "fine",
    "season": "early dry season",
    "patchiness": "low",
    "rainfallZone": "low",
    "yearsSinceLastFire": 0,
    "fireScarArea": 0,
    "vegetation": "Shrubland hummock",
}
DEFAULT_VEGETATION = {
    "region": "South West",
    "treeSpecies": "Mixed species (Environmental Plantings)",
    "soil": "Loams & Clays",
    "area": 0,
    "age": 0,
}

# Sheep seasons expose feedAvailability, which the EAP CSV export does not
# contain. Leave False to omit the field; set True to send it (defaults to 0
# wherever the CSV has no value).
EMIT_FEED_AVAILABILITY = False

# =========================
# LOAD FLAT CSV
# =========================

df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
flat = dict(zip(df["key"].str.strip(), df["value"]))

# =========================
# SAFE VALUE HELPERS
# =========================


def f(key, default=0.0):
    """Float from the flat dict, tolerating blanks and stray quotes."""
    raw = str(flat.get(key, "")).strip().strip('"')
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def b(key, default=False):
    """Boolean from the flat dict."""
    raw = str(flat.get(key, "")).strip().strip('"').lower()
    if raw in ("true", "yes", "1"):
        return True
    if raw in ("false", "no", "0"):
        return False
    return default


def s(key, default=""):
    """String from the flat dict."""
    raw = str(flat.get(key, "")).strip().strip('"')
    return raw if raw else default


def has(key):
    """True when the key exists and carries a value."""
    return str(flat.get(key, "")).strip().strip('"') != ""


# =========================
# CLASS NAME MAPS
# =========================

BEEF_CLASSES = {
    "bullsGt1": "bulls gt1",
    "bullsGt1Traded": "bulls gt1 traded",
    "steersLt1": "steers lt1",
    "steersLt1Traded": "steers lt1 traded",
    "steers1To2": "steers1 to2",
    "steers1To2Traded": "steers1 to2 traded",
    "steersGt2": "steers gt2",
    "steersGt2Traded": "steers gt2 traded",
    "cowsGt2": "cows gt2",
    "cowsGt2Traded": "cows gt2 traded",
    "heifersLt1": "heifers lt1",
    "heifersLt1Traded": "heifers lt1 traded",
    "heifers1To2": "heifers1 to2",
    "heifers1To2Traded": "heifers1 to2 traded",
    "heifersGt2": "heifers gt2",
    "heifersGt2Traded": "heifers gt2 traded",
}

SHEEP_CLASSES = {
    "rams": "rams",
    "tradeRams": "trade rams",
    "wethers": "wethers",
    "tradeWethers": "trade wethers",
    "maidenBreedingEwes": "maiden breeding ewes",
    "tradeMaidenBreedingEwes": "trade maiden breeding ewes",
    "breedingEwes": "breeding ewes",
    "tradeBreedingEwes": "trade breeding ewes",
    "otherEwes": "other ewes",
    "tradeOtherEwes": "trade other ewes",
    "eweLambs": "ewe lambs",
    "tradeEweLambs": "trade ewe lambs",
    "wetherLambs": "wether lambs",
    "tradeWetherLambs": "trade wether lambs",
}

SEASONS = ["autumn", "winter", "spring", "summer"]

# =========================
# BUILDER FUNCTIONS
# =========================


def build_season(prefix, season, include_feed_availability=False):
    """One seasonal block. prefix is e.g. 'beef_0_classes_bulls gt1'."""
    base = f"{prefix}_{season}"
    block = {
        "head": f(f"{base}_head"),
        "liveweight": f(f"{base}_liveweight"),
        "liveweightGain": f(f"{base}_liveweight gain"),
        "crudeProtein": f(f"{base}_crude protein"),
        "dryMatterDigestibility": f(f"{base}_dry matter digestibility"),
    }
    if include_feed_availability:
        block["feedAvailability"] = f(f"{base}_feed availability")
    return block


def build_purchases(prefix, include_source):
    """Purchases array for one class. Never returned empty."""
    purchases = []
    j = 0
    while has(f"{prefix}_purchases_{j}_head") or has(
        f"{prefix}_purchases_{j}_purchase weight"
    ):
        entry = {}
        if include_source:
            entry["purchaseSource"] = s(
                f"{prefix}_purchases_{j}_purchase source", DEFAULT_PURCHASE_SOURCE
            )
        entry["head"] = f(f"{prefix}_purchases_{j}_head")
        entry["purchaseWeight"] = f(f"{prefix}_purchases_{j}_purchase weight")
        purchases.append(entry)
        j += 1

    if not purchases:
        entry = {}
        if include_source:
            entry["purchaseSource"] = DEFAULT_PURCHASE_SOURCE
        entry["head"] = 0
        entry["purchaseWeight"] = 0
        purchases.append(entry)

    return purchases


def build_beef_class(prefix):
    """One beef class block."""
    block = {season: build_season(prefix, season) for season in SEASONS}
    block["headSold"] = f(f"{prefix}_head sold")
    block["saleWeight"] = f(f"{prefix}_sale weight")
    block["purchases"] = build_purchases(prefix, include_source=True)
    return block


def build_sheep_class(prefix):
    """One sheep class block."""
    block = {
        season: build_season(prefix, season, EMIT_FEED_AVAILABILITY)
        for season in SEASONS
    }
    block["headShorn"] = f(f"{prefix}_head shorn")
    block["woolShorn"] = f(f"{prefix}_wool shorn")
    block["cleanWoolYield"] = f(f"{prefix}_clean wool yield")
    block["headSold"] = f(f"{prefix}_head sold")
    block["saleWeight"] = f(f"{prefix}_sale weight")
    block["purchases"] = build_purchases(prefix, include_source=False)
    return block


def build_fertiliser(prefix):
    """Fertiliser block, shared shape across beef and sheep."""
    others = []
    j = 0
    while has(f"{prefix}_fertiliser_other fertilisers_{j}_other type"):
        others.append(
            {
                "otherType": s(
                    f"{prefix}_fertiliser_other fertilisers_{j}_other type"
                ),
                "otherDryland": f(
                    f"{prefix}_fertiliser_other fertilisers_{j}_other dryland"
                ),
                "otherIrrigated": f(
                    f"{prefix}_fertiliser_other fertilisers_{j}_other irrigated"
                ),
            }
        )
        j += 1

    if not others:
        others.append(
            {
                "otherType": DEFAULT_OTHER_FERTILISER,
                "otherDryland": 0,
                "otherIrrigated": 0,
            }
        )

    return {
        "singleSuperphosphate": f(f"{prefix}_fertiliser_single superphosphate"),
        "pastureDryland": f(f"{prefix}_fertiliser_pasture dryland"),
        "pastureIrrigated": f(f"{prefix}_fertiliser_pasture irrigated"),
        "cropsDryland": f(f"{prefix}_fertiliser_crops dryland"),
        "cropsIrrigated": f(f"{prefix}_fertiliser_crops irrigated"),
        "otherFertilisers": others,
    }


def build_minerals(prefix):
    """Mineral supplementation block, shared shape across beef and sheep."""
    return {
        "mineralBlock": f(f"{prefix}_mineral supplementation_mineral block"),
        "mineralBlockUrea": f(f"{prefix}_mineral supplementation_mineral block urea"),
        "weanerBlock": f(f"{prefix}_mineral supplementation_weaner block"),
        "weanerBlockUrea": f(f"{prefix}_mineral supplementation_weaner block urea"),
        "drySeasonMix": f(f"{prefix}_mineral supplementation_dry season mix"),
        "drySeasonMixUrea": f(f"{prefix}_mineral supplementation_dry season mix urea"),
    }


def build_seasonal_fractions(prefix, label):
    """Four-season fraction block, e.g. cows calving / ewes lambing."""
    return {season: f(f"{prefix}_{label}_{season}") for season in SEASONS}


def build_beef_enterprise(i):
    """One beef enterprise."""
    prefix = f"beef_{i}"
    return {
        "id": "",
        "classes": {
            api_name: build_beef_class(f"{prefix}_classes_{csv_name}")
            for api_name, csv_name in BEEF_CLASSES.items()
        },
        "limestone": f(f"{prefix}_limestone"),
        "limestoneFraction": f(f"{prefix}_limestone fraction"),
        "fertiliser": build_fertiliser(prefix),
        "diesel": f(f"{prefix}_diesel"),
        "petrol": f(f"{prefix}_petrol"),
        "lpg": f(f"{prefix}_lpg"),
        "mineralSupplementation": build_minerals(prefix),
        "electricitySource": s(f"{prefix}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{prefix}_electricity renewable"),
        "electricityUse": f(f"{prefix}_electricity use"),
        "grainFeed": f(f"{prefix}_grain feed"),
        "hayFeed": f(f"{prefix}_hay feed"),
        "cottonseedFeed": f(f"{prefix}_cottonseed feed"),
        "herbicide": f(f"{prefix}_herbicide"),
        "herbicideOther": f(f"{prefix}_herbicide other"),
        "cowsCalving": build_seasonal_fractions(prefix, "cows calving"),
    }


def build_sheep_enterprise(i):
    """One sheep enterprise."""
    prefix = f"sheep_{i}"
    return {
        "id": "",
        "classes": {
            api_name: build_sheep_class(f"{prefix}_classes_{csv_name}")
            for api_name, csv_name in SHEEP_CLASSES.items()
        },
        "limestone": f(f"{prefix}_limestone"),
        "limestoneFraction": f(f"{prefix}_limestone fraction"),
        "fertiliser": build_fertiliser(prefix),
        "diesel": f(f"{prefix}_diesel"),
        "petrol": f(f"{prefix}_petrol"),
        "lpg": f(f"{prefix}_lpg"),
        "mineralSupplementation": build_minerals(prefix),
        "electricitySource": s(f"{prefix}_electricity source", "State Grid"),
        "electricityRenewable": f(f"{prefix}_electricity renewable"),
        "electricityUse": f(f"{prefix}_electricity use"),
        "grainFeed": f(f"{prefix}_grain feed"),
        "hayFeed": f(f"{prefix}_hay feed"),
        "herbicide": f(f"{prefix}_herbicide"),
        "herbicideOther": f(f"{prefix}_herbicide other"),
        "merinoPercent": f(f"{prefix}_merino percent"),
        "ewesLambing": build_seasonal_fractions(prefix, "ewes lambing"),
        "seasonalLambing": build_seasonal_fractions(prefix, "seasonal lambing"),
    }


def build_burning():
    """Burning array. Never returned empty."""
    burning = []
    i = 0
    while has(f"burning_{i}_fuel"):
        burning.append(
            {
                "fuel": s(f"burning_{i}_fuel"),
                "season": s(f"burning_{i}_season"),
                "patchiness": s(f"burning_{i}_patchiness"),
                "rainfallZone": s(f"burning_{i}_rainfall zone"),
                "yearsSinceLastFire": f(f"burning_{i}_years since last fire"),
                "fireScarArea": f(f"burning_{i}_fire scar area"),
                "vegetation": s(f"burning_{i}_vegetation"),
            }
        )
        i += 1

    if not burning:
        burning.append(dict(DEFAULT_BURNING))

    return burning


def build_proportions(i, label, enterprise_count):
    """
    Allocation proportions for one vegetation block.
    Padded to one entry per enterprise so the array length always matches.
    """
    values = []
    j = 0
    while has(f"vegetation_{i}_{label} proportion_{j}"):
        values.append(f(f"vegetation_{i}_{label} proportion_{j}"))
        j += 1

    while len(values) < enterprise_count:
        values.append(0)

    return values[:enterprise_count] if enterprise_count else [0]


def build_vegetation(beef_count, sheep_count):
    """Vegetation array. Never returned empty."""
    vegetation = []
    i = 0
    while has(f"vegetation_{i}_vegetation_region"):
        vegetation.append(
            {
                "vegetation": {
                    "region": s(f"vegetation_{i}_vegetation_region"),
                    "treeSpecies": s(f"vegetation_{i}_vegetation_tree species"),
                    "soil": s(f"vegetation_{i}_vegetation_soil"),
                    "area": f(f"vegetation_{i}_vegetation_area"),
                    "age": f(f"vegetation_{i}_vegetation_age"),
                },
                "beefProportion": build_proportions(i, "beef", beef_count),
                "sheepProportion": build_proportions(i, "sheep", sheep_count),
            }
        )
        i += 1

    if not vegetation:
        vegetation.append(
            {
                "vegetation": dict(DEFAULT_VEGETATION),
                "beefProportion": [0] * max(beef_count, 1),
                "sheepProportion": [0] * max(sheep_count, 1),
            }
        )

    return vegetation


# =========================
# ASSEMBLE PAYLOAD
# =========================

beef_enterprises = []
i = 0
while f"beef_{i}_id" in flat:
    beef_enterprises.append(build_beef_enterprise(i))
    i += 1

sheep_enterprises = []
i = 0
while f"sheep_{i}_id" in flat:
    sheep_enterprises.append(build_sheep_enterprise(i))
    i += 1

payload = {
    "state": s("state"),
    "northOfTropicOfCapricorn": b("north of tropic of capricorn"),
    "rainfallAbove600": b("rainfall above 600"),
    "beef": beef_enterprises,
    "sheep": sheep_enterprises,
    "burning": build_burning(),
    "vegetation": build_vegetation(len(beef_enterprises), len(sheep_enterprises)),
}

# =========================
# PAYLOAD PREVIEW
# =========================

print("=" * 60)
print("COMBINED SHEEP + BEEF PAYLOAD PREVIEW")
print("=" * 60)
print(f"State: {payload['state']}")
print(f"Beef enterprises:  {len(payload['beef'])}")
print(f"Sheep enterprises: {len(payload['sheep'])}")
print(f"Burning blocks:    {len(payload['burning'])}")
print(f"Vegetation blocks: {len(payload['vegetation'])}")
print("-" * 60)
print(json.dumps(payload, indent=2))
print("=" * 60)

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

print(f"Status code: {response.status_code}")
print(response.text)
