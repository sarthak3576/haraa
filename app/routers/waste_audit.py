import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.waste_audit_data import AUDIT_QUESTIONS, MAX_SCORE
from app.templating import templates

router = APIRouter()


@router.get("/waste-audit", response_class=HTMLResponse)
def waste_audit_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "waste_audit.html", {
        "request": request,
        "questions": AUDIT_QUESTIONS,
        "questions_json": json.dumps(AUDIT_QUESTIONS),
        "max_score": MAX_SCORE,
        "user_email": request.session.get("user_email"),
    })
