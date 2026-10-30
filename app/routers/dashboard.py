import csv
import io
import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

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
    set_weekly_goal_items,
)
from app.templating import templates

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    error = None
    stats, events, recent_events = {}, [], []
    series, leaderboard, streak, recycling_rate = {"dates": [], "categories": {}}, [], 0, 0.0
    weekly_goal, challenges, badges = {}, [], []

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
        error = str(exc)

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "user_email": user_email,
        "stats": stats,
        "events": recent_events,
        "series_json": json.dumps(series),
        "leaderboard": leaderboard,
        "streak": streak,
        "recycling_rate": recycling_rate,
        "weekly_goal": weekly_goal,
        "challenges": challenges,
        "badges": badges,
        "error": error,
    })


@router.post("/dashboard/goal")
def set_goal(request: Request, target_items: int = Form(...)):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)
    try:
        set_weekly_goal_items(user_email, max(1, target_items))
    except Exception:  # noqa: BLE001
        pass  # the dashboard page itself reports load errors; avoid a hard crash here
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/dashboard/export.csv")
def export_csv(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    events = get_all_events()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["created_at", "category", "weight_kg", "co2_saved_kg", "source", "user_email"])
    for e in events:
        writer.writerow([e["created_at"], e["category"], e["weight_kg"], e["co2_saved_kg"], e["source"], e["user_email"]])
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=waste_events.csv"},
    )
