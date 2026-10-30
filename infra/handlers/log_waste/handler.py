"""
POST /api/v1/waste-events -- Cognito-JWT-authorized.
Body: {"category": "plastic", "weight_kg": 0.5, "source": "api", "confidence": 0.0}
Reuses app.services.dashboard_service.log_waste_event exactly as the
server-rendered /upload/log route does.
"""
import json

from app.services.dashboard_service import log_waste_event
from app.services.waste_categories import ALL_CATEGORIES


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Request body must be JSON."})

    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_email = claims.get("email") or claims.get("cognito:username")
    if not user_email:
        return _response(401, {"error": "No email claim on the token."})

    category = payload.get("category")
    if category not in ALL_CATEGORIES:
        category = "other"

    try:
        weight_kg = float(payload.get("weight_kg", 0.5))
    except (TypeError, ValueError):
        return _response(400, {"error": "weight_kg must be a number."})

    log_waste_event(
        category=category,
        weight_kg=weight_kg,
        user_email=user_email,
        source=payload.get("source", "api"),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
    )

    return _response(200, {"ok": True, "category": category, "weight_kg": weight_kg})
