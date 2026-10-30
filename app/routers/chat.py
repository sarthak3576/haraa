import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.services.chatbot_service import get_chat_reply, get_provider_health
from app.templating import templates

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)
    history = request.session.get("chat_history", [])
    return templates.TemplateResponse(request, "chat.html", {
        "request": request,
        "user_email": request.session.get("user_email"),
        "history_json": json.dumps(history),
    })


@router.post("/api/chat")
def chat_api(request: Request, payload: ChatRequest):
    if not request.session.get("user_email"):
        return JSONResponse({"error": "not authenticated"}, status_code=401)

    history = request.session.get("chat_history", [])
    result = get_chat_reply(payload.message, history)

    history.append({"role": "user", "content": payload.message})
    history.append({"role": "assistant", "content": result["reply"], "provider": result["provider"]})
    request.session["chat_history"] = history[-20:]

    return JSONResponse({
        "reply": result["reply"],
        "provider": result["provider"],
        "notes": result["notes"],
    })


@router.post("/api/chat/clear")
def chat_clear(request: Request):
    if not request.session.get("user_email"):
        return JSONResponse({"error": "not authenticated"}, status_code=401)
    request.session["chat_history"] = []
    return JSONResponse({"ok": True})


@router.get("/api/chatbot/health")
def chatbot_health(request: Request):
    if not request.session.get("user_email"):
        return JSONResponse({"error": "not authenticated"}, status_code=401)
    return JSONResponse(get_provider_health())
