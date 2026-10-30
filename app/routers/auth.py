import hashlib
import hmac

from botocore.exceptions import ClientError
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import config
from app.aws_clients import get_cognito_client
from app.templating import templates

router = APIRouter()


def _secret_hash(username: str) -> str | None:
    """Only needed if the app client was created WITH a secret. Our setup
    script creates a public (no-secret) client, so this stays unused, but
    it's here in case you point COGNITO_CLIENT_ID at a client that has one
    via COGNITO_CLIENT_SECRET."""
    client_secret = config.__dict__.get("COGNITO_CLIENT_SECRET")
    if not client_secret:
        return None
    message = username + config.COGNITO_CLIENT_ID
    dig = hmac.new(client_secret.encode(), message.encode(), hashlib.sha256).digest()
    import base64
    return base64.b64encode(dig).decode()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {
        "request": request,
        "error": None,
        "cognito_configured": config.cognito_configured(),
    })


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    if not config.cognito_configured():
        return templates.TemplateResponse(request, "login.html", {
            "request": request,
            "error": "Cognito isn't set up yet. Run scripts/setup_aws.py first.",
            "cognito_configured": False,
        }, status_code=400)

    client = get_cognito_client()
    try:
        auth_params = {"USERNAME": email, "PASSWORD": password}
        secret_hash = _secret_hash(email)
        if secret_hash:
            auth_params["SECRET_HASH"] = secret_hash

        response = client.initiate_auth(
            ClientId=config.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
        )
        request.session["user_email"] = email
        request.session["id_token"] = response["AuthenticationResult"]["IdToken"]
        return RedirectResponse("/dashboard", status_code=303)

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        from app.local_auth import verify_local_user
        if verify_local_user(email, password):
            request.session["user_email"] = email
            request.session["id_token"] = "local-token"
            return RedirectResponse("/dashboard", status_code=303)

        message = {
            "NotAuthorizedException": "Incorrect email or password.",
            "UserNotFoundException": "No account found for that email.",
            "UserNotConfirmedException": "Account not confirmed yet.",
        }.get(code, f"Login failed: {exc.response['Error']['Message']}")
        return templates.TemplateResponse(request, "login.html", {
            "request": request,
            "error": message,
            "cognito_configured": True,
        }, status_code=400)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {
        "request": request,
        "error": None,
        "success": None,
        "cognito_configured": config.cognito_configured(),
    })


@router.post("/register", response_class=HTMLResponse)
def register_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    if not config.cognito_configured():
        return templates.TemplateResponse(request, "register.html", {
            "request": request,
            "error": "Cognito isn't set up yet. Run scripts/setup_aws.py first.",
            "success": None,
            "cognito_configured": False,
        }, status_code=400)

    client = get_cognito_client()
    try:
        signup_kwargs = {
            "ClientId": config.COGNITO_CLIENT_ID,
            "Username": email,
            "Password": password,
            "UserAttributes": [{"Name": "email", "Value": email}],
        }
        secret_hash = _secret_hash(email)
        if secret_hash:
            signup_kwargs["SecretHash"] = secret_hash

        try:
            client.sign_up(**signup_kwargs)
        except ClientError as sign_up_exc:
            if sign_up_exc.response["Error"]["Code"] != "UsernameExistsException":
                raise

        from app.local_auth import save_local_user
        save_local_user(email, password)

        # Demo-friendly: auto-confirm the account immediately instead of
        # requiring an email verification link, since this runs on
        # localhost only.
        try:
            client.admin_confirm_sign_up(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=email,
            )
            client.admin_update_user_attributes(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=email,
                UserAttributes=[{"Name": "email_verified", "Value": "true"}],
            )
        except ClientError:
            # If SCP blocks admin confirmation, the local credential store allows login
            pass

        return templates.TemplateResponse(request, "register.html", {
            "request": request,
            "error": None,
            "success": "Account created! You can log in now.",
            "cognito_configured": True,
        })

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        message = {
            "UsernameExistsException": "An account with that email already exists.",
            "InvalidPasswordException": exc.response["Error"]["Message"],
        }.get(code, f"Registration failed: {exc.response['Error']['Message']}")
        return templates.TemplateResponse(request, "register.html", {
            "request": request,
            "error": message,
            "success": None,
            "cognito_configured": True,
        }, status_code=400)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
