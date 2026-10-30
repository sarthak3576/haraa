from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.services.impact_calculator import calculate_impact
from app.services.waste_categories import ALL_CATEGORIES
from app.templating import templates

router = APIRouter()


class CalculatorInput(BaseModel):
    amounts_kg: dict[str, float]


@router.get("/calculator", response_class=HTMLResponse)
def calculator_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "calculator.html", {
        "request": request,
        "categories": ALL_CATEGORIES,
    })


@router.post("/api/calculator")
def calculator_api(request: Request, payload: CalculatorInput):
    if not request.session.get("user_email"):
        return JSONResponse({"error": "not authenticated"}, status_code=401)
    result = calculate_impact(payload.amounts_kg)
    return JSONResponse(result)
