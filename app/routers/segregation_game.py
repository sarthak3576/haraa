import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.services.segregation_game_data import BIN_LABELS, GAME_BINS, GAME_ITEMS
from app.services.segregation_game_service import get_best_score, submit_score
from app.templating import templates

router = APIRouter()


class ScoreSubmission(BaseModel):
    score: int


@router.get("/segregation-game", response_class=HTMLResponse)
def segregation_game_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    try:
        best_score = get_best_score(user_email)
    except Exception:  # noqa: BLE001
        best_score = 0

    return templates.TemplateResponse(request, "segregation_game.html", {
        "request": request,
        "bins": GAME_BINS,
        "bin_labels": BIN_LABELS,
        "items_json": json.dumps(GAME_ITEMS),
        "best_score": best_score,
    })


@router.post("/api/segregation-game/score")
def submit_game_score(request: Request, payload: ScoreSubmission):
    user_email = request.session.get("user_email")
    if not user_email:
        return JSONResponse({"error": "not authenticated"}, status_code=401)

    score = max(0, min(payload.score, len(GAME_ITEMS)))  # clamp to a sane range
    try:
        best = submit_score(user_email, score)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": f"Couldn't save your score right now: {exc}", "best_score": score}, status_code=200)
    return JSONResponse({"best_score": best})
