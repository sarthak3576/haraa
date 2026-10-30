from app.services.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, translate


def test_every_english_key_has_a_tamil_translation():
    en_keys = set(TRANSLATIONS["en"].keys())
    ta_keys = set(TRANSLATIONS["ta"].keys())
    assert en_keys == ta_keys, f"missing Tamil keys: {en_keys - ta_keys}, extra: {ta_keys - en_keys}"


def test_translate_falls_back_to_english_for_unknown_key():
    assert translate("ta", "nonexistent.key") == "nonexistent.key"


def test_translate_formats_placeholders():
    text = translate("en", "lookup.subtitle", count=42)
    assert "42" in text


def test_translate_defaults_unsupported_language_to_english():
    assert translate("fr", "nav.home") == TRANSLATIONS["en"]["nav.home"]


def test_supported_languages_include_english_and_tamil():
    assert "en" in SUPPORTED_LANGUAGES
    assert "ta" in SUPPORTED_LANGUAGES
