from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.disposal_guide_data import DISPOSAL_GUIDE
from app.services.nearby_centres_data import DASHBOARD_CATEGORY_TO_NEARBY_ID
from app.templating import templates

router = APIRouter()


@router.get("/disposal-guide", response_class=HTMLResponse)
def disposal_guide_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "disposal_guide.html", {
        "request": request,
        "guide": DISPOSAL_GUIDE,
        "nearby_map": DASHBOARD_CATEGORY_TO_NEARBY_ID,
    })
