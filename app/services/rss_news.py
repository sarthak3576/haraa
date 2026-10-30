"""
Fetches recent waste-management articles from free Google News RSS feeds,
cached in-memory for an hour so the Articles & News page doesn't re-fetch
on every request. Falls back to the curated NEWS_LINKS list (see
news_data.py) if the feeds can't be reached or parsed.
"""
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from app.services.news_data import NEWS_LINKS

CACHE_TTL_SECONDS = 60 * 60
_cache: dict = {"timestamp": 0, "articles": None, "is_fallback": True}

FEEDS = [
    {
        "topic": "Waste Management (India)",
        "url": "https://news.google.com/rss/search?q=waste+management+india&hl=en-IN&gl=IN&ceid=IN:en",
    },
    {
        "topic": "Recycling & Circular Economy",
        "url": "https://news.google.com/rss/search?q=recycling+circular+economy&hl=en-IN&gl=IN&ceid=IN:en",
    },
    {
        "topic": "Plastic Waste & Pollution",
        "url": "https://news.google.com/rss/search?q=plastic+waste+pollution&hl=en-IN&gl=IN&ceid=IN:en",
    },
]

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; waste-mgmt-demo/1.0)"}


def _fetch_feed(url: str, timeout: int = 8) -> list[dict]:
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = item.findtext("pubDate")
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else "Google News"

        try:
            pub_date = parsedate_to_datetime(pub_date_raw) if pub_date_raw else None
        except (TypeError, ValueError):
            pub_date = None

        if title and link:
            items.append({
                "title": title,
                "url": link,
                "source": source,
                "published": pub_date.isoformat() if pub_date else None,
                "published_display": pub_date.strftime("%d %b %Y") if pub_date else "",
            })
    return items


def get_articles(force_refresh: bool = False) -> dict:
    """Returns {"articles": [...], "is_fallback": bool, "fetched_at": float}."""
    now = time.time()
    if not force_refresh and _cache["articles"] is not None and (now - _cache["timestamp"]) < CACHE_TTL_SECONDS:
        return _cache

    all_articles = []
    try:
        for feed in FEEDS:
            feed_items = _fetch_feed(feed["url"])
            for item in feed_items:
                item["topic"] = feed["topic"]
            all_articles.extend(feed_items)

        if not all_articles:
            raise ValueError("No articles returned from any feed")

        # de-duplicate by title, keep newest first
        seen_titles = set()
        deduped = []
        all_articles.sort(key=lambda a: a["published"] or "", reverse=True)
        for article in all_articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                deduped.append(article)

        _cache.update({"timestamp": now, "articles": deduped[:40], "is_fallback": False})

    except (urllib.error.URLError, ET.ParseError, ValueError, TimeoutError, OSError):
        fallback = [
            {
                "title": link["title"],
                "url": link["url"],
                "source": link["source"],
                "topic": "Curated reference",
                "published": None,
                "published_display": "",
            }
            for link in NEWS_LINKS
        ]
        _cache.update({"timestamp": now, "articles": fallback, "is_fallback": True})

    return _cache
