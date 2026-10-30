"""Test Cognito client-side (non-admin) operations."""
import boto3
from botocore.exceptions import ClientError

region = "ap-south-1"
CLIENT_ID = "3e9dpln0qfgl9salhqcpqqh211"
POOL_ID = "ap-south-1_UrGplLefH"

cog = boto3.client("cognito-idp", region_name=region)

# 1. InitiateAuth (client-side, USER_PASSWORD_AUTH)
print("--- Cognito: InitiateAuth (client-side) ---")
try:
    cog.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "test@example.com", "PASSWORD": "WrongPass1"}
    )
except cog.exceptions.NotAuthorizedException:
    print("[OK] InitiateAuth accessible (wrong password, but API works)")
except cog.exceptions.UserNotFoundException:
    print("[OK] InitiateAuth accessible (user not found, but API works)")
except ClientError as e:
    err = e.response["Error"]
    print(f"[{err['Code']}] {err['Message'][:200]}")

# 2. GetUser (client-side, needs token)
print("--- Cognito: GetUser (client-side) ---")
try:
    cog.get_user(AccessToken="fake-token")
except cog.exceptions.NotAuthorizedException:
    print("[OK] GetUser accessible (bad token, but API works)")
except ClientError as e:
    err = e.response["Error"]
    print(f"[{err['Code']}] {err['Message'][:200]}")

# 3. AdminConfirmSignUp (admin-side)
print("--- Cognito: AdminConfirmSignUp ---")
try:
    cog.admin_confirm_sign_up(UserPoolId=POOL_ID, Username="nonexistent@test.com")
except cog.exceptions.UserNotFoundException:
    print("[OK] AdminConfirmSignUp accessible (user not found, but API works)")
except ClientError as e:
    err = e.response["Error"]
    print(f"[{err['Code']}] {err['Message'][:200]}")

# 4. AdminDeleteUser
print("--- Cognito: AdminDeleteUser ---")
try:
    cog.admin_delete_user(UserPoolId=POOL_ID, Username="__test_probe__@example.com")
except cog.exceptions.UserNotFoundException:
    print("[OK] AdminDeleteUser accessible")
except ClientError as e:
    err = e.response["Error"]
    print(f"[{err['Code']}] {err['Message'][:200]}")

# 5. AdminInitiateAuth
print("--- Cognito: AdminInitiateAuth ---")
try:
    cog.admin_initiate_auth(
        UserPoolId=POOL_ID,
        ClientId=CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "test@example.com", "PASSWORD": "WrongPass1"}
    )
except cog.exceptions.NotAuthorizedException:
    print("[OK] AdminInitiateAuth accessible (wrong password, but API works)")
except cog.exceptions.UserNotFoundException:
    print("[OK] AdminInitiateAuth accessible (user not found, but API works)")
except ClientError as e:
    err = e.response["Error"]
    print(f"[{err['Code']}] {err['Message'][:200]}")

print("\nDone.")
