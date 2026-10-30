"""
Turns raw Gemini/Bedrock exceptions into short, plain-English reasons
("Gemini: key not set", "Bedrock: access not enabled on this AWS
account", ...) used by the chat status line, /api/chatbot/health, and
scripts/diagnose_chatbot.py.

Never includes the API key or any secret value in a returned reason.
"""
from google.genai import errors as genai_errors


def classify_gemini_exception(exc: Exception) -> str:
    if isinstance(exc, genai_errors.ClientError):
        code = getattr(exc, "code", None)
        message = str(exc)
        if code == 429:
            return "Gemini: rate limit reached"
        if code == 404:
            return "Gemini: model not found"
        if "API_KEY_INVALID" in message or "API key not valid" in message:
            return "Gemini: invalid API key"
        if code in (401, 403):
            return "Gemini: API key not authorized"
        return f"Gemini: request rejected ({code})"

    if isinstance(exc, genai_errors.ServerError):
        return "Gemini: server error, temporarily unavailable"

    if isinstance(exc, genai_errors.APIError):
        return f"Gemini: API error ({getattr(exc, 'code', 'unknown')})"

    if isinstance(exc, TimeoutError):
        return "Gemini: request timed out"

    if isinstance(exc, OSError):
        return "Gemini: network error"

    return f"Gemini: unexpected error ({type(exc).__name__})"


def classify_bedrock_exception(exc: Exception) -> str:
    from botocore.exceptions import BotoCoreError, ClientError

    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        message = exc.response.get("Error", {}).get("Message", "")

        if code == "AccessDeniedException":
            return "Bedrock: access not enabled on this AWS account"
        if code == "ResourceNotFoundException":
            return "Bedrock: model not found"
        if code == "ValidationException":
            lower_message = message.lower()
            if "not allowed" in lower_message or "not authorized" in lower_message:
                return "Bedrock: access not enabled on this AWS account"
            if "model" in lower_message and (
                "identifier" in lower_message or "not found" in lower_message or "on-demand" in lower_message
            ):
                return "Bedrock: model not found or not enabled for on-demand use"
            return "Bedrock: invalid request"
        if code == "ThrottlingException":
            return "Bedrock: rate limit reached"
        if code == "ExpiredTokenException" or code == "UnrecognizedClientException":
            return "Bedrock: AWS credentials invalid or expired"
        return f"Bedrock: request rejected ({code or 'unknown'})"

    if isinstance(exc, BotoCoreError):
        if "Timeout" in type(exc).__name__:
            return "Bedrock: request timed out"
        return "Bedrock: network error"

    return f"Bedrock: unexpected error ({type(exc).__name__})"
