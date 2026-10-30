"""
Curates a clean subset of the shared waste item database for the
segregation game: only items whose bin maps unambiguously onto one of
the 5 game bins (wet / dry / hazardous / e-waste / biomedical).
"""
from app.services.waste_items_data import WASTE_ITEMS

GAME_BINS = ["wet", "dry", "hazardous", "e-waste", "biomedical"]

BIN_LABELS = {
    "wet": "Wet waste",
    "dry": "Dry waste",
    "hazardous": "Hazardous",
    "e-waste": "E-waste",
    "biomedical": "Biomedical",
}


def _map_bin(bin_text: str) -> str | None:
    lower = bin_text.lower()
    if lower.startswith("biomedical"):
        return "biomedical"
    if lower.startswith("e-waste") and "or" not in lower:
        return "e-waste"
    if lower.startswith("hazardous") and "if" not in lower and "or" not in lower:
        return "hazardous"
    if lower.startswith("wet waste") and "or" not in lower:
        return "wet"
    if lower.startswith("dry waste") and "or" not in lower:
        return "dry"
    return None


GAME_ITEMS = [
    {"title": item["title"], "bin": _map_bin(item["bin"])}
    for item in WASTE_ITEMS
    if _map_bin(item["bin"]) is not None
]
