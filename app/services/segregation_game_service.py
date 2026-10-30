from app import config
from app.aws_clients import get_dynamodb_resource

SK = "SEGREGATION_BEST"


def _table():
    return get_dynamodb_resource().Table(config.DYNAMODB_TABLE_NAME)


def get_best_score(user_email: str) -> int:
    result = _table().get_item(Key={"PK": f"GAME#{user_email}", "SK": SK})
    item = result.get("Item")
    return int(item["best_score"]) if item else 0


def submit_score(user_email: str, score: int) -> int:
    """Updates the stored best score only if this one is higher. Returns
    the (possibly unchanged) best score."""
    current_best = get_best_score(user_email)
    if score > current_best:
        _table().put_item(Item={"PK": f"GAME#{user_email}", "SK": SK, "best_score": score})
        return score
    return current_best
