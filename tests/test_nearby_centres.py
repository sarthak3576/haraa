from app.services.maps_links import build_maps_url
from app.services.nearby_centres_data import (
    CATEGORY_BY_ID,
    DASHBOARD_CATEGORY_TO_NEARBY_ID,
    NEARBY_CATEGORIES,
)


def test_build_maps_url_with_place_encodes_spaces_and_builds_near_query():
    url = build_maps_url("e-waste recycling centre", place="Koramangala, Bengaluru")
    assert url.startswith("https://www.google.com/maps/search/?api=1&query=")
    assert "e-waste+recycling+centre+near+Koramangala%2C+Bengaluru" in url


def test_build_maps_url_with_coordinates():
    url = build_maps_url("scrap dealer kabadiwala", lat=12.9352, lng=77.6146)
    assert "near+12.9352%2C77.6146" in url


def test_build_maps_url_coordinates_take_priority_over_place():
    url = build_maps_url("hazardous waste collection centre", place="Chennai", lat=13.08, lng=80.27)
    assert "13.08%2C80.27" in url
    assert "Chennai" not in url


def test_build_maps_url_with_no_location_falls_back_to_bare_term():
    url = build_maps_url("composting unit facility")
    assert url == "https://www.google.com/maps/search/?api=1&query=composting+unit+facility"


def test_build_maps_url_escapes_special_characters():
    url = build_maps_url("plastic recycling centre", place="M.G. Road & 5th Cross")
    assert "%26" in url  # '&' must be escaped, not left as a literal query separator
    assert url.count("&") == 1  # only the api=1&query= separator remains unescaped


def test_all_nine_categories_present():
    assert len(NEARBY_CATEGORIES) == 9
    for cat in NEARBY_CATEGORIES:
        assert cat["bring"]
        assert cat["dont_bring"]
        assert cat["tip"]


def test_dashboard_category_mapping_covers_all_categories():
    expected = {"plastic", "paper", "metal", "glass", "organic", "e-waste", "hazardous", "other"}
    assert set(DASHBOARD_CATEGORY_TO_NEARBY_ID.keys()) == expected
    for nearby_id in DASHBOARD_CATEGORY_TO_NEARBY_ID.values():
        assert nearby_id in CATEGORY_BY_ID
