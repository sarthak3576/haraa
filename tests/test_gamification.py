from datetime import datetime, timedelta, timezone

from app.services.gamification_service import get_badges, get_challenges, get_weekly_progress

USER = "gamer@example.com"


def _event(days_ago: float, category: str = "plastic", weight_kg: float = 1.0) -> dict:
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {"created_at": created.isoformat(), "category": category, "weight_kg": weight_kg, "user_email": USER}


def test_weekly_progress_counts_only_last_7_days():
    events = [_event(1), _event(3), _event(10)]  # the 10-day-old one is outside the window
    progress = get_weekly_progress(events, USER, goal_items=5)
    assert progress["items_logged"] == 2
    assert progress["met"] is False


def test_weekly_progress_met_when_goal_reached():
    events = [_event(i) for i in range(5)]
    progress = get_weekly_progress(events, USER, goal_items=5)
    assert progress["met"] is True
    assert progress["progress_pct"] == 100


def test_weekly_progress_ignores_other_users_events():
    events = [_event(1)] + [{"created_at": datetime.now(timezone.utc).isoformat(), "category": "plastic",
                              "weight_kg": 1.0, "user_email": "someone-else@example.com"}]
    progress = get_weekly_progress(events, USER, goal_items=5)
    assert progress["items_logged"] == 1


def test_plastic_free_week_challenge_fails_with_plastic_logged():
    events = [_event(1, category="plastic")]
    challenges = get_challenges(events, USER, streak_days=1)
    plastic_free = next(c for c in challenges if c["title"] == "Plastic-free week")
    assert plastic_free["completed"] is False


def test_plastic_free_week_challenge_passes_without_plastic():
    events = [_event(1, category="paper"), _event(2, category="organic")]
    challenges = get_challenges(events, USER, streak_days=1)
    plastic_free = next(c for c in challenges if c["title"] == "Plastic-free week")
    assert plastic_free["completed"] is True


def test_log_every_day_challenge_needs_seven_day_streak():
    challenges = get_challenges([], USER, streak_days=7)
    log_daily = next(c for c in challenges if c["title"] == "Log every day")
    assert log_daily["completed"] is True

    challenges_short = get_challenges([], USER, streak_days=3)
    log_daily_short = next(c for c in challenges_short if c["title"] == "Log every day")
    assert log_daily_short["completed"] is False


def test_badges_first_scan_and_thresholds():
    stats = {"total_items": 1, "total_kg": 0.5}
    badges = get_badges(stats, streak_days=0, challenges=[])
    earned_titles = {b["title"] for b in badges if b["earned"]}
    assert "First Scan" in earned_titles
    assert "Getting Started" not in earned_titles  # needs 10 items


def test_badges_include_completed_challenges():
    challenges = [{"title": "Plastic-free week", "description": "x", "completed": True}]
    badges = get_badges({"total_items": 0, "total_kg": 0}, streak_days=0, challenges=challenges)
    assert any(b["title"] == "Plastic-free week" and b["earned"] for b in badges)
