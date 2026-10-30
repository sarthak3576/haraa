"""
Utility to check AWS connection and verify credentials.
"""
import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config

def test_aws():
    print("=" * 60)
    print("AWS Connection Diagnostic")
    print("=" * 60)
    print(f"Target Region:       {config.AWS_REGION}")
    print(f"Cognito User Pool:   {config.COGNITO_USER_POOL_ID or 'Not configured'}")
    print(f"DynamoDB Table:      {config.DYNAMODB_TABLE_NAME or 'Not configured'}")
    print("-" * 60)

    try:
        sts = boto3.client("sts", region_name=config.AWS_REGION)
        caller = sts.get_caller_identity()
        print("[SUCCESS] AWS Credentials Verified!")
        print(f"Account ID: {caller['Account']}")
        print(f"IAM User / Role: {caller['Arn']}")
    except NoCredentialsError:
        print("[MISSING] No AWS credentials found.")
        print("\nTo connect this project to your AWS Console:")
        print("1. Open your AWS Console in your browser.")
        print("2. Search for 'IAM' -> 'Users' -> click your username -> 'Security credentials'.")
        print("3. Click 'Create access key' (select 'Command Line Interface' or 'Application').")
        print("4. Copy the Access Key ID and Secret Access Key, and either:")
        print("   A) Add them to .env.local in this project:")
        print("        AWS_ACCESS_KEY_ID=AKIA...")
        print("        AWS_SECRET_ACCESS_KEY=wJalrXUtn...")
        print("        AWS_DEFAULT_REGION=ap-south-1")
        print("   B) Or run in PowerShell:")
        print("        $env:AWS_ACCESS_KEY_ID=\"AKIA...\"")
        print("        $env:AWS_SECRET_ACCESS_KEY=\"wJalr...\"")
        print("        $env:AWS_DEFAULT_REGION=\"ap-south-1\"")
        return False
    except ClientError as e:
        print(f"[ERROR] AWS ClientError: {e}")
        return False

    # Check DynamoDB
    print("-" * 60)
    print(f"Checking DynamoDB table '{config.DYNAMODB_TABLE_NAME}'...")
    try:
        ddb = boto3.client("dynamodb", region_name=config.AWS_REGION)
        table = ddb.describe_table(TableName=config.DYNAMODB_TABLE_NAME)
        status = table["Table"]["TableStatus"]
        print(f"[SUCCESS] DynamoDB table is ACTIVE (Status: {status})")
    except ClientError as e:
        print(f"[NOTICE] DynamoDB check: {e}")

    # Check Cognito
    print("-" * 60)
    print(f"Checking Cognito pool '{config.COGNITO_USER_POOL_ID}'...")
    try:
        cognito = boto3.client("cognito-idp", region_name=config.AWS_REGION)
        pool = cognito.describe_user_pool(UserPoolId=config.COGNITO_USER_POOL_ID)
        print(f"[SUCCESS] Cognito User Pool '{pool['UserPool']['Name']}' is reachable")
    except ClientError as e:
        print(f"[NOTICE] Cognito check: {e}")

    print("=" * 60)
    return True

if __name__ == "__main__":
    test_aws()
