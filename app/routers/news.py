from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.rss_news import FEEDS, get_articles
from app.templating import templates

router = APIRouter()


@router.get("/news", response_class=HTMLResponse)
def news_page(request: Request):
    if not request.session.get("user_email"):
        return RedirectResponse("/login", status_code=303)

    data = get_articles()
    topics = sorted({a["topic"] for a in data["articles"]})

    return templates.TemplateResponse(request, "news.html", {
        "request": request,
        "articles": data["articles"],
        "is_fallback": data["is_fallback"],
        "topics": topics,
        "feed_count": len(FEEDS),
    })
