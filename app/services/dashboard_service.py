import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from app import config
from app.aws_clients import get_dynamodb_resource
from app.services.waste_categories import ALL_CATEGORIES, CO2_SAVED_PER_KG

STATS_PK, STATS_SK = "STATS", "TOTAL"


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def log_waste_event(category: str, weight_kg: float, user_email: str,
                     source: str, confidence: float = 0.0) -> None:
    """
    Writes an immutable event row and atomically bumps the running totals
    in the single STATS/TOTAL aggregate row so the dashboard can be read
    with one GetItem instead of scanning the whole table.
    """
    table = _table()
    now = datetime.now(timezone.utc)
    co2_saved = round(weight_kg * CO2_SAVED_PER_KG.get(category, CO2_SAVED_PER_KG["other"]), 3)

    table.put_item(Item={
        "PK": "EVENT",
        "SK": f"{now.isoformat()}#{uuid.uuid4().hex[:8]}",
        "category": category,
        "weight_kg": Decimal(str(weight_kg)),
        "co2_saved_kg": Decimal(str(co2_saved)),
        "user_email": user_email,
        "source": source,
        "confidence": Decimal(str(confidence)),
        "created_at": now.isoformat(),
    })

    table.update_item(
        Key={"PK": STATS_PK, "SK": STATS_SK},
        UpdateExpression=(
            "ADD total_items :one, "
            f"cat_{category}_kg :w, "
            "total_kg :w, "
            "total_co2_saved_kg :co2"
        ),
        ExpressionAttributeValues={
            ":one": 1,
            ":w": Decimal(str(weight_kg)),
            ":co2": Decimal(str(co2_saved)),
        },
    )


def get_dashboard_stats() -> dict:
    table = _table()
    result = table.get_item(Key={"PK": STATS_PK, "SK": STATS_SK})
    item = result.get("Item", {})

    by_category = {
        cat: float(item.get(f"cat_{cat}_kg", 0)) for cat in ALL_CATEGORIES
    }

    return {
        "total_items": int(item.get("total_items", 0)),
        "total_kg": float(item.get("total_kg", 0)),
        "total_co2_saved_kg": float(item.get("total_co2_saved_kg", 0)),
        "by_category_kg": by_category,
    }


def _parse_events(items: list[dict]) -> list[dict]:
    events = []
    for item in items:
        events.append({
            "category": item.get("category"),
            "weight_kg": float(item.get("weight_kg", 0)),
            "co2_saved_kg": float(item.get("co2_saved_kg", 0)),
            "user_email": item.get("user_email"),
            "source": item.get("source"),
            "created_at": item.get("created_at"),
        })
    return events


def get_recent_events(limit: int = 10) -> list[dict]:
    table = _table()
    result = table.query(
        KeyConditionExpression=Key("PK").eq("EVENT"),
        ScanIndexForward=False,
        Limit=limit,
    )
    return _parse_events(result.get("Items", []))


def get_all_events(max_items: int = 1000) -> list[dict]:
    """Fine at demo scale: a single query against the EVENT partition."""
    table = _table()
    items, last_key = [], None
    while len(items) < max_items:
        kwargs = {"KeyConditionExpression": Key("PK").eq("EVENT"), "ScanIndexForward": False}
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        result = table.query(**kwargs)
        items.extend(result.get("Items", []))
        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            break
    return _parse_events(items[:max_items])


def get_daily_category_series(events: list[dict]) -> dict:
    """Returns {dates: [...], categories: {cat: [kg per date]}} for a stacked trend chart."""
    by_date_cat: dict = {}
    for e in events:
        date = (e["created_at"] or "")[:10]
        if not date:
            continue
        by_date_cat.setdefault(date, {}).setdefault(e["category"], 0.0)
        by_date_cat[date][e["category"]] += e["weight_kg"]

    dates = sorted(by_date_cat.keys())
    categories = {cat: [round(by_date_cat.get(d, {}).get(cat, 0.0), 2) for d in dates] for cat in ALL_CATEGORIES}
    return {"dates": dates, "categories": categories}


def get_leaderboard(events: list[dict], top_n: int = 5) -> list[dict]:
    totals: dict = {}
    for e in events:
        email = e.get("user_email") or "unknown"
        totals[email] = totals.get(email, 0.0) + e["weight_kg"]

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    leaderboard = []
    for email, kg in ranked:
        prefix = email.split("@")[0] if "@" in email else email
        leaderboard.append({"user_prefix": prefix, "total_kg": round(kg, 2)})
    return leaderboard


def get_streak_days(events: list[dict], user_email: str) -> int:
    """Consecutive days (ending today, UTC) with at least one logged event for this user."""
    user_dates = {
        (e["created_at"] or "")[:10]
        for e in events
        if e.get("user_email") == user_email and e["created_at"]
    }
    if not user_dates:
        return 0

    streak = 0
    day = datetime.now(timezone.utc).date()
    from datetime import timedelta
    while day.isoformat() in user_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_recycling_rate(stats: dict) -> float:
    """Share of logged waste (by item count proxy via kg) that wasn't classified 'other'."""
    total = stats["total_kg"]
    if total <= 0:
        return 0.0
    other_kg = stats["by_category_kg"].get("other", 0.0)
    return round((total - other_kg) / total * 100, 1)
