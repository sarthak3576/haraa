"""Test all AWS services the app needs."""
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"

# 1. STS
print("--- STS ---")
sts = boto3.client("sts", region_name=region)
identity = sts.get_caller_identity()
print(f"  Identity: {identity['Arn']}")
print(f"  Account:  {identity['Account']}")

# 2. Cognito
print("--- Cognito ---")
try:
    cog = boto3.client("cognito-idp", region_name=region)
    pools = cog.list_user_pools(MaxResults=10)
    for p in pools["UserPools"]:
        print(f"  Pool: {p['Name']} ({p['Id']})")
    if not pools["UserPools"]:
        print("  No pools found (but API call succeeded)")
except ClientError as e:
    print(f"  {e.response['Error']['Code']}: {e.response['Error']['Message'][:150]}")

# 3. DynamoDB
print("--- DynamoDB ---")
try:
    ddb = boto3.client("dynamodb", region_name=region)
    tables = ddb.list_tables()
    print(f"  Tables: {tables['TableNames']}")
except ClientError as e:
    print(f"  {e.response['Error']['Code']}: {e.response['Error']['Message'][:150]}")

# 4. Rekognition
print("--- Rekognition ---")
try:
    rek = boto3.client("rekognition", region_name=region)
    rek.list_collections()
    print("  Rekognition: accessible")
except ClientError as e:
    print(f"  {e.response['Error']['Code']}: {e.response['Error']['Message'][:150]}")

# 5. Bedrock
print("--- Bedrock ---")
try:
    bed = boto3.client("bedrock", region_name=region)
    models = bed.list_foundation_models(byProvider="Anthropic")
    names = [m["modelId"] for m in models["modelSummaries"][:3]]
    print(f"  Bedrock models: {names}")
except ClientError as e:
    print(f"  {e.response['Error']['Code']}: {e.response['Error']['Message'][:150]}")
except Exception as e:
    print(f"  {type(e).__name__}: {str(e)[:150]}")

print("\nDone.")
