# Cost estimate (demo scale: a handful of people, a few dozen requests/day)

Nothing in this stack runs continuously or auto-scales on a schedule --
every line item is pay-per-request/pay-per-GB. At demo-scale traffic, the
realistic total is **well under $1/month**, and several services round to
$0 under their always-free tiers. Figures are ballpark (ap-south-1
pricing), the same spirit as the existing `about.html` table for the local
app -- not an invoice.

| Service | Pricing basis | Demo-scale cost |
|---|---|---|
| Lambda (7 functions) | $0.20 / 1M requests + $0.0000166667 / GB-s | A few cents/month -- free tier alone (1M requests + 400,000 GB-s/month) likely covers all of it |
| API Gateway (HTTP API) | ~$1.00 / 1M requests | Fractions of a cent at this volume |
| CloudFront | Free tier: 1 TB out + 10M requests/month (first 12 months); after that, ~$0.085/GB in this price class | $0 under free tier; cents/month after |
| S3 (uploads + frontend) | ~$0.025/GB-month storage + request costs | Uploads bucket self-empties after 7 days, so storage never accumulates; frontend bucket is ~1.4 MB. Cents at most |
| DynamoDB (on-demand) | ~$1.25 / 1M write request units, ~$0.25 / 1M read request units | Cents at most -- same table design as the already-working local on-demand table |
| Cognito | Free under 50,000 MAUs | $0 |
| Rekognition (`DetectLabels`) | ~$1 / 1,000 images | Cents (only called on an actual upload/classify) |
| Bedrock (Claude Haiku, optional) | Per-token, fractions of a cent/message | Cents at most, only if the chatbot falls through to it |
| Gemini (optional, via SSM key) | Free tier (generous daily limits) | $0 if enabled |
| CloudWatch (dashboard + 3 alarms + logs) | Dashboard: $3/month flat; alarms: $0.10/alarm/month; logs: ~$0.50/GB ingested | ~$3.30/month -- the single largest line item, from the dashboard's flat fee, not traffic |
| SNS (alarm topics) | Free tier: 1M requests/month | $0 |
| SSM Parameter Store (standard tier) | Free | $0 |

**Total at demo scale: roughly $3-4/month**, almost entirely the
CloudWatch dashboard's flat $3/month fee -- everything that scales with
actual usage (Lambda, API Gateway, DynamoDB, S3, Rekognition) stays in the
cents range or free-tier range at this traffic level.

## What's already excluded to avoid idle cost

- No NAT Gateway (~$32/month + per-GB if it existed -- this stack has no
  VPC at all, so there's nothing to NAT).
- No always-on EC2/Fargate/"warm" Lambda (no provisioned concurrency).
- No REST API (HTTP API's pricing is roughly 1/3 of REST API's per-request cost).
- No provisioned-capacity DynamoDB (on-demand means $0 when nothing is
  reading/writing, not a baseline hourly charge).
- No custom domain / Route 53 hosted zone / ACM-managed certificate.

## Estimated-charges alarm

`scripts/deploy.sh` creates a CloudWatch alarm on the `AWS/Billing`
`EstimatedCharges` metric (in **us-east-1**, since that's the only region
that metric is published in, regardless of this stack's own ap-south-1
region), threshold $5. It only receives data if **"Receive Billing
Alerts"** is turned on under Billing preferences for this account -- a
one-time account-level setting that CloudFormation/SAM cannot flip for
you. If it isn't already on, the deploy's test report will say so
explicitly.

## Teardown

`scripts/destroy.sh` empties both S3 buckets, deletes the whole
CloudFormation stack, and removes the separate us-east-1 billing alarm +
SNS topic -- nothing billable is left running afterward (the one shared,
account-wide `aws-sam-cli-managed-default` artifacts bucket that `sam
deploy --resolve-s3` maintains is intentionally left in place, since it's
a reusable AWS SAM CLI convention rather than something this project owns;
it holds a few KB of zipped Lambda artifacts and costs effectively nothing
idle).
