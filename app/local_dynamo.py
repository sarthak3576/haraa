"""
Local SQLite-backed fallback for DynamoDB Table operations.
Provides identical API for:
- put_item(Item={...})
- get_item(Key={...})
- update_item(Key={...}, UpdateExpression=..., ExpressionAttributeValues=...)
- query(KeyConditionExpression=..., ScanIndexForward=..., Limit=...)
"""
import json
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "waste_mgmt.db"


def _json_serial(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class LocalDynamoTable:
    def __init__(self, name: str, db_path: Path = DB_PATH):
        self.name = name
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, timeout=10.0)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    pk TEXT NOT NULL,
                    sk TEXT NOT NULL,
                    data TEXT NOT NULL,
                    PRIMARY KEY (pk, sk)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_pk_sk ON items (pk, sk)")

    def put_item(self, Item: dict) -> dict:
        pk = str(Item.get("PK", ""))
        sk = str(Item.get("SK", ""))
        payload = json.dumps(Item, default=_json_serial)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO items (pk, sk, data) VALUES (?, ?, ?)",
                (pk, sk, payload),
            )
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def get_item(self, Key: dict) -> dict:
        pk = str(Key.get("PK", ""))
        sk = str(Key.get("SK", ""))
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT data FROM items WHERE pk = ? AND sk = ?", (pk, sk)
            )
            row = cursor.fetchone()
            if not row:
                return {}
            item = json.loads(row[0])
            return {"Item": item}

    def update_item(
        self,
        Key: dict,
        UpdateExpression: str = "",
        ExpressionAttributeValues: dict = None,
    ) -> dict:
        ExpressionAttributeValues = ExpressionAttributeValues or {}
        pk = str(Key.get("PK", ""))
        sk = str(Key.get("SK", ""))

        existing = self.get_item(Key).get("Item", {"PK": pk, "SK": sk})

        # Parse ADD expressions: e.g. ADD total_items :one, total_kg :w
        add_match = re.search(r"ADD\s+([^,]+(?:,[^,]+)*)", UpdateExpression, re.IGNORECASE)
        if add_match:
            clauses = [c.strip() for c in add_match.group(1).split(",")]
            for clause in clauses:
                parts = clause.split()
                if len(parts) == 2:
                    field, val_key = parts
                    val = ExpressionAttributeValues.get(val_key, 0)
                    if isinstance(val, Decimal):
                        val = int(val) if val % 1 == 0 else float(val)
                    curr = existing.get(field, 0)
                    existing[field] = curr + val

        # Parse SET expressions: e.g. SET logged = :true
        set_match = re.search(r"SET\s+([^,]+(?:,[^,]+)*)", UpdateExpression, re.IGNORECASE)
        if set_match:
            clauses = [c.strip() for c in set_match.group(1).split(",")]
            for clause in clauses:
                parts = [p.strip() for p in clause.split("=")]
                if len(parts) == 2:
                    field, val_key = parts
                    val = ExpressionAttributeValues.get(val_key)
                    if isinstance(val, Decimal):
                        val = int(val) if val % 1 == 0 else float(val)
                    existing[field] = val

        self.put_item(existing)
        return {"Attributes": existing, "ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(
        self,
        KeyConditionExpression=None,
        ScanIndexForward: bool = True,
        Limit: int = 1000,
        ExclusiveStartKey: dict = None,
    ) -> dict:
        pk = ""
        if hasattr(KeyConditionExpression, "get_expression"):
            expr = KeyConditionExpression.get_expression()
            values = expr.get("values", ())
            if len(values) >= 2:
                pk = str(values[1])
        elif isinstance(KeyConditionExpression, str):
            match = re.search(r"PK\s*=\s*:(\w+)", KeyConditionExpression)
            if match:
                pk = match.group(1)

        order = "ASC" if ScanIndexForward else "DESC"
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"SELECT data FROM items WHERE pk = ? ORDER BY sk {order} LIMIT ?",
                (pk, Limit),
            )
            rows = cursor.fetchall()
            items = [json.loads(r[0]) for r in rows]
            return {"Items": items, "Count": len(items)}


class LocalDynamoResource:
    def Table(self, name: str):
        return LocalDynamoTable(name)
