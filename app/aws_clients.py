"""
Thin, cached factories for boto3 clients.

No access keys are ever read or written here. boto3 uses the default
credential provider chain, which picks up whatever credentials are already
configured on this machine (aws configure, environment variables, SSO,
an instance/role profile, etc.) automatically.
"""
from functools import lru_cache

import boto3
from botocore.config import Config

from app import config


@lru_cache
def get_cognito_client():
    return boto3.client("cognito-idp", region_name=config.AWS_REGION)


@lru_cache
def get_dynamodb_resource():
    try:
        ddb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
        ddb.Table(config.DYNAMODB_TABLE_NAME).load()
        return ddb
    except Exception:
        from app.local_dynamo import LocalDynamoResource
        return LocalDynamoResource()


@lru_cache
def get_rekognition_client():
    return boto3.client("rekognition", region_name=config.AWS_REGION)


@lru_cache
def get_bedrock_runtime_client():
    # Short timeouts + no retries so a stuck/slow Bedrock call fails fast
    # and the chatbot's provider chain can fall back quickly.
    timeout_config = Config(
        connect_timeout=config.BEDROCK_TIMEOUT_SECONDS,
        read_timeout=config.BEDROCK_TIMEOUT_SECONDS,
        retries={"max_attempts": 1},
    )
    return boto3.client("bedrock-runtime", region_name=config.BEDROCK_REGION, config=timeout_config)
