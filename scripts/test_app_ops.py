"""Test the SPECIFIC operations the app actually uses (not admin/list calls)."""
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
POOL_ID = "ap-south-1_UrGplLefH"
CLIENT_ID = "3e9dpln0qfgl9salhqcpqqh211"
TABLE = "WasteMgmt"

print("=" * 60)
print("Testing specific app-level operations")
print("=" * 60)

# 1. Cognito: AdminGetUser (what login uses)
print("\n--- Cognito: AdminGetUser ---")
try:
    cog = boto3.client("cognito-idp", region_name=region)
    cog.admin_get_user(UserPoolId=POOL_ID, Username="test@example.com")
    print("  [OK] AdminGetUser succeeded")
except cog.exceptions.UserNotFoundException:
    print("  [OK] Cognito accessible (user not found, but API call worked)")
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"][:200]
    print(f"  [{code}] {msg}")

# 2. Cognito: SignUp (what registration uses - won't actually create user)
print("\n--- Cognito: SignUp (dry check) ---")
try:
    cog.sign_up(
        ClientId=CLIENT_ID,
        Username="__test_probe__@example.com",
        Password="TestProbe1234",
        UserAttributes=[{"Name": "email", "Value": "__test_probe__@example.com"}]
    )
    print("  [OK] SignUp succeeded (will clean up)")
    # Clean up
    try:
        cog.admin_delete_user(UserPoolId=POOL_ID, Username="__test_probe__@example.com")
    except:
        pass
except cog.exceptions.UsernameExistsException:
    print("  [OK] Cognito SignUp accessible (user exists)")
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"][:200]
    print(f"  [{code}] {msg}")

# 3. DynamoDB: GetItem (what dashboard/scans use)
print("\n--- DynamoDB: GetItem ---")
try:
    ddb = boto3.client("dynamodb", region_name=region)
    ddb.get_item(TableName=TABLE, Key={"PK": {"S": "__probe__"}, "SK": {"S": "__probe__"}})
    print("  [OK] DynamoDB GetItem accessible")
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"][:200]
    print(f"  [{code}] {msg}")

# 4. Rekognition: DetectLabels (what scan uses)
print("\n--- Rekognition: DetectLabels (no image, just access check) ---")
try:
    rek = boto3.client("rekognition", region_name=region)
    # Use minimal bytes - will fail with InvalidImageException if accessible
    rek.detect_labels(Image={"Bytes": b"x"})
    print("  [OK] Rekognition accessible")
except rek.exceptions.InvalidImageFormatException:
    print("  [OK] Rekognition accessible (bad image, but API call worked)")
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"][:200]
    print(f"  [{code}] {msg}")

# 5. Try us-east-1 for DynamoDB
print("\n--- DynamoDB us-east-1: ListTables ---")
try:
    ddb2 = boto3.client("dynamodb", region_name="us-east-1")
    tables = ddb2.list_tables()
    print(f"  [OK] us-east-1 DynamoDB tables: {tables['TableNames']}")
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg = e.response["Error"]["Message"][:200]
    print(f"  [{code}] {msg}")

print("\nDone.")
