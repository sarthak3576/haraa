"""
POST /api/v1/chat -- Cognito-JWT-authorized.
Body: {"message": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}
Stateless (the JSON API has no server-side session), so the caller resends
its own trimmed history each turn. Reuses the exact same provider chain
(Gemini -> Bedrock -> offline) as the server-rendered /api/chat route.

GEMINI_API_KEY is fetched here from SSM Parameter Store (SecureString, set
up OUTSIDE this stack via `aws ssm put-parameter`) *before* app.config is
imported, since app.config only ever reads it from a real environment
variable or .env.local -- never written here, never logged.
"""
import json
import os

_param_name = os.environ.get("GEMINI_SSM_PARAM_NAME")
if _param_name:
    try:
        import boto3
        _ssm = boto3.client("ssm")
        _value = _ssm.get_parameter(Name=_param_name, WithDecryption=True)["Parameter"]["Value"]
        os.environ.setdefault("GEMINI_API_KEY", _value)
    except Exception:  # noqa: BLE001 -- no parameter set yet, or no value: chain falls back to Bedrock/offline
        pass

from app.services.chatbot_service import get_chat_reply  # noqa: E402


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    if not (claims.get("email") or claims.get("cognito:username")):
        return _response(401, {"error": "No email claim on the token."})

    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Request body must be JSON."})

    message = payload.get("message", "").strip()
    if not message:
        return _response(400, {"error": "Missing 'message'."})
    history = payload.get("history", [])[-6:]

    result = get_chat_reply(message, history)
    return _response(200, result)
