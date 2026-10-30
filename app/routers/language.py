from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services.i18n import SUPPORTED_LANGUAGES

router = APIRouter()


@router.get("/set-language/{lang}")
def set_language(request: Request, lang: str, next: str = "/home"):
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    request.session["lang"] = lang
    response = RedirectResponse(next, status_code=303)
    response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response
