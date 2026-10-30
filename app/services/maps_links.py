"""
Builds plain Google Maps search URLs: no API key, no billing account, no
embedded map, just https://www.google.com/maps/search/?api=1&query=...
which opens the Maps search results page directly.
"""
from urllib.parse import quote_plus

MAPS_SEARCH_BASE = "https://www.google.com/maps/search/?api=1&query="


def build_maps_url(category_term: str, place: str | None = None,
                    lat: float | None = None, lng: float | None = None) -> str:
    if lat is not None and lng is not None:
        query = f"{category_term} near {lat},{lng}"
    elif place:
        query = f"{category_term} near {place}"
    else:
        query = category_term
    return MAPS_SEARCH_BASE + quote_plus(query)
