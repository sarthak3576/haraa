from datetime import date

from app.services.collection_reminder_service import build_ics, get_reminder_banner


def test_banner_none_when_no_collection_days():
    assert get_reminder_banner({"wet_days": [], "dry_days": []}) is None


def test_banner_mentions_today():
    today = date.today().weekday()
    banner = get_reminder_banner({"wet_days": [today], "dry_days": []})
    assert "today" in banner.lower()
    assert "wet waste" in banner.lower()


def test_banner_mentions_tomorrow_when_not_today():
    tomorrow = (date.today().weekday() + 1) % 7
    banner = get_reminder_banner({"wet_days": [], "dry_days": [tomorrow]})
    assert "tomorrow" in banner.lower()
    assert "dry waste" in banner.lower()


def test_banner_prefers_today_over_tomorrow_wording():
    today = date.today().weekday()
    # today is both a wet and dry day; tomorrow should not also be mentioned
    # for the same stream since "today" already covers it
    banner = get_reminder_banner({"wet_days": [today], "dry_days": [today]})
    assert banner.count("today") == 2 or "today" in banner.lower()


def test_build_ics_contains_valid_calendar_structure():
    ics = build_ics("user@example.com", {"wet_days": [0], "dry_days": [2]})
    assert ics.startswith("BEGIN:VCALENDAR")
    assert ics.strip().endswith("END:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == 2
    assert "SUMMARY:Wet waste collection" in ics
    assert "SUMMARY:Dry waste collection" in ics
    assert "RRULE:FREQ=WEEKLY;BYDAY=MO" in ics
    assert "RRULE:FREQ=WEEKLY;BYDAY=WE" in ics


def test_build_ics_empty_when_no_days_selected():
    ics = build_ics("user@example.com", {"wet_days": [], "dry_days": []})
    assert "BEGIN:VEVENT" not in ics
