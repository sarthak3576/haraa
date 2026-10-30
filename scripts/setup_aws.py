"""
One-time provisioning script. Creates the AWS resources this app needs:

  - A Cognito User Pool + App Client (no client secret, USER_PASSWORD_AUTH
    enabled) for login/registration.
  - A DynamoDB table (on-demand/PAY_PER_REQUEST billing, so you pay only
    for what you use -- a few cents at most for a demo).

It uses whatever AWS credentials are already configured on this machine
(same as the `aws` CLI) -- nothing is hardcoded and no keys are written
anywhere. It writes the resulting resource IDENTIFIERS (user pool id, app
client id, table name) to .env, which the app reads at startup.

Safe to re-run: it skips creation of anything that already exists (matched
by name), and never deletes anything. Estimated ongoing cost if left idle:
$0 (Cognito's free tier covers tens of thousands of users; DynamoDB
on-demand with no traffic is ~$0; Rekognition/Bedrock are billed only per
API call you make from the app).
"""
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.env_file_io import upsert_env_file  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

REGION = "ap-south-1"
USER_POOL_NAME = "waste-mgmt-pool"
APP_CLIENT_NAME = "waste-mgmt-client"
TABLE_NAME = "WasteMgmt"


def upsert_env(values: dict) -> None:
    """Resource IDs only (never secrets) -- see app/env_file_io.py for the
    shared read-modify-write logic that preserves every other line."""
    upsert_env_file(ENV_PATH, values)
    print(f"Wrote {', '.join(values.keys())} to {ENV_PATH}")


def find_existing_user_pool(client) -> str | None:
    paginator_pools = client.list_user_pools(MaxResults=60)["UserPools"]
    for pool in paginator_pools:
        if pool["Name"] == USER_POOL_NAME:
            return pool["Id"]
    return None


def create_user_pool(client) -> str:
    existing = find_existing_user_pool(client)
    if existing:
        print(f"User pool '{USER_POOL_NAME}' already exists: {existing}")
        return existing

    response = client.create_user_pool(
        PoolName=USER_POOL_NAME,
        AutoVerifiedAttributes=[],
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": False,
            }
        },
        Schema=[
            {"Name": "email", "AttributeDataType": "String", "Required": True, "Mutable": True},
        ],
        UsernameAttributes=["email"],
        AdminCreateUserConfig={"AllowAdminCreateUserOnly": False},
    )
    pool_id = response["UserPool"]["Id"]
    print(f"Created user pool: {pool_id}")
    return pool_id


def find_existing_app_client(client, user_pool_id: str) -> str | None:
    response = client.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)
    for c in response["UserPoolClients"]:
        if c["ClientName"] == APP_CLIENT_NAME:
            return c["ClientId"]
    return None


def create_app_client(client, user_pool_id: str) -> str:
    existing = find_existing_app_client(client, user_pool_id)
    if existing:
        print(f"App client '{APP_CLIENT_NAME}' already exists: {existing}")
        return existing

    response = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=APP_CLIENT_NAME,
        GenerateSecret=False,
        ExplicitAuthFlows=[
            "ALLOW_USER_PASSWORD_AUTH",
            "ALLOW_ADMIN_USER_PASSWORD_AUTH",
            "ALLOW_REFRESH_TOKEN_AUTH",
        ],
    )
    client_id = response["UserPoolClient"]["ClientId"]
    print(f"Created app client: {client_id}")
    return client_id


def create_dynamodb_table(region: str) -> str:
    dynamodb = boto3.client("dynamodb", region_name=region)
    try:
        dynamodb.describe_table(TableName=TABLE_NAME)
        print(f"DynamoDB table '{TABLE_NAME}' already exists.")
        return TABLE_NAME
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    dynamodb.create_table(
        TableName=TABLE_NAME,
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"Creating DynamoDB table '{TABLE_NAME}' (PAY_PER_REQUEST)...")
    waiter = dynamodb.get_waiter("table_exists")
    waiter.wait(TableName=TABLE_NAME)
    print("Table is active.")
    return TABLE_NAME


def main():
    print(f"Provisioning AWS resources in {REGION} using your default AWS credentials...")
    try:
        sts = boto3.client("sts", region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"Using AWS identity: {identity['Arn']}")
    except ClientError as exc:
        print(f"Could not verify AWS credentials: {exc}")
        sys.exit(1)

    cognito = boto3.client("cognito-idp", region_name=REGION)
    user_pool_id = create_user_pool(cognito)
    client_id = create_app_client(cognito, user_pool_id)
    table_name = create_dynamodb_table(REGION)

    upsert_env({
        "AWS_REGION": REGION,
        "BEDROCK_REGION": REGION,
        "BEDROCK_MODEL_ID": "anthropic.claude-haiku-5-5",
        "COGNITO_USER_POOL_ID": user_pool_id,
        "COGNITO_CLIENT_ID": client_id,
        "DYNAMODB_TABLE_NAME": table_name,
    })

    print("\nDone. Start the app with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
