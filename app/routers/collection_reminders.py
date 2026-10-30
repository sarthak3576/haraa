from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.services.collection_reminder_service import (
    WEEKDAY_NAMES,
    build_ics,
    get_collection_days,
    get_reminder_banner,
    save_collection_days,
)
from app.templating import templates

router = APIRouter()


@router.get("/collection-reminders", response_class=HTMLResponse)
def collection_reminders_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    error = None
    collection_days = {"wet_days": [], "dry_days": []}
    try:
        collection_days = get_collection_days(user_email)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    return templates.TemplateResponse(request, "collection_reminders.html", {
        "request": request,
        "weekday_names": list(enumerate(WEEKDAY_NAMES)),
        "collection_days": collection_days,
        "banner": get_reminder_banner(collection_days) if not error else None,
        "error": error,
    })


@router.post("/collection-reminders", response_class=HTMLResponse)
def save_reminders(request: Request, wet_days: list[int] = Form(default=[]), dry_days: list[int] = Form(default=[])):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)
    try:
        save_collection_days(user_email, wet_days, dry_days)
    except Exception:  # noqa: BLE001
        pass  # the settings page itself reports load errors; avoid a hard crash here
    return RedirectResponse("/collection-reminders", status_code=303)


@router.get("/collection-reminders/calendar.ics")
def download_ics(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    collection_days = get_collection_days(user_email)
    ics_content = build_ics(user_email, collection_days)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=waste-collection.ics"},
    )
