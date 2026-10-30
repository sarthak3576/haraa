"""
POST /api/v1/uploads/presign -- Cognito-JWT-authorized.
Body (optional): {"content_type": "image/jpeg"}
Returns a short-lived presigned PUT URL plus the S3 key the browser should
upload straight to (and that /api/v1/classify is then called with). Keys
are namespaced under uploads/<cognito-sub>/... purely for organization --
IAM scoping is at the uploads/* prefix level (see docs/SECURITY.md).
"""
import json
import os
import uuid

import boto3

UPLOADS_BUCKET = os.environ["UPLOADS_BUCKET"]
EXPIRES_SECONDS = 300
_REGION = os.environ["AWS_REGION"]
# Explicit region_name alone wasn't enough -- the Lambda runtime's
# preinstalled botocore still signed/addressed the URL against the global
# s3.amazonaws.com host, which S3 307-redirects for any non-us-east-1
# bucket. Pinning endpoint_url forces the regional host outright.
_s3 = boto3.client("s3", region_name=_REGION, endpoint_url=f"https://s3.{_REGION}.amazonaws.com")

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}


def lambda_handler(event, context):
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        payload = {}

    content_type = payload.get("content_type", "image/jpeg")
    if content_type not in _ALLOWED_CONTENT_TYPES:
        return _response(400, {"error": f"content_type must be one of {sorted(_ALLOWED_CONTENT_TYPES)}."})

    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_sub = claims.get("sub", "unknown")

    extension = content_type.split("/", 1)[1]
    key = f"uploads/{user_sub}/{uuid.uuid4().hex}.{extension}"

    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": UPLOADS_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=EXPIRES_SECONDS,
    )

    return _response(200, {"upload_url": upload_url, "key": key, "expires_in": EXPIRES_SECONDS})
