# Security (serverless deployment)

## IAM: one execution role per Lambda, least privilege

Every function in `infra/template.yaml` gets its own execution role (SAM
creates one automatically per `AWS::Serverless::Function`, scoped by that
function's own `Policies:` block) -- none are shared, and none use
`Resource: "*"` except for the handful of AWS actions below that simply
don't support resource-level scoping.

| Function | Actions | Resource | Why |
|---|---|---|---|
| `web` | `dynamodb:GetItem/PutItem/UpdateItem/Query` | the one table ARN | every dashboard/upload/game route reads or writes it |
| `web` | `rekognition:DetectLabels` | `*` | Rekognition does not support resource-level permissions for this action |
| `web` | `cognito-idp:InitiateAuth`, `cognito-idp:SignUp` | `*` | these two actions are not resource-scopable in IAM (confirmed against the Cognito IAM action reference) |
| `web` | `cognito-idp:AdminConfirmSignUp`, `cognito-idp:AdminUpdateUserAttributes` | the one user pool ARN | these admin actions *are* scopable, so they're scoped |
| `web` | `bedrock:InvokeModel` | `arn:aws:bedrock:<region>::foundation-model/*` | scoped to the service's foundation-model resource type, not account-wide `*` |
| `web` | `ssm:GetParameter` (only if `GeminiParameterName` is set) | the one parameter ARN | optional Gemini key lookup |
| `classify` | `rekognition:DetectLabels` | `*` | same constraint as above |
| `classify` | `s3:GetObject` | `<uploads-bucket>/uploads/*` | only needs to read what was just uploaded |
| `presign` | `s3:PutObject` | `<uploads-bucket>/uploads/*` | a presigned URL is only valid for actions its signer is authorized for -- this is what makes the signature meaningful |
| `log-waste` | `dynamodb:PutItem/UpdateItem` | the one table ARN | writes an event row + bumps the aggregate; no read access needed |
| `dashboard` | `dynamodb:GetItem/Query` | the one table ARN | read-only |
| `quiz-scores` | `dynamodb:GetItem/PutItem` | the one table ARN | reads/writes only the one `GAME#<user>` item |
| `chatbot` | `bedrock:InvokeModel` | foundation-model ARN | same as web |
| `chatbot` | `ssm:GetParameter` (conditional) | the one parameter ARN | same as web |

No function has `dynamodb:Scan`, `dynamodb:DeleteTable`, `s3:DeleteObject`,
`s3:PutBucketPolicy`, `iam:*`, or any action outside what its own handler
code actually calls.

## Where wildcards remain, and why

A small number of AWS APIs genuinely don't support resource-level IAM
conditions:
- `rekognition:DetectLabels` -- Rekognition's synchronous detection APIs
  are not resource-scopable; AWS's own managed policies for Rekognition
  use `Resource: "*"` for the same reason.
- `cognito-idp:InitiateAuth` / `SignUp` -- these are "public client" auth
  actions; Cognito's IAM reference does not list them as supporting
  resource-level permissions (unlike the `Admin*` actions, which are
  scoped above to the specific user pool ARN).

Both are documented here rather than silently left broad.

## Secrets

- **No AWS access keys anywhere.** Every Lambda uses its own execution
  role; the deploying machine's `aws configure`d credentials are only used
  by `sam deploy` / `scripts/deploy.sh` itself, never embedded in the stack.
- **`SessionSecret`** (signs the browser session cookie) is generated fresh
  by `scripts/deploy.sh` via `openssl rand -hex 32` on every deploy and
  passed as a `NoEcho` CloudFormation parameter -- never written to a file,
  never logged, never the same value as any local `.env`'s `SESSION_SECRET`.
- **`GEMINI_API_KEY`** is never in code, never in the template, never in an
  environment-variable default. If you want it live, you create it
  yourself, outside of anything this project runs:
  ```
  aws ssm put-parameter --name /haraa/demo/gemini-api-key \
    --type SecureString --value "<your key>"
  ```
  and pass that parameter *name* (not the value) to `scripts/deploy.sh` via
  `GEMINI_PARAMETER_NAME`. The `chatbot`/`web` Lambdas decrypt it at runtime
  via `ssm:GetParameter` scoped to that one parameter's ARN. If it's never
  set, the existing provider chain (Gemini -> Bedrock -> offline assistant)
  just skips straight to Bedrock, then the offline assistant -- exactly the
  same graceful degradation as running locally with no key configured.

## Network / transport

- CloudFront enforces HTTPS (`ViewerProtocolPolicy: redirect-to-https`) on
  every behavior; the origin-to-CloudFront hop to API Gateway is also
  HTTPS-only (`OriginProtocolPolicy: https-only`).
- The frontend S3 bucket has `PublicAccessBlockConfiguration` fully
  enabled and is only reachable via CloudFront's Origin Access Control
  (its bucket policy's `Condition` pins access to this one distribution's
  ARN) -- there is no public bucket URL.
- The uploads S3 bucket also has `PublicAccessBlockConfiguration` fully
  enabled; the only way in or out is a time-limited (5 minute) presigned
  URL signed by the `presign`/`classify` Lambdas' own scoped permissions.
  Its CORS rule allows any origin (`AllowedOrigins: ["*"]`) -- this is
  deliberate and safe here: CORS only controls whether a *browser's JS*
  can read the response, not whether the signed `PUT` succeeds, and the
  actual access control is the presigned signature itself (time-limited,
  scoped to one exact key, one exact bucket, one exact HTTP method).
- The session cookie is `httponly` (via Starlette's `SessionMiddleware`
  default) and marked `Secure` in the deployed environment
  (`SESSION_HTTPS_ONLY=true`, `app/config.py`), `SameSite=Lax`.

## IAM changes made to the deploying user (`waste-app`), for the record

This account's `waste-app` IAM user was already at AWS's hard limit of 10
managed policies attached per user, and lacked Lambda-management and SSM
Parameter Store permissions entirely (needed to deploy/update this stack
at all). To fix this without exceeding the limit:
- Detached `AmazonBedrockFullAccess` (only used for the *local* chatbot's
  optional direct Bedrock calls under this same identity -- it already
  degrades gracefully to the offline assistant without it; the *deployed*
  Lambdas have their own, separate, scoped `bedrock:InvokeModel` permission
  regardless of this).
- Added one new customer-managed policy, `haraa-lambda-ssm-admin`, scoped
  to exactly the Lambda-management and SSM Parameter Store actions this
  deployment needs (not the full `AWSLambda_FullAccess` / `AmazonSSMFullAccess`
  managed policies, to stay narrower and keep a free policy slot available).

This only affects what the `waste-app` *deploying identity* can do in the
AWS console/CLI -- it has no bearing on any Lambda's own execution-role
permissions, which are the ones listed in the table above.
