"""The approved public grooming tariffs, stored as integer paise."""

DOG_PACKAGES = [
    ("bath-brush", "Bath & Brush"),
    ("hygiene-groom", "Hygiene Groom"),
    ("full-groom", "Full Style Groom"),
    ("signature-coat-spa", "Signature Coat Spa"),
]

CAT_PACKAGES = [
    ("cat-coat-refresh", "Coat Refresh"),
    ("cat-hygiene-groom", "Hygiene Groom"),
    ("cat-full-coat-groom", "Full Coat Groom"),
]

DOG_PRICES = {
    "bath-brush": {"small": 99900, "medium": 119900, "large": 149900, "giant": 189900},
    "hygiene-groom": {"small": 129900, "medium": 159900, "large": 199900, "giant": 249900},
    "full-groom": {"small": 179900, "medium": 219900, "large": 269900, "giant": 329900},
    "signature-coat-spa": {"small": 229900, "medium": 269900, "large": 329900, "giant": 399900},
}

CAT_PRICES = {
    "cat-coat-refresh": {"short": 99900, "long": 129900},
    "cat-hygiene-groom": {"short": 139900, "long": 169900},
    "cat-full-coat-groom": {"short": 189900, "long": 239900},
}

DOG_SIZE_LABELS = {"small": "Toy/Small", "medium": "Medium", "large": "Large", "giant": "Giant"}
CAT_COAT_LABELS = {"short": "Short coat", "long": "Long coat"}


def price_for(species, service_slug, size=None, coat=None):
    """Return the approved tariff in paise, or None for services quoted by scope."""
    if species == "dog":
        return DOG_PRICES.get(service_slug, {}).get(size)
    if species == "cat":
        return CAT_PRICES.get(service_slug, {}).get(coat)
    return None


def decorate_service(service):
    """Attach derived display data; stored service rows never set customer prices."""
    item = dict(service)
    labels = dict(DOG_PACKAGES + CAT_PACKAGES)
    if item["slug"] in labels:
        item["name"] = labels[item["slug"]]
    dog = DOG_PRICES.get(item["slug"])
    cat = CAT_PRICES.get(item["slug"])
    price_map = dog or cat or {}
    item["price_map"] = price_map
    item["price"] = min(price_map.values()) if price_map else None
    item["reference"] = None
    return item


def pricing_tables():
    return {
        "dog_packages": DOG_PACKAGES,
        "dog_sizes": DOG_SIZE_LABELS,
        "dog_prices": DOG_PRICES,
        "cat_packages": CAT_PACKAGES,
        "cat_coats": CAT_COAT_LABELS,
        "cat_prices": CAT_PRICES,
    }

