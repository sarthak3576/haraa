"""
A single shared Jinja2Templates instance for the whole app (instead of
each router creating its own), so template globals like icon() are
registered once and available everywhere.
"""
import re
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from app.services.i18n import LANGUAGE_LABELS, get_current_language, translate

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
ICONS_DIR = BASE_DIR / "static" / "icons"


def _inject_i18n(request: Request) -> dict:
    lang = get_current_language(request)
    return {
        "lang": lang,
        "language_labels": LANGUAGE_LABELS,
        "t": lambda key, **kwargs: translate(lang, key, **kwargs),
        # Cognito ID token already stashed at login (app/routers/auth.py) --
        # exposed here so page JS can call the deployed /api/v1/* JWT-authorized
        # endpoints with `Authorization: Bearer <token>`. Unused by the
        # server-rendered pages themselves, which stay cookie-session-authed.
        "api_id_token": request.session.get("id_token", ""),
    }


templates = Jinja2Templates(directory=str(TEMPLATES_DIR), context_processors=[_inject_i18n])

_icon_cache: dict[str, str] = {}
_SIZE_ATTR_RE = re.compile(r'\s(width|height)="\d+"')


def _load_icon(name: str) -> str:
    if name not in _icon_cache:
        path = ICONS_DIR / f"{name}.svg"
        svg = path.read_text() if path.exists() else ""
        svg = _SIZE_ATTR_RE.sub("", svg)
        _icon_cache[name] = svg
    return _icon_cache[name]


def icon(name: str, css_class: str = "icon") -> Markup:
    """Usage in templates: {{ icon("leaf") }} or {{ icon("camera", "icon-lg") }}."""
    svg = _load_icon(name)
    if not svg:
        return Markup("")
    svg = svg.replace("<svg", f'<svg class="{css_class}" aria-hidden="true"', 1)
    return Markup(svg)


templates.env.globals["icon"] = icon
