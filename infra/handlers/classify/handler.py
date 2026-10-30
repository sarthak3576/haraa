"""
POST /api/v1/classify -- Cognito-JWT-authorized.
Body: {"key": "<S3 object key under uploads/, from /api/v1/uploads/presign>"}
Classifies the already-uploaded image via Rekognition DetectLabels, reading
it directly from S3 (no image bytes round-trip through API Gateway/Lambda).
"""
import json
import os

from app.aws_clients import get_rekognition_client
from app.services.waste_categories import classify_labels

UPLOADS_BUCKET = os.environ["UPLOADS_BUCKET"]


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Request body must be JSON."})

    key = payload.get("key")
    if not key or not key.startswith("uploads/"):
        return _response(400, {"error": "Missing or invalid 'key' (expected an uploads/... S3 key)."})

    client = get_rekognition_client()
    try:
        response = client.detect_labels(
            Image={"S3Object": {"Bucket": UPLOADS_BUCKET, "Name": key}},
            MaxLabels=15,
            MinConfidence=55,
        )
    except client.exceptions.InvalidS3ObjectException:
        return _response(404, {"error": "That upload wasn't found (it may have already expired -- uploads are deleted after 7 days)."})
    except Exception as exc:  # noqa: BLE001
        return _response(502, {"error": f"Rekognition call failed: {exc}"})

    labels = response.get("Labels", [])
    category, confidence, matched_label = classify_labels(labels)

    return _response(200, {
        "engine": "Amazon Rekognition",
        "category": category,
        "confidence": round(confidence, 1),
        "matched_label": matched_label,
        "all_labels": [
            {"name": l["Name"], "confidence": round(l["Confidence"], 1)}
            for l in labels
        ],
    })
