from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.collection_reminder_service import get_collection_days, get_reminder_banner
from app.services.dashboard_service import get_dashboard_stats
from app.templating import templates

router = APIRouter()


@router.get("/home", response_class=HTMLResponse)
def home_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    try:
        stats = get_dashboard_stats()
    except Exception:  # noqa: BLE001
        stats = {"total_items": 0, "total_kg": 0, "total_co2_saved_kg": 0}

    banner = None
    try:
        banner = get_reminder_banner(get_collection_days(user_email))
    except Exception:  # noqa: BLE001
        pass

    return templates.TemplateResponse(request, "home.html", {
        "request": request,
        "stats": stats,
        "collection_banner": banner,
    })
