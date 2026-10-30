import logging
import time

from botocore.exceptions import BotoCoreError, ClientError

from app import config
from app.aws_clients import get_bedrock_runtime_client
from app.services.chat_diagnostics import classify_bedrock_exception
from app.services.chat_system_prompt import SYSTEM_PROMPT
from app.services.fallback_chatbot import fallback_reply
from app.services.gemini_chatbot import GeminiBlocked, GeminiUnavailable, get_gemini_reply

logger = logging.getLogger(__name__)

# Which providers to try, in order, for each CHATBOT_PROVIDER setting.
# Every chain ends in "offline" so the user always gets an answer.
_PROVIDER_CHAINS = {
    "auto": ["gemini", "bedrock", "offline"],
    "gemini": ["gemini", "offline"],
    "bedrock": ["bedrock", "offline"],
    "offline": ["offline"],
}


def _get_bedrock_reply(message: str, history: list[dict]) -> str:
    client = get_bedrock_runtime_client()

    messages = []
    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": [{"text": turn["content"]}]})
    messages.append({"role": "user", "content": [{"text": message}]})

    response = client.converse(
        modelId=config.BEDROCK_MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=messages,
        inferenceConfig={"maxTokens": 400, "temperature": 0.4},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def get_chat_reply(message: str, history: list[dict]) -> dict:
    """
    Returns {"reply": str, "provider": "gemini"|"bedrock"|"offline", "notes": [str, ...]}.

    "notes" lists the short, plain-English reason each skipped/failed
    provider didn't answer (e.g. "Gemini: key not set",
    "Bedrock: access not enabled on this AWS account") -- safe to show directly in the UI.
    """
    chain = _PROVIDER_CHAINS.get(config.CHATBOT_PROVIDER, _PROVIDER_CHAINS["auto"])
    notes: list[str] = []

    for provider in chain:
        if provider == "gemini":
            try:
                reply = get_gemini_reply(message, history)
                return {"reply": reply, "provider": "gemini", "notes": notes}
            except GeminiBlocked as exc:
                logger.warning("Gemini blocked the response: %s", exc)
                notes.append(exc.reason)
                continue
            except GeminiUnavailable as exc:
                logger.warning("Gemini unavailable: %s", exc)
                notes.append(exc.reason)
                continue

        elif provider == "bedrock":
            try:
                reply = _get_bedrock_reply(message, history)
                return {"reply": reply, "provider": "bedrock", "notes": notes}
            except (ClientError, BotoCoreError, KeyError, IndexError) as exc:
                reason = classify_bedrock_exception(exc)
                logger.warning("Bedrock unavailable (%s): %s", reason, exc)
                notes.append(reason)
                continue

        else:  # "offline" -- always succeeds, ends every chain
            return {"reply": fallback_reply(message), "provider": "offline", "notes": notes}

    # Should be unreachable since every chain ends in "offline", but keep a
    # safe final fallback just in case.
    return {"reply": fallback_reply(message), "provider": "offline", "notes": notes}


_HEALTH_CACHE_TTL_SECONDS = 30
_health_cache: dict[str, tuple[float, dict]] = {}


def _check_gemini_health() -> dict:
    try:
        get_gemini_reply("ping", [])
        return {"available": True, "reason": None}
    except GeminiBlocked as exc:
        return {"available": False, "reason": exc.reason}
    except GeminiUnavailable as exc:
        return {"available": False, "reason": exc.reason}


def _check_bedrock_health() -> dict:
    try:
        _get_bedrock_reply("ping", [])
        return {"available": True, "reason": None}
    except (ClientError, BotoCoreError, KeyError, IndexError) as exc:
        return {"available": False, "reason": classify_bedrock_exception(exc)}


def get_provider_health() -> dict:
    """
    Runs (cheap, cached for 30s) live checks against Gemini and Bedrock and
    reports which chatbot providers are actually working right now, with a
    plain-English reason for any that aren't. Used by /api/chatbot/health.
    """
    now = time.time()
    checks = {"gemini": _check_gemini_health, "bedrock": _check_bedrock_health}
    results = {}

    for name, check_fn in checks.items():
        cached = _health_cache.get(name)
        if cached and (now - cached[0]) < _HEALTH_CACHE_TTL_SECONDS:
            results[name] = cached[1]
            continue
        result = check_fn()
        _health_cache[name] = (now, result)
        results[name] = result

    results["offline"] = {"available": True, "reason": None}
    results["active_provider_chain"] = _PROVIDER_CHAINS.get(config.CHATBOT_PROVIDER, _PROVIDER_CHAINS["auto"])
    return results
