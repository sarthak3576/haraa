"""
Badges and 7-day challenges are computed on the fly from existing
dashboard events and stats (no extra state needed). The weekly goal is
the one piece of state a user sets themselves, stored per-user in the
same DynamoDB table as everything else.
"""
from datetime import datetime, timedelta, timezone

from app import config
from app.aws_clients import get_dynamodb_resource

GOAL_SK = "WEEKLY"


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def set_weekly_goal_items(user_email: str, target_items: int) -> None:
    _table().put_item(Item={
        "PK": f"GOAL#{user_email}",
        "SK": GOAL_SK,
        "target_items": target_items,
    })


def get_weekly_goal_items(user_email: str, default: int = 5) -> int:
    result = _table().get_item(Key={"PK": f"GOAL#{user_email}", "SK": GOAL_SK})
    item = result.get("Item")
    return int(item["target_items"]) if item else default


def _events_in_last_days(events: list[dict], user_email: str, days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for e in events:
        if e.get("user_email") != user_email or not e.get("created_at"):
            continue
        try:
            created = datetime.fromisoformat(e["created_at"])
        except ValueError:
            continue
        if created >= cutoff:
            out.append(e)
    return out


def get_weekly_progress(events: list[dict], user_email: str, goal_items: int) -> dict:
    week_events = _events_in_last_days(events, user_email, 7)
    items_logged = len(week_events)
    return {
        "goal_items": goal_items,
        "items_logged": items_logged,
        "progress_pct": min(100, round(items_logged / goal_items * 100)) if goal_items > 0 else 0,
        "met": items_logged >= goal_items,
    }


def get_challenges(events: list[dict], user_email: str, streak_days: int) -> list[dict]:
    week_events = _events_in_last_days(events, user_email, 7)
    plastic_count = sum(1 for e in week_events if e.get("category") == "plastic")

    return [
        {
            "title": "Plastic-free week",
            "description": "Go 7 days without logging any plastic waste.",
            "progress": f"{len(week_events)} items logged, {plastic_count} of them plastic",
            "completed": len(week_events) > 0 and plastic_count == 0,
        },
        {
            "title": "Log every day",
            "description": "Log at least one item every day for 7 days in a row.",
            "progress": f"{streak_days}-day streak",
            "completed": streak_days >= 7,
        },
        {
            "title": "Five in a week",
            "description": "Log at least 5 items within 7 days.",
            "progress": f"{len(week_events)} of 5 items",
            "completed": len(week_events) >= 5,
        },
    ]


def get_badges(stats: dict, streak_days: int, challenges: list[dict]) -> list[dict]:
    total_items = stats.get("total_items", 0)
    total_kg = stats.get("total_kg", 0.0)

    badges = [
        {"title": "First Scan", "description": "Logged your first item.", "earned": total_items >= 1},
        {"title": "Getting Started", "description": "Logged 10 items.", "earned": total_items >= 10},
        {"title": "Half Century", "description": "Logged 50 items.", "earned": total_items >= 50},
        {"title": "Century Club", "description": "Logged 100 items.", "earned": total_items >= 100},
        {"title": "Recycling Rookie", "description": "Diverted 5 kg of waste.", "earned": total_kg >= 5},
        {"title": "Green Champion", "description": "Diverted 20 kg of waste.", "earned": total_kg >= 20},
        {"title": "Week Warrior", "description": "A 7-day logging streak.", "earned": streak_days >= 7},
    ]
    for challenge in challenges:
        if challenge["completed"]:
            badges.append({"title": challenge["title"], "description": challenge["description"], "earned": True})

    return badges
