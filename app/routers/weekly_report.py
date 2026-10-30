from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.dashboard_service import get_all_events
from app.services.weekly_report_service import build_weekly_report
from app.templating import templates

router = APIRouter()


@router.get("/weekly-report", response_class=HTMLResponse)
def weekly_report_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    error = None
    report = None
    try:
        events = get_all_events()
        report = build_weekly_report(events, user_email)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    return templates.TemplateResponse(request, "weekly_report.html", {
        "request": request,
        "user_email": user_email,
        "report": report,
        "error": error,
    })
