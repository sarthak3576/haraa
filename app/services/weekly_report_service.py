from datetime import datetime, timedelta, timezone


def _window_totals(events: list[dict], user_email: str, days_back_start: int, days_back_end: int) -> dict:
    """Totals for events with (now - days_back_start) <= created_at < (now - days_back_end)."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days_back_start)
    window_end = now - timedelta(days=days_back_end)

    items, kg, co2 = 0, 0.0, 0.0
    by_category: dict[str, float] = {}

    for e in events:
        if e.get("user_email") != user_email or not e.get("created_at"):
            continue
        try:
            created = datetime.fromisoformat(e["created_at"])
        except ValueError:
            continue
        if window_start <= created < window_end:
            items += 1
            kg += e.get("weight_kg", 0.0)
            co2 += e.get("co2_saved_kg", 0.0)
            cat = e.get("category", "other")
            by_category[cat] = by_category.get(cat, 0.0) + e.get("weight_kg", 0.0)

    return {"items": items, "kg": round(kg, 2), "co2": round(co2, 2), "by_category": by_category}


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None  # avoid a misleading infinite/undefined percentage when there's no baseline
    return round((current - previous) / previous * 100, 1)


def build_weekly_report(events: list[dict], user_email: str) -> dict:
    this_week = _window_totals(events, user_email, days_back_start=7, days_back_end=0)
    last_week = _window_totals(events, user_email, days_back_start=14, days_back_end=7)

    return {
        "this_week": this_week,
        "last_week": last_week,
        "items_change_pct": _pct_change(this_week["items"], last_week["items"]),
        "kg_change_pct": _pct_change(this_week["kg"], last_week["kg"]),
        "co2_change_pct": _pct_change(this_week["co2"], last_week["co2"]),
    }
