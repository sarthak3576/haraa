from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.disposal_guide_data import DISPOSAL_GUIDE
from app.templating import templates

router = APIRouter()


@router.get("/poster", response_class=HTMLResponse)
def poster_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "poster.html", {
        "request": request,
        "guide": DISPOSAL_GUIDE,
    })
