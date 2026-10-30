import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.services.learn_content import LEARN_SECTIONS, get_section
from app.services.learn_progress import get_user_quiz_progress, submit_quiz_score
from app.templating import templates

router = APIRouter()


class QuizSubmission(BaseModel):
    section_id: str
    answers: list[int]


@router.get("/learn", response_class=HTMLResponse)
def learn_page(request: Request):
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse("/login", status_code=303)

    try:
        progress = get_user_quiz_progress(user_email)
    except Exception:  # noqa: BLE001
        progress = {}

    # strip answer keys before sending quiz data to the client; the
    # server grades answers in /api/learn/quiz instead
    client_sections = [
        {
            **section,
            "quiz": [{"q": q["q"], "options": q["options"]} for q in section["quiz"]],
        }
        for section in LEARN_SECTIONS
    ]

    return templates.TemplateResponse(request, "learn.html", {
        "request": request,
        "sections": LEARN_SECTIONS,
        "sections_json": json.dumps(client_sections),
        "progress": progress,
    })


@router.post("/api/learn/quiz")
def submit_quiz(request: Request, payload: QuizSubmission):
    user_email = request.session.get("user_email")
    if not user_email:
        return JSONResponse({"error": "not authenticated"}, status_code=401)

    section = get_section(payload.section_id)
    if not section:
        return JSONResponse({"error": "unknown section"}, status_code=404)

    questions = section["quiz"]
    score = sum(
        1 for i, q in enumerate(questions)
        if i < len(payload.answers) and payload.answers[i] == q["answer"]
    )
    total = len(questions)

    try:
        result = submit_quiz_score(user_email, payload.section_id, score, total)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": f"Could not save score: {exc}"}, status_code=500)

    return JSONResponse({
        "score": score,
        "total": total,
        "best_score": result["best_score"],
        "correct_answers": [q["answer"] for q in questions],
    })
