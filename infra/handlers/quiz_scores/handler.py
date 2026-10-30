"""
GET/POST /api/v1/quiz-score -- Cognito-JWT-authorized.
GET: {"best_score": N}
POST body {"score": N}: {"best_score": N} (updated only if higher, same
rule as app.services.segregation_game_service.submit_score).
"""
import json

from app.services.segregation_game_service import get_best_score, submit_score


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_email = claims.get("email") or claims.get("cognito:username")
    if not user_email:
        return _response(401, {"error": "No email claim on the token."})

    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if method == "GET":
        return _response(200, {"best_score": get_best_score(user_email)})

    try:
        payload = json.loads(event.get("body") or "{}")
        score = int(payload["score"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _response(400, {"error": "Body must be JSON with an integer 'score'."})

    return _response(200, {"best_score": submit_score(user_email, score)})
