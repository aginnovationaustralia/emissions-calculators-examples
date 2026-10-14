import json
import re

import pandas as pd
import requests

# =========================
# CONFIG
# =========================
CSV_PATH = r"your file path here"
CERT_PATH = r"your file path here"
KEY_PATH = r"your file path here"
API_URL = "https://emissionscalculator-mtls.production.aiaapi.com/calculator/3.0.2/feedlot"

# =========================
# LOAD FLAT CSV
# =========================
df = pd.read_csv(CSV_PATH)
flat = dict(zip(df["key"].astype(str).str.strip(), df["value"]))


# =========================
# SAFE VALUE HELPERS
# =========================
def f(key, default=0):
    """Float value from the flat CSV, falling back to a default."""
    v = flat.get(key)
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def b(key, default=False):
    """Boolean value from the flat CSV, falling back to a default."""
    v = flat.get(key)
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return default
    return str(v).strip().strip('"').lower() in ("true", "yes", "y", "1")


def s(key, default=""):
    """String value from the flat CSV, falling back to a default."""
    v = flat.get(key)
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "":
        return default
    return str(v).strip().strip('"')


# =========================
# KEY NAMING HELPER
# =========================
def csv_key(camel):
    """Convert an API camelCase field name into the CSV's spaced form.

    The EAP export writes camelCase API fields with a space inserted before
    each capital letter, in lower case:
        heifers1To2Traded  ->  heifers1 to2 traded
        steersLt1          ->  steers lt1
    """
    return re.sub(r"(?<!^)(?=[A-Z])", " ", camel).lower()


# >>> ENTERPRISE-SPECIFIC: the 16 livestock categories used by both
# the purchases and sales blocks, in API camelCase.
LIVESTOCK_CATEGORIES = [
    "bullsGt1",
    "bullsGt1Traded",
    "steersLt1",
    "steersLt1Traded",
    "steers1To2",
    "steers1To2Traded",
    "steersGt2",
    "steersGt2Traded",
    "cowsGt2",
    "cowsGt2Traded",
    "heifersLt1",
    "heifersLt1Traded",
    "heifers1To2",
    "heifers1To2Traded",
    "heifersGt2",
    "heifersGt2Traded",
]

# >>> ENTERPRISE-SPECIFIC: enum defaults used when an array would otherwise
# be empty (the API rejects empty repeating arrays).
DEFAULT_PURCHASE_SOURCE = "sth NSW/VIC/sth SA"
DEFAULT_OTHER_FERTILISER = "Monoammonium phosphate (MAP)"
DEFAULT_VEG_REGION = "South West"
DEFAULT_VEG_SPECIES = "Mixed species (Environmental Plantings)"
DEFAULT_VEG_SOIL = "Loams & Clays"


# =========================
# BUILDERS
# =========================
def build_stays(prefix):
    """stays[] under a feedlot group."""
    stays = []
    k = 0
    while f"{prefix}_stays_{k}_livestock" in flat:
        p = f"{prefix}_stays_{k}"
        stays.append(
            {
                "livestock": f(f"{p}_livestock"),
                "stayAverageDuration": f(f"{p}_stay average duration"),
                "liveweight": f(f"{p}_liveweight"),
                "dryMatterDigestibility": f(f"{p}_dry matter digestibility"),
                "crudeProtein": f(f"{p}_crude protein"),
                "nitrogenRetention": f(f"{p}_nitrogen retention"),
                "dailyIntake": f(f"{p}_daily intake"),
                "ndf": f(f"{p}_ndf"),
                "etherExtract": f(f"{p}_ether extract"),
            }
        )
        k += 1

    if not stays:
        stays = [
            {
                "livestock": 0,
                "stayAverageDuration": 0,
                "liveweight": 0,
                "dryMatterDigestibility": 0,
                "crudeProtein": 0,
                "nitrogenRetention": 0,
                "dailyIntake": 0,
                "ndf": 0,
                "etherExtract": 0,
            }
        ]
    return stays


def build_groups(prefix):
    """groups[] under a feedlot."""
    groups = []
    j = 0
    while any(k.startswith(f"{prefix}_groups_{j}_") for k in flat):
        groups.append({"stays": build_stays(f"{prefix}_groups_{j}")})
        j += 1

    if not groups:
        groups = [{"stays": build_stays(f"{prefix}_groups_0")}]
    return groups


def build_other_fertilisers(prefix):
    """otherFertilisers[] under a feedlot's fertiliser block."""
    others = []
    j = 0
    while f"{prefix}_other fertilisers_{j}_other type" in flat:
        p = f"{prefix}_other fertilisers_{j}"
        others.append(
            {
                "otherType": s(f"{p}_other type", DEFAULT_OTHER_FERTILISER),
                "otherDryland": f(f"{p}_other dryland"),
                "otherIrrigated": f(f"{p}_other irrigated"),
            }
        )
        j += 1

    if not others:
        others = [
            {
                "otherType": DEFAULT_OTHER_FERTILISER,
                "otherDryland": 0,
                "otherIrrigated": 0,
            }
        ]
    return others


def build_fertiliser(prefix):
    """fertiliser{} under a feedlot."""
    p = f"{prefix}_fertiliser"
    return {
        "singleSuperphosphate": f(f"{p}_single superphosphate"),
        "pastureDryland": f(f"{p}_pasture dryland"),
        "pastureIrrigated": f(f"{p}_pasture irrigated"),
        "cropsDryland": f(f"{p}_crops dryland"),
        "cropsIrrigated": f(f"{p}_crops irrigated"),
        "otherFertilisers": build_other_fertilisers(p),
    }


def build_purchase_entries(prefix, category):
    """One livestock category array inside purchases{}."""
    entries = []
    j = 0
    base = f"{prefix}_purchases_{csv_key(category)}"
    while f"{base}_{j}_head" in flat:
        p = f"{base}_{j}"
        entries.append(
            {
                "head": f(f"{p}_head"),
                "purchaseWeight": f(f"{p}_purchase weight"),
                "purchaseSource": s(f"{p}_purchase source", DEFAULT_PURCHASE_SOURCE),
            }
        )
        j += 1

    if not entries:
        entries = [
            {
                "head": 0,
                "purchaseWeight": 0,
                "purchaseSource": DEFAULT_PURCHASE_SOURCE,
            }
        ]
    return entries


def build_sale_entries(prefix, category):
    """One livestock category array inside sales{}."""
    entries = []
    j = 0
    base = f"{prefix}_sales_{csv_key(category)}"
    while f"{base}_{j}_head" in flat:
        p = f"{base}_{j}"
        entries.append(
            {
                "head": f(f"{p}_head"),
                "saleWeight": f(f"{p}_sale weight"),
            }
        )
        j += 1

    if not entries:
        entries = [{"head": 0, "saleWeight": 0}]
    return entries


def build_purchases(prefix):
    """purchases{} under a feedlot — every category always present."""
    return {c: build_purchase_entries(prefix, c) for c in LIVESTOCK_CATEGORIES}


def build_sales(prefix):
    """sales{} under a feedlot — every category always present."""
    return {c: build_sale_entries(prefix, c) for c in LIVESTOCK_CATEGORIES}


def build_feedlots():
    """feedlots[] at the payload root."""
    feedlots = []
    i = 0
    while f"feedlots_{i}_id" in flat:
        p = f"feedlots_{i}"
        feedlots.append(
            {
                "id": s(f"{p}_id"),
                "system": s(f"{p}_system", "Drylot"),
                "groups": build_groups(p),
                "fertiliser": build_fertiliser(p),
                "purchases": build_purchases(p),
                "sales": build_sales(p),
                "diesel": f(f"{p}_diesel"),
                "petrol": f(f"{p}_petrol"),
                "lpg": f(f"{p}_lpg"),
                "electricitySource": s(f"{p}_electricity source", "State Grid"),
                "electricityRenewable": f(f"{p}_electricity renewable"),
                "electricityUse": f(f"{p}_electricity use"),
                "grainFeed": f(f"{p}_grain feed"),
                "hayFeed": f(f"{p}_hay feed"),
                "cottonseedFeed": f(f"{p}_cottonseed feed"),
                "herbicide": f(f"{p}_herbicide"),
                "herbicideOther": f(f"{p}_herbicide other"),
                "distanceCattleTransported": f(f"{p}_distance cattle transported"),
                "truckType": s(f"{p}_truck type", "4 Deck Trailer"),
                "limestone": f(f"{p}_limestone"),
                "limestoneFraction": f(f"{p}_limestone fraction"),
            }
        )
        i += 1
    return feedlots


def build_feedlot_proportion(prefix, feedlot_count):
    """feedlotProportion[] — one entry per feedlot."""
    proportions = []
    j = 0
    while f"{prefix}_feedlot proportion_{j}" in flat:
        proportions.append(f(f"{prefix}_feedlot proportion_{j}"))
        j += 1

    if not proportions:
        proportions = [0] * max(feedlot_count, 1)
    return proportions


def build_vegetation(feedlot_count):
    """vegetation[] at the payload root."""
    vegetation = []
    i = 0
    while f"vegetation_{i}_vegetation_area" in flat:
        p = f"vegetation_{i}"
        vegetation.append(
            {
                "vegetation": {
                    "region": s(f"{p}_vegetation_region", DEFAULT_VEG_REGION),
                    "treeSpecies": s(f"{p}_vegetation_tree species", DEFAULT_VEG_SPECIES),
                    "soil": s(f"{p}_vegetation_soil", DEFAULT_VEG_SOIL),
                    "area": f(f"{p}_vegetation_area"),
                    "age": f(f"{p}_vegetation_age"),
                },
                "feedlotProportion": build_feedlot_proportion(p, feedlot_count),
            }
        )
        i += 1

    if not vegetation:
        vegetation = [
            {
                "vegetation": {
                    "region": DEFAULT_VEG_REGION,
                    "treeSpecies": DEFAULT_VEG_SPECIES,
                    "soil": DEFAULT_VEG_SOIL,
                    "area": 0,
                    "age": 0,
                },
                "feedlotProportion": [0] * max(feedlot_count, 1),
            }
        ]
    return vegetation


# =========================
# BUILD PAYLOAD
# =========================
feedlots = build_feedlots()

payload = {
    "id": s("id"),
    "state": s("state"),
    "feedlots": feedlots,
    "vegetation": build_vegetation(len(feedlots)),
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
# POST TO API
# =========================
headers = {"Content-Type": "application/json"}

response = requests.post(
    API_URL,
    json=payload,
    headers=headers,
    cert=(CERT_PATH, KEY_PATH),
    verify=True,
)

print("=" * 25)
print("API RESPONSE")
print("=" * 25)
print("Status code:", response.status_code)
print(response.text)
