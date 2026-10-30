"""
Tests for the Gemini/Bedrock/offline chatbot provider chain. All AWS and
Gemini API calls are mocked -- no network access or real credentials are
used.
"""
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError as BotoClientError
from google.genai import errors as genai_errors

from app import config
from app.services import chatbot_service
from app.services.fallback_chatbot import fallback_reply
from app.services.gemini_chatbot import GeminiBlocked, GeminiUnavailable, get_gemini_reply


# ---------- gemini_chatbot.get_gemini_reply (mocking the genai SDK client) ----------

def _fake_response(text="Hello!", finish_reason="STOP", block_reason=None):
    candidate = MagicMock()
    candidate.finish_reason = finish_reason
    response = MagicMock()
    response.text = text
    response.candidates = [candidate]
    response.prompt_feedback = MagicMock()
    response.prompt_feedback.block_reason = block_reason
    return response


def test_get_gemini_reply_success(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = _fake_response(text="Recycle it!")

    with patch("app.services.gemini_chatbot.genai.Client", return_value=fake_client):
        reply = get_gemini_reply("How do I recycle plastic?", [])

    assert reply == "Recycle it!"


def test_get_gemini_reply_raises_unavailable_without_api_key(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    with pytest.raises(GeminiUnavailable) as exc_info:
        get_gemini_reply("hi", [])
    assert exc_info.value.reason == "Gemini: key not set"


def test_get_gemini_reply_raises_unavailable_on_rate_limit(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = genai_errors.ClientError(
        code=429, response_json={"error": {"message": "rate limited"}}
    )

    with patch("app.services.gemini_chatbot.genai.Client", return_value=fake_client):
        with pytest.raises(GeminiUnavailable) as exc_info:
            get_gemini_reply("hi", [])
    assert exc_info.value.reason == "Gemini: rate limit reached"


def test_get_gemini_reply_raises_unavailable_on_invalid_key(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = genai_errors.ClientError(
        code=400,
        response_json={"error": {"message": "API key not valid. Please pass a valid API key."}},
    )

    with patch("app.services.gemini_chatbot.genai.Client", return_value=fake_client):
        with pytest.raises(GeminiUnavailable) as exc_info:
            get_gemini_reply("hi", [])
    assert exc_info.value.reason == "Gemini: invalid API key"


def test_get_gemini_reply_raises_unavailable_on_model_not_found(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = genai_errors.ClientError(
        code=404, response_json={"error": {"message": "model not found"}}
    )

    with patch("app.services.gemini_chatbot.genai.Client", return_value=fake_client):
        with pytest.raises(GeminiUnavailable) as exc_info:
            get_gemini_reply("hi", [])
    assert exc_info.value.reason == "Gemini: model not found"


def test_get_gemini_reply_raises_blocked_on_safety_finish_reason(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = _fake_response(text=None, finish_reason="SAFETY")

    with patch("app.services.gemini_chatbot.genai.Client", return_value=fake_client):
        with pytest.raises(GeminiBlocked) as exc_info:
            get_gemini_reply("hi", [])
    assert exc_info.value.reason == "Gemini: response blocked by safety filters"


# ---------- chat_diagnostics classifiers ----------

def test_classify_bedrock_access_denied():
    from app.services.chat_diagnostics import classify_bedrock_exception
    exc = BotoClientError({"Error": {"Code": "AccessDeniedException", "Message": "nope"}}, "Converse")
    assert classify_bedrock_exception(exc) == "Bedrock: access not enabled on this AWS account"


def test_classify_bedrock_throttling():
    from app.services.chat_diagnostics import classify_bedrock_exception
    exc = BotoClientError({"Error": {"Code": "ThrottlingException", "Message": "too many requests"}}, "Converse")
    assert classify_bedrock_exception(exc) == "Bedrock: rate limit reached"


def test_classify_bedrock_operation_not_allowed_is_access_not_enabled():
    from app.services.chat_diagnostics import classify_bedrock_exception
    exc = BotoClientError(
        {"Error": {"Code": "ValidationException", "Message": "Operation not allowed"}}, "Converse"
    )
    assert classify_bedrock_exception(exc) == "Bedrock: access not enabled on this AWS account"


# ---------- chatbot_service.get_chat_reply (provider chain orchestration) ----------

def test_chat_reply_uses_gemini_when_available(monkeypatch):
    monkeypatch.setattr(config, "CHATBOT_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(chatbot_service, "get_gemini_reply", lambda m, h: "gemini says hi")

    result = chatbot_service.get_chat_reply("hello", [])
    assert result["provider"] == "gemini"
    assert result["reply"] == "gemini says hi"
    assert result["notes"] == []


def test_chat_reply_falls_back_to_bedrock_when_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(config, "CHATBOT_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")

    def fake_gemini(message, history):
        raise GeminiUnavailable("simulated outage", reason="Gemini: rate limit reached")

    monkeypatch.setattr(chatbot_service, "get_gemini_reply", fake_gemini)
    monkeypatch.setattr(chatbot_service, "_get_bedrock_reply", lambda m, h: "bedrock says hi")

    result = chatbot_service.get_chat_reply("hello", [])
    assert result["provider"] == "bedrock"
    assert result["reply"] == "bedrock says hi"
    assert result["notes"] == ["Gemini: rate limit reached"]


def test_chat_reply_falls_back_to_offline_when_everything_fails(monkeypatch):
    monkeypatch.setattr(config, "CHATBOT_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")

    def fake_gemini(message, history):
        raise GeminiUnavailable("simulated outage", reason="Gemini: key not set")

    def fake_bedrock(message, history):
        raise BotoClientError({"Error": {"Code": "AccessDeniedException", "Message": "nope"}}, "Converse")

    monkeypatch.setattr(chatbot_service, "get_gemini_reply", fake_gemini)
    monkeypatch.setattr(chatbot_service, "_get_bedrock_reply", fake_bedrock)

    result = chatbot_service.get_chat_reply("how do I recycle plastic?", [])
    assert result["provider"] == "offline"
    assert "plastic" in result["reply"].lower()
    assert result["notes"] == ["Gemini: key not set", "Bedrock: access not enabled on this AWS account"]


def test_chat_reply_reports_missing_gemini_key_and_falls_back_to_bedrock(monkeypatch):
    monkeypatch.setattr(config, "CHATBOT_PROVIDER", "auto")
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    monkeypatch.setattr(chatbot_service, "_get_bedrock_reply", lambda m, h: "bedrock says hi")

    result = chatbot_service.get_chat_reply("hello", [])
    assert result["provider"] == "bedrock"
    assert result["notes"] == ["Gemini: key not set"]


def test_chat_reply_provider_setting_offline_skips_everything_else(monkeypatch):
    monkeypatch.setattr(config, "CHATBOT_PROVIDER", "offline")
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")

    def fail(*args, **kwargs):
        raise AssertionError("should not be called when CHATBOT_PROVIDER=offline")

    monkeypatch.setattr(chatbot_service, "get_gemini_reply", fail)
    monkeypatch.setattr(chatbot_service, "_get_bedrock_reply", fail)

    result = chatbot_service.get_chat_reply("hello", [])
    assert result["provider"] == "offline"


# ---------- fallback_chatbot (60+ topics, fuzzy matching, generic-word guard) ----------

def test_fallback_reply_handles_thermometer_typo():
    reply = fallback_reply("how do i dispose a borken thermometr")
    assert "mercury" in reply.lower() or "hazardous" in reply.lower()


def test_fallback_reply_exact_thermometer_match():
    reply = fallback_reply("I broke a thermometer, what do I do?")
    assert "mercury" in reply.lower()
    assert "collection point" in reply.lower()


def test_fallback_has_at_least_120_topics():
    from app.services.fallback_chatbot import TOPICS
    assert len(TOPICS) >= 120


def test_fallback_does_not_match_generic_waste_word():
    """Regression test: 'how much waste is produced globally in 2026' used
    to match the e-waste topic purely because 'waste' is a substring of
    'e-waste'. It must not do that, and should instead recognise this as a
    stats/current-events question it can't answer offline."""
    reply = fallback_reply("how much waste is produced globally in 2026")
    assert "e-waste" not in reply.lower()
    assert "statistics" in reply.lower() or "current events" in reply.lower()


def test_fallback_recognises_stats_question_by_year():
    reply = fallback_reply("what was the total garbage generated in 2025")
    assert "online assistant" in reply.lower()


def test_fallback_unmatched_question_suggests_three_topics():
    reply = fallback_reply("zzz qqq nonsense query")
    assert "did you mean" in reply.lower()
    # three suggestions joined by "; "
    assert reply.count(";") == 2


def test_fallback_topic_includes_bin_and_do_not_note():
    reply = fallback_reply("what bin does a plastic bottle go in")
    assert "dry waste" in reply.lower()
    assert "don't" in reply.lower()


def test_fallback_hazardous_items_mention_collection_point():
    for query in ["broken thermometer", "old batteries", "expired medicine", "paint can"]:
        reply = fallback_reply(query)
        assert "collection point" in reply.lower() or "pharmacy" in reply.lower() or "authorised" in reply.lower()
