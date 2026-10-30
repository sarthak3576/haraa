# Benchmarks

Measured against the live `haraa-demo` stack in `ap-south-1` via `curl -w
"%{time_total}"`, from a single machine (not a load test -- just real
numbers from exercising the deployed app, at demo scale). All functions use
`python3.12`/`x86_64`; the `web` and `chatbot` functions carry the shared
`WebDepsLayer` (512 MB memory, 29s timeout); the other four (`classify`,
`presign`, `log-waste`, `dashboard`, `quiz-scores`) have no layer (256 MB,
15s timeout).

## Cold start vs. warm (web function, `GET /healthz`)

| | Time |
|---|---|
| Cold (first request after a fresh deploy) | 3.8s - 4.3s, across 4 separate deploys |
| Warm (immediate second request) | 0.25s - 0.49s |

The cold-start cost here is almost entirely FastAPI/Starlette/Pydantic
import time plus Mangum's ASGI bridge setup inside a 512 MB execution
environment -- `/healthz` itself does no I/O. Every number above is a real
measurement taken right after a `scripts/deploy.sh` run (i.e. a guaranteed
cold container), not a synthetic benchmark.

## Full round-trip, warm (representative single calls)

| Call | Observed |
|---|---|
| `GET /static/style.css` | 200, ~12 KB, well under 1s |
| `GET /static/.../confusion_matrix.png` (binary) | 200, ~44 KB, well under 1s |
| `POST /register` + `POST /login` (Cognito `InitiateAuth` round-trip) | 303 redirect, well under 1s |
| `POST /upload` (image normalize + Rekognition `DetectLabels` + DynamoDB write) | ~4.2s total (dominated by Rekognition's own latency, not Lambda) |
| `POST /api/v1/uploads/presign` (no layer, cold-ish) | well under 1s |
| Direct browser `PUT` to the presigned S3 URL | well under 1s (network-bound, not Lambda) |
| `POST /api/v1/classify` (Rekognition `DetectLabels` via S3Object) | ~1-2s, dominated by Rekognition |
| `GET /api/v1/dashboard` (5+ DynamoDB reads, aggregated) | well under 1s |
| `POST /api/v1/chat` (offline-assistant fallback, no network call) | well under 1s |

## What drives the numbers

- The no-layer functions (`classify`, `presign`, `log-waste`, `dashboard`,
  `quiz-scores`) cold-start meaningfully faster than `web`/`chatbot` --
  there's no `fastapi`/`pydantic`/`pillow` import tax, just `boto3` (already
  preloaded in the Lambda Python runtime itself) plus a handful of small
  pure-Python service modules.
- Rekognition's own `DetectLabels` latency (not Lambda, not API Gateway) is
  the single biggest contributor to both `/upload` and `/api/v1/classify`,
  consistent with it being a synchronous ML inference call on AWS's side.
- These are single-request measurements from one location, not a sustained
  load test -- treat them as "what a real user actually experiences," not
  as a capacity benchmark. The new per-route throttles (`docs/DEPLOY_STATUS.md`)
  cap `classify`/`presign` at 2 req/s steady (burst 5) regardless of load.
