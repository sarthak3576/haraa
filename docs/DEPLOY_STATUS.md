# Deploy status

**Live URL:** `https://bv6atp8dyl.execute-api.ap-south-1.amazonaws.com`
(direct API Gateway URL -- CloudFront is off for now; see below)

Stack: `haraa-demo`, region `ap-south-1`. Deployed via `scripts/deploy.sh`
(`EnableCloudFront=false`, the current default).

## What works

- Static assets (CSS, icons, binary PNGs) -- served by the web Lambda's own
  `StaticFiles` mount
- Register -> login -> cookie session (`Secure`, `HttpOnly`, `SameSite=Lax`)
  -> dashboard, exactly like localhost
- Photo upload -> Rekognition classify -> log waste -> dashboard reflects it
- HEIC/HEIF photos (e.g. straight off an iPhone) -- converted to JPEG in the
  browser before upload (see "HEIC conversion" below)
- Chatbot -- responds via the offline assistant (see "Known limitations" for why)
- Every `/api/v1/*` JWT-protected route: rejects requests with no token
  (401), then succeeds with a real Cognito token -- `uploads/presign` ->
  direct browser-to-S3 `PUT` -> `classify` (reading from S3) ->
  `waste-events` -> `quiz-score` (GET/POST) -> `chat`
- API Gateway throttling: 10 req/s (burst 20) account-wide, 2 req/s (burst 5)
  specifically on `POST /api/v1/uploads/presign` and `POST /api/v1/classify`
  -- the two routes that actually spend money per call
- CloudWatch dashboard, the API-5xx alarm, the Lambda-errors alarm, and a
  dedicated `classify-invocation-spike` alarm (>=100 classify invocations in
  5 minutes) as a cost guard on top of the throttling
- Both S3 buckets stay private; the uploads bucket's 7-day lifecycle rule
  is in place

## Known limitations

- **`SESSION_SECRET` is a plaintext Lambda environment variable.** Hidden
  from CloudFormation (`NoEcho`, shows as `****` in `describe-stacks`), but
  under the hood it's a plain Lambda env var -- readable via
  `lambda:GetFunctionConfiguration` by anything with that IAM permission in
  this account. That's how every Lambda env var works (there's no
  "write-only" variant); it is not an AWS credential, only a local
  cookie-signing secret. Deliberately left as-is for now (decision pending
  on whether to move it to SSM SecureString like `GEMINI_API_KEY`).
- **No HEIC decoding on the server**, in either code path. The browser-side
  conversion (below) covers normal use from the upload page, but the raw
  `POST /upload`/`POST /api/v1/classify` endpoints themselves still reject a
  HEIC file if one reaches them directly (e.g. a non-browser API client that
  skips conversion) -- `pillow-heif` isn't in the Lambda layer (see
  `docs/ARCHITECTURE.md`).
- **CloudFront is pending account verification.** AWS returned
  `AccessDenied` ("Your account must be verified...") when creating the
  distribution. `EnableCloudFront` is a one-flag toggle (default `false`) --
  once you've gone through AWS Support, redeploy with
  `ENABLE_CLOUDFRONT=true scripts/deploy.sh` and nothing else changes.
- **Bedrock access is restricted.** "access not enabled on this AWS
  account" -- request model access in the Bedrock console. The chatbot
  falls back to the offline assistant automatically in the meantime (Gemini
  is also unconfigured -- no SSM parameter set -- so it falls through both).
- **Signup is open to anyone who reaches the URL.** `POST /register` calls
  Cognito `SignUp` + auto-confirms the account (same demo-friendly behavior
  as localhost) with no invite code, email-domain allowlist, or admin
  approval step -- anyone who finds the API Gateway URL can create an
  account and use the app (rate-limited by the throttling above, but not
  gated). Fine for a demo; would need an approval step or an allowlist
  before sharing this URL more broadly.
- **~4 second cold start** on the `web`/`chatbot` functions (FastAPI/Pydantic/
  Pillow/Mangum import time in a fresh execution environment -- see
  `docs/BENCHMARKS.md`). Warm requests are ~0.2-0.5s. The four no-layer
  `/api/v1/*` functions cold-start noticeably faster.

## HEIC conversion

`app/templates/upload.html` now lazy-loads a locally-bundled copy of
[heic2any](https://github.com/alexcorvi/heic2any) (`app/static/js/heic2any.min.js`,
MIT licensed, no CDN/runtime dependency) the moment a `.heic`/`.heif` file is
selected, converts it to JPEG in the browser, and swaps it into the file
input before submission -- works whether or not the backend has HEIC
decoding available (it doesn't, in this deployment -- see
`docs/ARCHITECTURE.md`). If conversion fails (e.g. offline, or an
unsupported HEIC variant), the page shows a clear message asking for a
JPEG/PNG instead, rather than silently submitting a file the server can't
read.

## How to deploy

```
git checkout aws-deploy
scripts/deploy.sh                                  # CloudFront off, Gemini off
ENABLE_CLOUDFRONT=true scripts/deploy.sh           # add CloudFront (needs account verification)
GEMINI_PARAMETER_NAME=/haraa/demo/gemini-api-key \
  scripts/deploy.sh                                # Gemini on (after you put the SSM parameter yourself)
```

One command (`scripts/deploy.sh`) builds (cross-platform `pip install`, no
Docker) and deploys the whole stack, then prints the stack outputs and sets
up the `us-east-1` billing alarm.

## How to destroy

```
scripts/destroy.sh
```

Empties both S3 buckets (CloudFormation can't delete a non-empty bucket),
deletes the `haraa-demo` stack, and removes the separate `us-east-1`
billing alarm + SNS topic. Nothing is left running or billable afterward.

## Test identity used while verifying this

A handful of disposable `haraatest+<timestamp>@example.com` Cognito users
were created during testing (via the app's own `/register` and via direct
`aws cognito-idp sign-up` calls) and a few waste events logged under them --
harmless demo data, safe to ignore or delete via the Cognito/DynamoDB
console.
