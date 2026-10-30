from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templating import templates

router = APIRouter()


@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "about.html", {"request": request})
