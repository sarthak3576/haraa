"""
Rule-based offline assistant used whenever every online provider (Gemini,
Bedrock) is unavailable or not configured. Draws on the shared 120+-item
household waste database (app/services/waste_items_data.py -- the same
one the "Where does it go?" search page uses), each with which bin it
goes in (the Indian wet/dry/hazardous/e-waste/biomedical system), short
step-by-step advice, and a "do not" note.

Matching is deliberately conservative: a bare generic word like "waste",
"garbage", "trash", or "rubbish" is never enough on its own to pick a
topic (that was a real bug: a question like "how much waste is produced
globally" was matching "e-waste" purely because "waste" is a substring of
it). A match must come from a specific, non-generic keyword, either by
exact substring or close fuzzy match. If nothing matches confidently, the
assistant says so plainly, suggests the closest topics it does know, and
-- for questions that sound like they want statistics or current events --
says plainly that this needs the online assistant.
"""
import difflib
import re

from app.services.waste_items_data import WASTE_ITEMS as TOPICS

GENERIC_WORDS = {
    "waste", "wastes", "garbage", "trash", "rubbish", "junk",
    "item", "items", "thing", "things", "stuff", "material", "materials",
    "dispose", "disposal", "throw", "away", "bin", "bins",
}

STATS_HINTS = {
    "how much", "percent", "percentage", "statistics", "stats", "data",
    "global", "globally", "world", "worldwide", "average", "per capita",
    "trend", "report", "study", "survey", "ranking", "rank", "compare",
    "latest", "news", "current",
}

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_WORD_RE = re.compile(r"[a-z0-9]+")


# Pre-tokenized, generic-word-free vocabulary used for fuzzy matching.
_FUZZY_VOCAB: dict[str, int] = {}
for _idx, _topic in enumerate(TOPICS):
    for _kw in _topic["keywords"]:
        for _word in _WORD_RE.findall(_kw.lower()):
            if _word not in GENERIC_WORDS and len(_word) >= 4:
                _FUZZY_VOCAB.setdefault(_word, _idx)


def _format_topic(topic: dict) -> str:
    lines = [f"{topic['title']} -- {topic['bin']}.", ""]
    lines.extend(f"- {step}" for step in topic["steps"])
    lines.append("")
    lines.append(topic["do_not"])
    return "\n".join(lines)


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _looks_like_stats_question(lower_message: str) -> bool:
    if _YEAR_RE.search(lower_message):
        return True
    return any(hint in lower_message for hint in STATS_HINTS)


def _closest_topics(lower_message: str, n: int = 3) -> list[str]:
    words = [w for w in _tokenize(lower_message) if w not in GENERIC_WORDS and len(w) >= 3]
    if not words:
        return [t["title"] for t in TOPICS[:n]]

    scores: dict[int, float] = {}
    for idx, topic in enumerate(TOPICS):
        topic_text = " ".join(topic["keywords"]).lower()
        best = max(
            (difflib.SequenceMatcher(None, w, tw).ratio()
             for w in words for tw in _tokenize(topic_text)),
            default=0.0,
        )
        scores[idx] = best

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [TOPICS[idx]["title"] for idx, _ in ranked[:n]]


def _substring_match(lower_message: str) -> dict | None:
    for topic in TOPICS:
        for keyword in topic["keywords"]:
            if keyword in GENERIC_WORDS:
                continue
            if keyword in lower_message:
                return topic
    return None


def _fuzzy_match(lower_message: str) -> dict | None:
    words = [w for w in set(_tokenize(lower_message)) if w not in GENERIC_WORDS and len(w) >= 4]
    words.sort(key=len, reverse=True)

    for word in words:
        matches = difflib.get_close_matches(word, _FUZZY_VOCAB.keys(), n=1, cutoff=0.84)
        if matches:
            return TOPICS[_FUZZY_VOCAB[matches[0]]]
    return None


def fallback_reply(message: str) -> str:
    """Returns the plain reply text. No provider/notice text is embedded --
    the UI shows a separate, subtle 'Offline mode' badge when needed."""
    lower = message.lower()

    topic = _substring_match(lower) or _fuzzy_match(lower)
    if topic:
        return _format_topic(topic)

    suggestions = _closest_topics(lower)
    suggestion_text = "; ".join(suggestions)

    if _looks_like_stats_question(lower):
        return (
            "I can't look up live statistics or current events offline. "
            "Ask the online assistant for that.\n\n"
            f"Meanwhile, I can help with: {suggestion_text}."
        )

    return (
        "I'm not confident enough to answer that one offline.\n\n"
        f"Did you mean one of these: {suggestion_text}?"
    )
