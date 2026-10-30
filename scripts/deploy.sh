#!/usr/bin/env bash
# One-command deploy of the whole Haraa serverless stack.
#
# Usage:
#   scripts/deploy.sh                                  # no CloudFront, no Gemini
#   ENABLE_CLOUDFRONT=true scripts/deploy.sh           # add CloudFront (needs
#                                                        an AWS-verified account)
#   GEMINI_PARAMETER_NAME=/haraa/demo/gemini-api-key \
#     scripts/deploy.sh                                # Gemini enabled
#     (only if you already ran, yourself:
#        aws ssm put-parameter --name /haraa/demo/gemini-api-key \
#          --type SecureString --value "<your key>"
#      -- this script never reads, prints, or sets the key value.)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../infra"

STAGE="${STAGE:-demo}"
GEMINI_PARAMETER_NAME="${GEMINI_PARAMETER_NAME:-}"
ENABLE_CLOUDFRONT="${ENABLE_CLOUDFRONT:-false}"
SESSION_SECRET="$(openssl rand -hex 32)"

echo "==> Building (cross-platform pip install, no Docker)..."
sam build

echo "==> Deploying stack 'haraa-${STAGE}' to ap-south-1 (EnableCloudFront=${ENABLE_CLOUDFRONT})..."
# SAM's --parameter-overrides shorthand rejects an explicitly empty value
# (ParameterKey=), so GeminiParameterName is only passed when set -- the
# template's own Default: "" covers the unset case.
PARAM_OVERRIDES=("Stage=${STAGE}" "SessionSecret=${SESSION_SECRET}" "EnableCloudFront=${ENABLE_CLOUDFRONT}")
if [ -n "$GEMINI_PARAMETER_NAME" ]; then
  PARAM_OVERRIDES+=("GeminiParameterName=${GEMINI_PARAMETER_NAME}")
fi
sam deploy --parameter-overrides "${PARAM_OVERRIDES[@]}"

echo "==> Stack outputs:"
OUTPUTS_JSON=$(aws cloudformation describe-stacks --stack-name "haraa-${STAGE}" --region ap-south-1 \
  --query 'Stacks[0].Outputs' --output json)
echo "$OUTPUTS_JSON" | python3 -c "
import json, sys
for o in json.load(sys.stdin):
    print(f\"  {o['OutputKey']}: {o['OutputValue']}\")
"

echo
echo "==> Billing: creating/updating the estimated-charges alarm in us-east-1"
echo "    (AWS/Billing metrics only exist there, regardless of the stack's own region)."
BILLING_TOPIC_ARN=$(aws sns create-topic --name "haraa-${STAGE}-billing-alarm" --region us-east-1 \
  --tags Key=Project,Value=haraa Key=Environment,Value="${STAGE}" Key=ManagedBy,Value=deploy.sh \
  --query 'TopicArn' --output text)
aws cloudwatch put-metric-alarm --region us-east-1 \
  --alarm-name "haraa-${STAGE}-estimated-charges" \
  --alarm-description "Estimated AWS charges exceeded the demo-scale threshold." \
  --namespace "AWS/Billing" --metric-name EstimatedCharges \
  --dimensions Name=Currency,Value=USD \
  --statistic Maximum --period 21600 --evaluation-periods 1 \
  --threshold 5 --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$BILLING_TOPIC_ARN"
echo "    Billing alarm topic: $BILLING_TOPIC_ARN"
echo "    Subscribe your email to it if you want a notification:"
echo "      aws sns subscribe --region us-east-1 --topic-arn $BILLING_TOPIC_ARN --protocol email --notification-endpoint you@example.com"
echo "    Note: this only receives data if 'Receive Billing Alerts' is turned on"
echo "    under Billing preferences for this account -- a one-time account"
echo "    setting this script cannot flip for you."
echo
if [ "$ENABLE_CLOUDFRONT" = "true" ]; then
  echo "==> Done. CloudFront URL is above (CloudFrontUrl) -- allow a few minutes"
  echo "    after first deploy for the distribution to finish propagating."
else
  echo "==> Done. CloudFront is disabled (EnableCloudFront=false) -- use HttpApiUrl"
  echo "    above directly. Re-run with ENABLE_CLOUDFRONT=true once your AWS"
  echo "    account is verified for CloudFront to add it in front of the same stack."
fi
