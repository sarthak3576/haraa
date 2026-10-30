from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from app import config
from app.aws_clients import get_dynamodb_resource


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def submit_quiz_score(user_email: str, section_id: str, score: int, total: int) -> dict:
    table = _table()
    pk = f"QUIZ#{user_email}"
    sk = section_id

    existing = table.get_item(Key={"PK": pk, "SK": sk}).get("Item")
    best_score = max(score, existing.get("best_score", 0)) if existing else score

    table.put_item(Item={
        "PK": pk,
        "SK": sk,
        "best_score": best_score,
        "total": total,
        "last_score": score,
        "attempts": (existing.get("attempts", 0) + 1) if existing else 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"best_score": best_score, "total": total}


def get_user_quiz_progress(user_email: str) -> dict:
    table = _table()
    result = table.query(
        KeyConditionExpression=Key("PK").eq(f"QUIZ#{user_email}")
    )
    progress = {}
    for item in result.get("Items", []):
        progress[item["SK"]] = {
            "best_score": int(item.get("best_score", 0)),
            "total": int(item.get("total", 0)),
            "attempts": int(item.get("attempts", 0)),
        }
    return progress
