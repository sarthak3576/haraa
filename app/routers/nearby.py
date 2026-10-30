from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.nearby_centres_data import NEARBY_CATEGORIES
from app.templating import templates

router = APIRouter()


@router.get("/nearby-centres", response_class=HTMLResponse)
def nearby_centres_page(request: Request, category: str = ""):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "nearby.html", {
        "request": request,
        "categories": NEARBY_CATEGORIES,
        "preselected_category": category,
    })
