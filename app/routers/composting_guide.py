from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.composting_guide_data import COMPOSTING_GUIDES
from app.templating import templates

router = APIRouter()


@router.get("/composting-guide", response_class=HTMLResponse)
def composting_guide_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "composting_guide.html", {
        "request": request,
        "guides": COMPOSTING_GUIDES,
    })
