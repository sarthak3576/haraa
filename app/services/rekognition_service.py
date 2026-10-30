from app.aws_clients import get_rekognition_client
from app.services.waste_categories import classify_labels


def detect_waste_type(image_bytes: bytes) -> dict:
    """
    Calls Rekognition DetectLabels on raw image bytes (no S3 bucket needed)
    and maps the result onto a waste category.
    """
    client = get_rekognition_client()
    response = client.detect_labels(
        Image={"Bytes": image_bytes},
        MaxLabels=15,
        MinConfidence=55,
    )
    labels = response.get("Labels", [])
    category, confidence, matched_label = classify_labels(labels)

    return {
        "category": category,
        "confidence": round(confidence, 1),
        "matched_label": matched_label,
        "all_labels": [
            {"name": l["Name"], "confidence": round(l["Confidence"], 1)}
            for l in labels
        ],
    }
