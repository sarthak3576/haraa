"""
Lets a user record which weekdays their area's wet/dry waste is collected,
computes a simple "collection is today/tomorrow" reminder, and generates a
downloadable .ics calendar file (hand-rolled, no extra dependency).
"""
import uuid
from datetime import date, timedelta

from app import config
from app.aws_clients import get_dynamodb_resource

SK = "COLLECTION_DAYS"

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAY_ICS_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def save_collection_days(user_email: str, wet_days: list[int], dry_days: list[int]) -> None:
    _table().put_item(Item={
        "PK": f"SETTINGS#{user_email}",
        "SK": SK,
        "wet_days": wet_days,
        "dry_days": dry_days,
    })


def get_collection_days(user_email: str) -> dict:
    result = _table().get_item(Key={"PK": f"SETTINGS#{user_email}", "SK": SK})
    item = result.get("Item")
    if not item:
        return {"wet_days": [], "dry_days": []}
    return {
        "wet_days": [int(d) for d in item.get("wet_days", [])],
        "dry_days": [int(d) for d in item.get("dry_days", [])],
    }


def get_reminder_banner(collection_days: dict) -> str | None:
    today = date.today().weekday()  # Monday=0
    tomorrow = (today + 1) % 7

    messages = []
    if today in collection_days["wet_days"]:
        messages.append("Wet waste collection is today.")
    if today in collection_days["dry_days"]:
        messages.append("Dry waste collection is today.")
    if tomorrow in collection_days["wet_days"] and today not in collection_days["wet_days"]:
        messages.append("Wet waste collection is tomorrow.")
    if tomorrow in collection_days["dry_days"] and today not in collection_days["dry_days"]:
        messages.append("Dry waste collection is tomorrow.")

    return " ".join(messages) if messages else None


def _next_occurrence(weekday: int) -> date:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    return today + timedelta(days=days_ahead)


def build_ics(user_email: str, collection_days: dict) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Haraa//Collection Reminders//EN",
        "CALSCALE:GREGORIAN",
    ]

    for label, days in (("Wet waste collection", collection_days["wet_days"]),
                         ("Dry waste collection", collection_days["dry_days"])):
        for weekday in days:
            start = _next_occurrence(weekday)
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uuid.uuid4()}@haraa.local",
                f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
                f"RRULE:FREQ=WEEKLY;BYDAY={WEEKDAY_ICS_CODES[weekday]}",
                f"SUMMARY:{label}",
                "END:VEVENT",
            ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
