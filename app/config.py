"""
Configuration loading order (highest priority first):
  1. Real process environment variables (shell export, launch environment).
  2. .env.local -- YOUR secrets (GEMINI_API_KEY, etc). Gitignored. Never
     written to by this app; you edit it yourself.
  3. .env -- non-secret app/resource config, plus the auto-generated
     SESSION_SECRET. Written to only via app/env_file_io.py's
     upsert_env_file(), which preserves every other line untouched.

An empty value in a higher-priority source does NOT hide a real value in a
lower-priority one -- each key is resolved by checking all three sources in
order and taking the first non-blank value found.

Both files are loaded by absolute path from the project root (not the
current working directory), so this works the same regardless of where
you launch the app from.
"""
import secrets
from pathlib import Path

from dotenv import dotenv_values
import os

from app.env_file_io import upsert_env_file

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
ENV_LOCAL_PATH = BASE_DIR / ".env.local"

_env_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
_env_local_values = dotenv_values(ENV_LOCAL_PATH) if ENV_LOCAL_PATH.exists() else {}

# If AWS credentials are provided in .env.local or .env, ensure boto3 sees them in os.environ
for _aws_key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_DEFAULT_REGION"):
    if _aws_key not in os.environ:
        _val = _env_local_values.get(_aws_key) or _env_values.get(_aws_key)
        if _val:
            os.environ[_aws_key] = _val


def _get(key: str, default: str = "") -> str:
    """env var > .env.local > .env, skipping blank values at each level."""
    for source in (os.environ, _env_local_values, _env_values):
        value = source.get(key)
        if value:
            return value
    return default


# --- AWS region / service config (resource identifiers only, never secrets) ---
AWS_REGION = _get("AWS_REGION", "ap-south-1")
BEDROCK_REGION = _get("BEDROCK_REGION", AWS_REGION)
BEDROCK_MODEL_ID = _get("BEDROCK_MODEL_ID", "anthropic.claude-haiku-5-5")

COGNITO_USER_POOL_ID = _get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = _get("COGNITO_CLIENT_ID", "")

DYNAMODB_TABLE_NAME = _get("DYNAMODB_TABLE_NAME", "WasteMgmt")

APP_HOST = _get("APP_HOST", "127.0.0.1")
APP_PORT = int(_get("APP_PORT", "8000"))

# --- Chatbot provider settings ---
# CHATBOT_PROVIDER: "auto" (default, try Gemini -> Bedrock -> offline),
# "gemini" (Gemini -> offline), "bedrock" (Bedrock -> offline), or
# "offline" (offline assistant only).
CHATBOT_PROVIDER = _get("CHATBOT_PROVIDER", "auto").strip().lower()
if CHATBOT_PROVIDER not in ("auto", "gemini", "bedrock", "offline"):
    CHATBOT_PROVIDER = "auto"

# Gemini: free-tier-eligible Flash model as of writing (ai.google.dev/gemini-api/docs/models).
# gemini-3.8-flash ("new stable") was tried first but reproducibly hung
# (504 DEADLINE_EXCEEDED, even at 25s+) whenever system_instruction was set,
# in live testing against the real API -- gemini-3.5-flash-lite answered
# the same prompt correctly in ~3-8s, is explicitly free-tier and
# recommended for new projects, so it's the default here instead.
# Override via GEMINI_MODEL in .env or .env.local if Google renames/retires this model.
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-3.5-flash-lite")

# GEMINI_API_KEY is a secret: read from a real env var or .env.local only
# (never from .env, never written anywhere by this app).
GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or _env_local_values.get("GEMINI_API_KEY") or "").strip() or None

# Target ~8s for Gemini. Gemini's API itself rejects any deadline below 10s
# outright (INVALID_ARGUMENT), so gemini_chatbot.py floors whatever is
# configured here at that 10s minimum before sending it.
GEMINI_TIMEOUT_SECONDS = float(_get("GEMINI_TIMEOUT_SECONDS", "8"))

# Target ~5s for Bedrock (applied as both connect and read timeout).
BEDROCK_TIMEOUT_SECONDS = float(_get("BEDROCK_TIMEOUT_SECONDS", "5"))

# --- Deployment-mode flags (both default to localhost behavior) ---
# LOCAL_ML_ENABLED=false (set by the Lambda deployment) skips the local
# PyTorch model entirely and goes straight to Rekognition -- the local
# model isn't shipped to Lambda at all in this phase.
LOCAL_ML_ENABLED = _get("LOCAL_ML_ENABLED", "true").strip().lower() not in ("false", "0", "no")

# SESSION_HTTPS_ONLY=true (set by the Lambda deployment, where CloudFront
# terminates TLS) marks the session cookie Secure; stays False for the
# plain-http localhost server.
SESSION_HTTPS_ONLY = _get("SESSION_HTTPS_ONLY", "false").strip().lower() in ("true", "1", "yes")

# --- local session secret (NOT an AWS credential, NOT a Gemini key) ---
# Generated once on first run and persisted to .env so logged-in sessions
# survive server restarts. This is only used to sign the local browser
# session cookie; it is never sent to AWS or Google.
SESSION_SECRET = _get("SESSION_SECRET")
if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_hex(32)
    try:
        upsert_env_file(ENV_PATH, {"SESSION_SECRET": SESSION_SECRET})
    except OSError:
        pass


def cognito_configured() -> bool:
    return bool(COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID)


def startup_status_lines() -> list[str]:
    """
    One-line-per-provider status for startup logging. Reports only
    "set"/"not set" for keys -- never the value itself.
    """
    return [
        f"Gemini key: {'set' if GEMINI_API_KEY else 'not set'}, model: {GEMINI_MODEL}",
        f"Bedrock model: {BEDROCK_MODEL_ID} (region: {BEDROCK_REGION})",
        f"Chatbot provider mode: {CHATBOT_PROVIDER}",
        f"Cognito configured: {'yes' if cognito_configured() else 'no'}",
    ]
