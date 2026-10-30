"""
Wraps the Gemini Developer API (google-genai SDK) for the chatbot's
primary provider. GEMINI_API_KEY is read from the environment only (via
app.config, which itself only reads os.environ / an untouched .env) --
this module never writes it anywhere, including logs.
"""
import logging

from google import genai
from google.genai import errors, types

from app import config
from app.services.chat_diagnostics import classify_gemini_exception
from app.services.chat_system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# finish_reason values that mean "a complete, unblocked answer"
_OK_FINISH_REASONS = {"STOP", "MAX_TOKENS"}


class GeminiUnavailable(Exception):
    """Network error, timeout, rate limit, or other API failure.

    `.reason` is a short, plain-English string (e.g. "Gemini: rate limit
    reached") safe to show directly in the UI.
    """

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


class GeminiBlocked(Exception):
    """The prompt or response was blocked by Gemini's safety filters."""

    def __init__(self, message: str):
        super().__init__(message)
        self.reason = "Gemini: response blocked by safety filters"


def _history_to_contents(message: str, history: list[dict]) -> list[dict]:
    contents = []
    for turn in history[-6:]:
        role = "model" if turn.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    return contents


def get_gemini_reply(message: str, history: list[dict]) -> str:
    if not config.GEMINI_API_KEY:
        raise GeminiUnavailable("GEMINI_API_KEY is not set", reason="Gemini: key not set")

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    contents = _history_to_contents(message, history)
    # The Gemini API rejects a deadline below 10s outright (INVALID_ARGUMENT),
    # so the configured ~8s target is floored here rather than sent as-is.
    timeout_ms = int(max(config.GEMINI_TIMEOUT_SECONDS, 10) * 1000)

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=400,
                temperature=0.4,
                http_options=types.HttpOptions(timeout=timeout_ms),
            ),
        )
    except (errors.ClientError, errors.ServerError, errors.APIError, TimeoutError, OSError) as exc:
        reason = classify_gemini_exception(exc)
        logger.warning("Gemini call failed (%s): %s", reason, exc)
        raise GeminiUnavailable(f"Gemini call failed: {exc}", reason=reason) from exc

    block_reason = None
    prompt_feedback = getattr(response, "prompt_feedback", None)
    if prompt_feedback is not None and getattr(prompt_feedback, "block_reason", None):
        block_reason = prompt_feedback.block_reason

    finish_reason = None
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        finish_reason = getattr(candidates[0], "finish_reason", None)
        finish_reason = str(finish_reason).rsplit(".", 1)[-1] if finish_reason else None

    if block_reason or (finish_reason and finish_reason not in _OK_FINISH_REASONS) or not response.text:
        logger.warning("Gemini blocked response: block_reason=%s finish_reason=%s", block_reason, finish_reason)
        raise GeminiBlocked(f"Gemini blocked the response (finish_reason={finish_reason}, block_reason={block_reason})")

    return response.text.strip()
