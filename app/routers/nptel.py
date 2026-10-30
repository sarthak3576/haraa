from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.nptel_data import NPTEL_COURSES, NPTEL_NOTE
from app.templating import templates

router = APIRouter()


@router.get("/nptel", response_class=HTMLResponse)
def nptel_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "nptel.html", {
        "request": request,
        "courses": NPTEL_COURSES,
        "note": NPTEL_NOTE,
    })
