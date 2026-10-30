"""
GET /api/v1/dashboard -- Cognito-JWT-authorized.
Same composition as app/routers/dashboard.py's dashboard_page, returned as
JSON instead of rendered HTML.
"""
import json

from app.services.dashboard_service import (
    get_all_events,
    get_dashboard_stats,
    get_daily_category_series,
    get_leaderboard,
    get_recent_events,
    get_recycling_rate,
    get_streak_days,
)
from app.services.gamification_service import (
    get_badges,
    get_challenges,
    get_weekly_goal_items,
    get_weekly_progress,
)


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_email = claims.get("email") or claims.get("cognito:username")
    if not user_email:
        return _response(401, {"error": "No email claim on the token."})

    try:
        stats = get_dashboard_stats()
        events = get_all_events()
        recent_events = get_recent_events()
        series = get_daily_category_series(events)
        leaderboard = get_leaderboard(events)
        streak = get_streak_days(events, user_email)
        recycling_rate = get_recycling_rate(stats)

        goal_target = get_weekly_goal_items(user_email)
        weekly_goal = get_weekly_progress(events, user_email, goal_target)
        challenges = get_challenges(events, user_email, streak)
        badges = get_badges(stats, streak, challenges)
    except Exception as exc:  # noqa: BLE001
        return _response(502, {"error": str(exc)})

    return _response(200, {
        "stats": stats,
        "recent_events": recent_events,
        "series": series,
        "leaderboard": leaderboard,
        "streak": streak,
        "recycling_rate": recycling_rate,
        "weekly_goal": weekly_goal,
        "challenges": challenges,
        "badges": badges,
    })
