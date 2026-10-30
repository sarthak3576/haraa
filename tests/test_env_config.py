"""
Tests for the env-loading precedence (real env > .env.local > .env, blank
doesn't hide a real value) and the shared env-file writer that guarantees
every unrelated line is preserved and refuses to write secret-looking keys.
"""
import os

import pytest

from app import config
from app.env_file_io import upsert_env_file


@pytest.fixture
def clean_env(monkeypatch):
    """Isolate app.config's module-level env dicts so tests don't depend on
    (or affect) this machine's real .env / .env.local / shell env."""
    monkeypatch.setattr(config, "_env_values", {})
    monkeypatch.setattr(config, "_env_local_values", {})
    for key in ("WM_TEST_KEY",):
        monkeypatch.delenv(key, raising=False)
    yield


def test_get_prefers_real_env_var_over_files(clean_env, monkeypatch):
    monkeypatch.setenv("WM_TEST_KEY", "from-real-env")
    monkeypatch.setattr(config, "_env_local_values", {"WM_TEST_KEY": "from-env-local"})
    monkeypatch.setattr(config, "_env_values", {"WM_TEST_KEY": "from-env"})
    assert config._get("WM_TEST_KEY") == "from-real-env"


def test_get_prefers_env_local_over_env(clean_env, monkeypatch):
    monkeypatch.setattr(config, "_env_local_values", {"WM_TEST_KEY": "from-env-local"})
    monkeypatch.setattr(config, "_env_values", {"WM_TEST_KEY": "from-env"})
    assert config._get("WM_TEST_KEY") == "from-env-local"


def test_get_falls_back_to_env_file(clean_env, monkeypatch):
    monkeypatch.setattr(config, "_env_values", {"WM_TEST_KEY": "from-env"})
    assert config._get("WM_TEST_KEY") == "from-env"


def test_blank_real_env_var_does_not_hide_env_local_value(clean_env, monkeypatch):
    monkeypatch.setenv("WM_TEST_KEY", "")  # set but blank
    monkeypatch.setattr(config, "_env_local_values", {"WM_TEST_KEY": "from-env-local"})
    assert config._get("WM_TEST_KEY") == "from-env-local"


def test_blank_env_local_value_does_not_hide_env_file_value(clean_env, monkeypatch):
    monkeypatch.setattr(config, "_env_local_values", {"WM_TEST_KEY": ""})
    monkeypatch.setattr(config, "_env_values", {"WM_TEST_KEY": "from-env"})
    assert config._get("WM_TEST_KEY") == "from-env"


def test_get_returns_default_when_nothing_set(clean_env):
    assert config._get("WM_TEST_KEY", "fallback") == "fallback"


# ---------- upsert_env_file ----------

def test_upsert_env_file_preserves_unrelated_lines(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "# a comment\n"
        "\n"
        "AWS_REGION=ap-south-1\n"
        "COGNITO_USER_POOL_ID=old-pool\n"
        "\n"
        "# another comment\n"
        "DYNAMODB_TABLE_NAME=WasteMgmt\n"
    )

    upsert_env_file(env_path, {"COGNITO_USER_POOL_ID": "new-pool", "COGNITO_CLIENT_ID": "new-client"})

    content = env_path.read_text()
    lines = content.splitlines()

    assert "# a comment" in lines
    assert "# another comment" in lines
    assert "AWS_REGION=ap-south-1" in lines
    assert "DYNAMODB_TABLE_NAME=WasteMgmt" in lines
    assert "COGNITO_USER_POOL_ID=new-pool" in lines
    assert "COGNITO_USER_POOL_ID=old-pool" not in lines
    assert "COGNITO_CLIENT_ID=new-client" in lines
    # blank lines preserved (3 blank-ish boundaries from the original content)
    assert content.count("\n\n") >= 1


def test_upsert_env_file_creates_file_if_missing(tmp_path):
    env_path = tmp_path / ".env"
    upsert_env_file(env_path, {"SESSION_SECRET": "abc123"})
    assert "SESSION_SECRET=abc123" in env_path.read_text()


def test_upsert_env_file_refuses_secret_like_keys(tmp_path):
    env_path = tmp_path / ".env"
    for bad_key in ["GEMINI_API_KEY", "AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "SOME_TOKEN", "DB_PASSWORD"]:
        with pytest.raises(ValueError):
            upsert_env_file(env_path, {bad_key: "whatever"})
    assert not env_path.exists() or env_path.read_text() == ""


def test_upsert_env_file_allows_session_secret(tmp_path):
    env_path = tmp_path / ".env"
    upsert_env_file(env_path, {"SESSION_SECRET": "deadbeef"})
    assert "SESSION_SECRET=deadbeef" in env_path.read_text()


def test_upsert_env_file_does_not_touch_file_when_rejected(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("EXISTING=value\n")
    with pytest.raises(ValueError):
        upsert_env_file(env_path, {"GEMINI_API_KEY": "leak-attempt"})
    assert env_path.read_text() == "EXISTING=value\n"


# ---------- startup status lines never include secret values ----------

def test_startup_status_lines_never_include_the_key_value(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "super-secret-value-12345")
    lines = config.startup_status_lines()
    joined = " ".join(lines)
    assert "super-secret-value-12345" not in joined
    assert "set" in joined.lower()


def test_startup_status_lines_report_not_set_when_missing(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    lines = config.startup_status_lines()
    assert any("not set" in line for line in lines)
