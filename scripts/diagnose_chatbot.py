"""
Direct diagnostic for the chatbot's LLM providers. Loads config the same
way the app does (real env vars > .env.local > .env), reports only
whether each secret is "set" or "not set" (never the value), makes a real
call to Gemini (if a key is configured) and to Bedrock with the
configured models, and reports the outcome -- success, or the exact
exception type/message and its classified plain-English reason.

Run with:
    .venv/bin/python scripts/diagnose_chatbot.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402  (loads .env/.env.local as a side effect)
from app.services.chat_diagnostics import classify_bedrock_exception, classify_gemini_exception  # noqa: E402
from app.services.gemini_chatbot import get_gemini_reply  # noqa: E402


def main():
    print("=" * 70)
    print("Chatbot provider diagnostic")
    print("=" * 70)

    print(f"\nCHATBOT_PROVIDER        = {config.CHATBOT_PROVIDER}")
    print(f"GEMINI_MODEL            = {config.GEMINI_MODEL}")
    print(f"GEMINI_API_KEY          = {'set' if config.GEMINI_API_KEY else 'not set'}")
    print(f"BEDROCK_MODEL_ID        = {config.BEDROCK_MODEL_ID}")
    print(f"BEDROCK_REGION          = {config.BEDROCK_REGION}")
    print(f"GEMINI_TIMEOUT_SECONDS  = {config.GEMINI_TIMEOUT_SECONDS}")
    print(f"BEDROCK_TIMEOUT_SECONDS = {config.BEDROCK_TIMEOUT_SECONDS}")

    print("\n--- Gemini ---")
    if not config.GEMINI_API_KEY:
        print("Result: SKIPPED -- no key set.")
        print("To enable Gemini, add this line to .env.local (create the file if it doesn't exist):")
        print("    GEMINI_API_KEY=your-key-from-aistudio.google.com")
    else:
        try:
            get_gemini_reply("ping", [])
            print("Result: SUCCESS -- Gemini answered.")
        except Exception as exc:  # noqa: BLE001 -- intentionally broad, this IS the diagnostic
            reason = getattr(exc, "reason", None) or classify_gemini_exception(exc)
            print("Result: FAILED")
            print(f"Exception type: {type(exc).__name__}")
            print(f"Exception message: {exc}")
            print(f"Classified reason: {reason}")

    print("\n--- Bedrock ---")
    try:
        from app.services.chatbot_service import _get_bedrock_reply
        _get_bedrock_reply("ping", [])
        print("Result: SUCCESS -- Bedrock answered.")
    except Exception as exc:  # noqa: BLE001
        reason = classify_bedrock_exception(exc)
        print("Result: FAILED")
        print(f"Exception type: {type(exc).__name__}")
        print(f"Exception message: {exc}")
        print(f"Classified reason: {reason}")
        if "access not enabled" in reason:
            print(
                "Note: this is an AWS account restriction (Bedrock model access must be "
                "approved in the Bedrock console under 'Model access') -- not something "
                "this code can fix."
            )

    print("\n--- Offline assistant ---")
    print("Result: SUCCESS (always available, no external call)")

    print("\nDone.")


if __name__ == "__main__":
    main()
