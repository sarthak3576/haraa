from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.dashboard_service import log_waste_event
from app.services.scan_history_service import get_recent_scans, get_scan, mark_scan_logged
from app.services.waste_categories import DEFAULT_WEIGHT_KG
from app.templating import templates

router = APIRouter()


@router.get("/my-scans", response_class=HTMLResponse)
def my_scans_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    error = None
    scans = []
    try:
        scans = get_recent_scans(user_email)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    return templates.TemplateResponse(request, "my_scans.html", {
        "request": request,
        "scans": scans,
        "error": error,
        "default_weight": DEFAULT_WEIGHT_KG,
    })


@router.post("/my-scans/log", response_class=HTMLResponse)
def log_scan(request: Request, scan_id: str = Form(...), weight_kg: float = Form(...)):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    try:
        scan = get_scan(user_email, scan_id)
        if scan and not scan["logged"]:
            log_waste_event(
                category=scan["category"],
                weight_kg=weight_kg,
                user_email=user_email,
                source="photo",
                confidence=scan["confidence"],
            )
            mark_scan_logged(user_email, scan_id)
    except Exception:  # noqa: BLE001
        pass  # the scans page itself reports load errors; avoid a hard crash here

    return RedirectResponse("/my-scans", status_code=303)
