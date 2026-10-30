import uuid
from datetime import datetime, timezone
from decimal import Decimal

from boto3.dynamodb.conditions import Key

from app import config
from app.aws_clients import get_dynamodb_resource


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def save_scan(user_email: str, thumbnail_b64: str, category: str, confidence: float) -> str:
    """Stores a tiny (~96px) base64 JPEG thumbnail inline in DynamoDB --
    small enough to stay well within the 400KB item limit, so no S3
    bucket is needed. Returns the new scan's id."""
    now = datetime.now(timezone.utc)
    scan_id = f"{now.isoformat()}#{uuid.uuid4().hex[:8]}"

    _table().put_item(Item={
        "PK": f"SCAN#{user_email}",
        "SK": scan_id,
        "thumbnail_b64": thumbnail_b64,
        "category": category,
        "confidence": Decimal(str(confidence)),
        "created_at": now.isoformat(),
        "logged": False,
    })
    return scan_id


def mark_scan_logged(user_email: str, scan_id: str) -> None:
    _table().update_item(
        Key={"PK": f"SCAN#{user_email}", "SK": scan_id},
        UpdateExpression="SET logged = :true",
        ExpressionAttributeValues={":true": True},
    )


def get_recent_scans(user_email: str, limit: int = 20) -> list[dict]:
    result = _table().query(
        KeyConditionExpression=Key("PK").eq(f"SCAN#{user_email}"),
        ScanIndexForward=False,
        Limit=limit,
    )
    scans = []
    for item in result.get("Items", []):
        scans.append({
            "scan_id": item["SK"],
            "thumbnail_b64": item.get("thumbnail_b64", ""),
            "category": item.get("category"),
            "confidence": float(item.get("confidence", 0.0)),
            "created_at": item.get("created_at"),
            "logged": bool(item.get("logged", False)),
        })
    return scans


def get_scan(user_email: str, scan_id: str) -> dict | None:
    result = _table().get_item(Key={"PK": f"SCAN#{user_email}", "SK": scan_id})
    item = result.get("Item")
    if not item:
        return None
    return {
        "scan_id": item["SK"],
        "category": item.get("category"),
        "confidence": float(item.get("confidence", 0.0)),
        "logged": bool(item.get("logged", False)),
    }
