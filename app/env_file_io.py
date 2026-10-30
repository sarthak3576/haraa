"""
The ONLY code in this project allowed to write to a .env-style file.
Both app/config.py (for the auto-generated SESSION_SECRET) and
scripts/setup_aws.py (for Cognito/DynamoDB resource IDs) go through
upsert_env_file() here, so there is exactly one read-modify-write path to
audit.

Guarantees:
  - Reads the file first, then writes back every existing line (including
    comments and blank lines) untouched, except the specific keys passed in.
  - Only the keys named in `values` are added/changed; everything else in
    the file is preserved exactly.
  - Refuses to write anything that looks like a secret (API keys, AWS
    credentials) -- those belong in .env.local, edited by the user only.
"""
from pathlib import Path

# Key name patterns this function will never write, as a safety net against
# accidentally persisting a secret from application code.
_FORBIDDEN_KEY_MARKERS = ("API_KEY", "SECRET_ACCESS_KEY", "ACCESS_KEY_ID", "_TOKEN", "_PASSWORD")
# SESSION_SECRET is a local cookie-signing secret this app generates and
# manages itself (never an external credential), so it's explicitly allowed.
_ALLOWED_EXCEPTIONS = {"SESSION_SECRET"}


def _is_forbidden(key: str) -> bool:
    if key in _ALLOWED_EXCEPTIONS:
        return False
    return any(marker in key.upper() for marker in _FORBIDDEN_KEY_MARKERS)


def upsert_env_file(path: Path, values: dict[str, str]) -> None:
    forbidden = [k for k in values if _is_forbidden(k)]
    if forbidden:
        raise ValueError(
            f"Refusing to write secret-looking key(s) to {path.name}: {forbidden}. "
            "Secrets belong in .env.local, edited by the user only."
        )

    lines = path.read_text().splitlines() if path.exists() else []
    seen: set[str] = set()
    updated_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in values:
                updated_lines.append(f"{key}={values[key]}")
                seen.add(key)
                continue
        updated_lines.append(line)

    for key, value in values.items():
        if key not in seen:
            updated_lines.append(f"{key}={value}")

    text = "\n".join(updated_lines)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text)
