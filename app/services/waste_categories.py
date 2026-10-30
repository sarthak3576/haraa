"""
Maps Amazon Rekognition labels to a small set of waste categories, and holds
illustrative (not scientifically audited) CO2-savings-per-kg factors used to
populate the dashboard. These numbers are rough, commonly cited ballpark
figures meant to make the demo dashboard feel real -- tune them if you have
better local data.
"""

CATEGORY_KEYWORDS = {
    "plastic": [
        "plastic", "plastic bottle", "bottle", "bag", "packaging",
        "plastic bag", "disposable", "straw", "wrap",
    ],
    "paper": [
        "paper", "cardboard", "box", "carton", "newspaper", "book",
        "document", "envelope",
    ],
    "metal": [
        "can", "tin", "aluminium", "aluminum", "metal", "steel", "foil",
    ],
    "glass": [
        "glass", "jar", "wine bottle",
    ],
    "organic": [
        "food", "fruit", "vegetable", "plant", "leaf", "produce",
        "compost", "banana", "apple",
    ],
    "e-waste": [
        "electronics", "phone", "mobile phone", "computer", "laptop",
        "battery", "circuit board", "cable",
    ],
}

CO2_SAVED_PER_KG = {
    "plastic": 1.5,
    "paper": 0.9,
    "metal": 2.0,
    "glass": 0.3,
    "organic": 0.5,
    "e-waste": 3.0,
    "other": 0.2,
}

ALL_CATEGORIES = list(CO2_SAVED_PER_KG.keys())

DEFAULT_WEIGHT_KG = 0.5


def classify_labels(labels: list[dict]) -> tuple[str, float, str]:
    """
    labels: Rekognition DetectLabels 'Labels' list, each a dict with
    'Name' and 'Confidence'.

    Returns (category, confidence, matched_label_name). Falls back to
    ("other", 0.0, "") if nothing recognizable was found.
    """
    best = ("other", 0.0, "")
    for label in labels:
        name = label.get("Name", "")
        confidence = float(label.get("Confidence", 0.0))
        name_lower = name.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in name_lower for keyword in keywords):
                if confidence > best[1]:
                    best = (category, confidence, name)
    return best
