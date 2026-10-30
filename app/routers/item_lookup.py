from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.nearby_centres_data import DASHBOARD_CATEGORY_TO_NEARBY_ID
from app.services.waste_items_data import WASTE_ITEMS
from app.templating import templates

router = APIRouter()


@router.get("/where-does-it-go", response_class=HTMLResponse)
def item_lookup_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    categories = sorted({item["category"] for item in WASTE_ITEMS})
    return templates.TemplateResponse(request, "item_lookup.html", {
        "request": request,
        "items": WASTE_ITEMS,
        "categories": categories,
        "nearby_map": DASHBOARD_CATEGORY_TO_NEARBY_ID,
    })
