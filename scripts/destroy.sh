#!/usr/bin/env bash
# One-command teardown of everything scripts/deploy.sh created.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../infra"

STAGE="${STAGE:-demo}"
STACK_NAME="haraa-${STAGE}"

echo "==> Emptying S3 buckets first (CloudFormation can't delete a non-empty bucket)..."
for OUTPUT_KEY in UploadsBucketName; do
  BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region ap-south-1 \
    --query "Stacks[0].Outputs[?OutputKey=='${OUTPUT_KEY}'].OutputValue" --output text 2>/dev/null || true)
  if [ -n "${BUCKET:-}" ] && [ "$BUCKET" != "None" ]; then
    echo "    Emptying s3://$BUCKET"
    aws s3 rm "s3://$BUCKET" --recursive --region ap-south-1 || true
  fi
done

# The frontend bucket has no stack Output (it's internal) -- find it by its
# stack-assigned logical id instead.
FRONTEND_BUCKET=$(aws cloudformation describe-stack-resource --stack-name "$STACK_NAME" --region ap-south-1 \
  --logical-resource-id FrontendBucket --query 'StackResourceDetail.PhysicalResourceId' --output text 2>/dev/null || true)
if [ -n "${FRONTEND_BUCKET:-}" ] && [ "$FRONTEND_BUCKET" != "None" ]; then
  echo "    Emptying s3://$FRONTEND_BUCKET"
  aws s3 rm "s3://$FRONTEND_BUCKET" --recursive --region ap-south-1 || true
fi

echo "==> Deleting stack '$STACK_NAME'..."
sam delete --stack-name "$STACK_NAME" --region ap-south-1 --no-prompts

echo "==> Removing the us-east-1 billing alarm + topic..."
aws cloudwatch delete-alarms --region us-east-1 --alarm-names "haraa-${STAGE}-estimated-charges" || true
TOPIC_ARN=$(aws sns list-topics --region us-east-1 --query "Topics[?contains(TopicArn, 'haraa-${STAGE}-billing-alarm')].TopicArn" --output text || true)
if [ -n "${TOPIC_ARN:-}" ] && [ "$TOPIC_ARN" != "None" ]; then
  aws sns delete-topic --region us-east-1 --topic-arn "$TOPIC_ARN" || true
fi

echo "==> Done. Everything scripts/deploy.sh created has been removed."
