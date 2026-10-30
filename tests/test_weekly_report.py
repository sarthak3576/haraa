from datetime import datetime, timedelta, timezone

from app.services.weekly_report_service import build_weekly_report

USER = "reporter@example.com"


def _event(days_ago: float, weight_kg: float = 1.0, co2: float = 0.5, category: str = "plastic") -> dict:
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"created_at": created.isoformat(), "weight_kg": weight_kg, "co2_saved_kg": co2,
            "category": category, "user_email": USER}


def test_report_separates_this_week_from_last_week():
    events = [_event(1), _event(3), _event(10), _event(13)]
    report = build_weekly_report(events, USER)
    assert report["this_week"]["items"] == 2
    assert report["last_week"]["items"] == 2


def test_report_ignores_events_older_than_two_weeks():
    events = [_event(1), _event(20)]
    report = build_weekly_report(events, USER)
    assert report["this_week"]["items"] == 1
    assert report["last_week"]["items"] == 0


def test_report_ignores_other_users():
    events = [_event(1), {"created_at": datetime.now(timezone.utc).isoformat(), "weight_kg": 5,
                           "co2_saved_kg": 1, "category": "paper", "user_email": "other@example.com"}]
    report = build_weekly_report(events, USER)
    assert report["this_week"]["items"] == 1


def test_percent_change_is_none_without_baseline():
    events = [_event(1)]  # only this week, nothing last week
    report = build_weekly_report(events, USER)
    assert report["items_change_pct"] is None


def test_percent_change_computed_when_baseline_exists():
    events = [_event(1), _event(2), _event(10)]  # 2 this week, 1 last week
    report = build_weekly_report(events, USER)
    assert report["items_change_pct"] == 100.0


def test_by_category_breakdown_this_week():
    events = [_event(1, weight_kg=2.0, category="plastic"), _event(2, weight_kg=3.0, category="paper")]
    report = build_weekly_report(events, USER)
    assert report["this_week"]["by_category"] == {"plastic": 2.0, "paper": 3.0}
