import io

from PIL import Image

from app.services.fallback_chatbot import fallback_reply
from app.services.image_utils import InvalidImageError, load_and_normalize_image
from app.services.impact_calculator import calculate_impact
from app.services.waste_categories import classify_labels


def test_fallback_chatbot_matches_keyword():
    reply = fallback_reply("How do I recycle plastic bottles?")
    assert "plastic" in reply.lower()


def test_fallback_chatbot_default_reply():
    reply = fallback_reply("asdkjaslkdj random gibberish")
    assert "not confident enough" in reply.lower()


def test_classify_labels_maps_known_keyword():
    labels = [{"Name": "Plastic Bottle", "Confidence": 92.0}]
    category, confidence, matched = classify_labels(labels)
    assert category == "plastic"
    assert matched == "Plastic Bottle"


def test_classify_labels_falls_back_to_other():
    labels = [{"Name": "Mystery Object", "Confidence": 99.0}]
    category, confidence, matched = classify_labels(labels)
    assert category == "other"


def test_calculate_impact_basic():
    result = calculate_impact({"plastic": 2.0, "paper": 1.0})
    assert result["total_co2_kg"] == round(2.0 * 1.5 + 1.0 * 0.9, 2)
    assert result["total_trees"] > 0  # only paper contributes trees
    assert "plastic" in result["breakdown"]


def test_calculate_impact_ignores_zero_amounts():
    result = calculate_impact({"plastic": 0, "metal": 0})
    assert result["total_co2_kg"] == 0
    assert result["breakdown"] == {}


def test_load_and_normalize_image_accepts_valid_jpeg():
    img = Image.new("RGB", (50, 50), color=(10, 20, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    normalized_image, jpeg_bytes = load_and_normalize_image(buf.getvalue())
    assert normalized_image.mode == "RGB"
    assert jpeg_bytes[:2] == b"\xff\xd8"  # JPEG magic bytes


def test_load_and_normalize_image_rejects_garbage():
    try:
        load_and_normalize_image(b"not an image, just text")
        assert False, "expected InvalidImageError"
    except InvalidImageError:
        pass


def test_load_and_normalize_image_rejects_empty():
    try:
        load_and_normalize_image(b"")
        assert False, "expected InvalidImageError"
    except InvalidImageError:
        pass
