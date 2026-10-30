import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.templating import templates
from app.routers import (
    about,
    auth,
    calculator,
    chat,
    collection_reminders,
    composting_guide,
    dashboard,
    disposal_guide,
    home,
    item_lookup,
    language,
    learn,
    model_performance,
    my_scans,
    nearby,
    news,
    nptel,
    poster,
    segregation_game,
    upload,
    waste_audit,
    weekly_report,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("waste_mgmt.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    for line in config.startup_status_lines():
        logger.info(line)
    yield

app = FastAPI(title="Haraa", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    same_site="lax",
    https_only=config.SESSION_HTTPS_ONLY,  # true behind CloudFront/TLS, false on plain-http localhost
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(language.router)
app.include_router(home.router)
app.include_router(learn.router)
app.include_router(nptel.router)
app.include_router(news.router)
app.include_router(dashboard.router)
app.include_router(calculator.router)
app.include_router(upload.router)
app.include_router(disposal_guide.router)
app.include_router(item_lookup.router)
app.include_router(nearby.router)
app.include_router(my_scans.router)
app.include_router(waste_audit.router)
app.include_router(segregation_game.router)
app.include_router(collection_reminders.router)
app.include_router(composting_guide.router)
app.include_router(poster.router)
app.include_router(weekly_report.router)
app.include_router(chat.router)
app.include_router(model_performance.router)
app.include_router(about.router)


@app.get("/")
def root(request: Request):
    if request.session.get("user_email"):
        return RedirectResponse("/home")
    return RedirectResponse("/login")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.exception_handler(StarletteHTTPException)
async def not_found_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(request, "404.html", {"request": request}, status_code=404)
    raise exc
