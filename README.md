# Haraa

*Sort smart. Waste less.*

A localhost-only waste-management web app built for Indian households.
Point a camera at a milk packet, a dead battery, or a broken thermometer
and get a straight answer: which bin it goes in, what to do with it, and
where to take it if it needs a special drop-off. Built as a final-year
project combining AWS-backed services (login, dashboard, chatbot, image
labelling) with a locally fine-tuned computer-vision model, a custom
design system, and a set of practical household tools.

## Features

- **Home** -- a calm hero with one call to action, three "how it works" steps, a live impact strip, and a few India-specific household tips.
- **Scan an item** -- classifies a photo with a **locally fine-tuned MobileNetV3-Large model** first (camera capture or file upload); if its confidence is below 60%, falls back to Amazon Rekognition. Handles JPEG/PNG/WebP/HEIC, auto-converts and resizes, and rejects non-images with a friendly message.
- **Where does it go?** -- search over 124 household items for the correct bin, prep steps, and a "do not" note.
- **My scans** -- your scan history with thumbnails (stored inline in DynamoDB, no S3 needed) and one-click "log to dashboard".
- **Learn** -- 7 sections (waste types, the 3Rs, segregation & India's bin-colour system, composting, e-waste, plastic, biomedical waste), each with a 3-question quiz; best scores saved per user.
- **Watch & learn** -- verified official NPTEL course pages for waste management & environmental engineering (no guessed video links).
- **News** -- live headlines from 3 Google News RSS feeds, cached hourly, with search/topic filters; falls back to a curated list if the feeds are unreachable.
- **Composting & DIY** -- step-by-step home composting, a kitchen bin setup, and upcycling ideas, with labelled image placeholders for your own photos.
- **Sorting guide** -- do's/don'ts and which bin to use per category, with a "find a place near me" shortcut.
- **Impact calculator** -- converts recycled kg into trees/water/energy/CO2 saved, formulas shown on the page.
- **Waste audit** -- an 8-question, 2-minute self-check producing a score and your top 3 improvements, with a printable summary.
- **Segregation game** -- drag-and-drop (or tap, for touch/accessibility) items into the right bin against a 60-second timer; best score saved per user.
- **Nearby centres** -- 9 categories (e-waste, scrap dealers/kabadiwala, hazardous collection, medicine take-back, composting units, municipal transfer stations, plastic/textile/glass recycling), each with what to bring/not bring and a tip. Links are plain Google Maps searches (`maps/search/?api=1&query=...`) -- no API key, no embedded map. "Use my current location" asks for Geolocation permission only on click and never stores coordinates.
- **Dashboard** -- cumulative waste saved, CO2 avoided, recycling rate, a day-streak counter, a weekly goal with progress bar, three 7-day challenges, a badge shelf, a stacked trend chart, a leaderboard (by email prefix only), and a CSV export.
- **Weekly report** -- items/kg/CO2 this week vs last week, with a "Download PDF" button (opens the browser's print dialog, pre-styled -- no PDF-generation dependency).
- **Collection reminders** -- set your area's wet/dry collection weekdays, get an in-app "today/tomorrow" banner, and download a `.ics` calendar file.
- **Poster** -- a printable A4 segregation reference sheet.
- **Ask Haraa (chatbot)** -- **Google Gemini** (default provider) with suggested questions, a typing indicator, and automatic fallback to **Amazon Bedrock** (`anthropic.claude-haiku-5-5`) and then a built-in offline assistant (124-item knowledge base, fuzzy-matched, generic-word-safe) if needed. A small "Chat status" indicator shows which provider is working. Restricted by its system prompt to waste-management topics, and always directs hazardous items to authorised collection points.
- **Model Performance** -- accuracy, per-class precision/recall/F1, confusion matrix, training curves, sample predictions, and documented limitations.
- **About** -- architecture diagram, component roles, and a cost summary.
- **English / Tamil** language switch for navigation, the home page, and the "Where does it go?"/Nearby Centres/Sorting Guide UI chrome, remembered via a cookie. (See the note under "What's unverified" below.)
- A custom design system (Fraunces + Inter, a warm forest/clay/sand/marigold palette, locally bundled Lucide icons, hand-drawn-style SVG illustrations), light/dark mode, and a friendly 404 page.

Everything runs on `127.0.0.1` only. AWS credentials are never read from or
written to any file in this project -- boto3 uses whatever credentials are
already configured on your machine.

## Architecture at a glance

```
Browser --> FastAPI app (localhost:8000) --> Amazon Cognito (login)
                                          --> Amazon DynamoDB (dashboard, scans, goals, game scores, reminders, quiz data)
                                          --> Amazon Rekognition (fallback image labels)
                                          --> Google Gemini (chatbot, primary provider)
                                          --> Amazon Bedrock (chatbot fallback, Claude Haiku)
                                          --> Local MobileNetV3 model (primary image classifier, in-process)
```

Chatbot provider order is controlled by `CHATBOT_PROVIDER` in `.env`:
`auto` (Gemini -> Bedrock -> offline, the default), `gemini` (Gemini ->
offline), `bedrock` (Bedrock -> offline), or `offline` (offline only).

## Cost

Designed to add no meaningful ongoing AWS cost:

- Cognito: free for the first 50,000 monthly active users.
- DynamoDB: on-demand billing mode, a few cents at most for demo-scale traffic. Everything new in this app (scan thumbnails, goals, game scores, reminders) reuses the same single table.
- Rekognition: ~$1 per 1,000 images, and it's only called when the local model's confidence is low.
- Gemini (Flash): free tier, generous daily limits -- $0 for normal demo use.
- Bedrock (Claude Haiku): fractions of a cent per chat message, and only used if Gemini is unavailable.
- The ML model trains and runs entirely on your own machine (CPU or Apple GPU/MPS) -- $0.
- No EC2, Lambda, API Gateway, or S3 buckets are created. Nothing runs on a schedule or auto-scales, so idle cost is $0.

## 1. Prerequisites

- macOS (Apple Silicon recommended for MPS-accelerated training, but CPU works too), or Linux/Windows with CUDA/CPU.
- `uv` (https://docs.astral.sh/uv/) for managing the two Python environments this project uses. Install with `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- AWS credentials already configured on this machine (`aws configure`, environment variables, or SSO) with permissions for Cognito, DynamoDB, Rekognition, and Bedrock in `ap-south-1`.
- (Optional, recommended) A free Gemini API key from https://aistudio.google.com/apikey for the chatbot's primary provider. Without it, the chatbot skips Gemini and uses Bedrock, then the offline assistant.

### Why two Python environments?

- **`.venv/`** (project root, Python 3.12): runs the FastAPI app itself, including loading the trained PyTorch model for inference.
- **`ml/.venv/`** (Python 3.12, separate from the app's): used only for training -- it has extra heavy dependencies (`scikit-learn`, `matplotlib`, `tqdm`) that the running app doesn't need.

Both were created with `uv venv --python 3.12`, since very new Python
versions (e.g. 3.15) may not yet have PyTorch wheels available.

## 2. Install dependencies

```bash
cd waste-mgmt

# App environment
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# ML training environment (separate, only needed to (re)train the model)
cd ml
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python torch torchvision scikit-learn matplotlib pillow pillow-heif tqdm
cd ..
```

## 3. Provision AWS resources (one time)

Creates a Cognito User Pool + App Client and a DynamoDB table in your AWS
account, using your existing AWS credentials. Safe to re-run (skips
anything that already exists; never deletes anything).

```bash
.venv/bin/python scripts/setup_aws.py
```

This writes the created resource IDs (not secrets) into `.env`.

## 4. Chatbot setup (Gemini / Bedrock / offline)

Secrets go in `.env.local` -- gitignored, and **never written to by this
app**; only you edit it. Copy the example and fill in your key:

```bash
cp .env.local.example .env.local
# then edit .env.local and set:
#   GEMINI_API_KEY=your-key-from-aistudio.google.com
```

Config loads in this order (highest priority first): real environment
variables, then `.env.local`, then `.env`. If `GEMINI_API_KEY` is unset
everywhere, the chatbot simply skips Gemini and uses Bedrock (or the
offline assistant) instead -- no error, just reported as "not set".

### Diagnosing chatbot provider issues

If the chatbot always answers via the offline assistant and you're not
sure why:

```bash
.venv/bin/python scripts/diagnose_chatbot.py
```
Loads config the same way the app does, reports only "set"/"not set" for
`GEMINI_API_KEY` (never the value), makes a real call to Gemini and to
Bedrock with your configured models, and reports the outcome for each.

Or, with the app running, visit `GET /api/chatbot/health` (while logged
in) for a live JSON status of each provider, e.g.:
```json
{"gemini": {"available": true, "reason": null},
 "bedrock": {"available": false, "reason": "Bedrock: access not enabled on this AWS account"},
 "offline": {"available": true, "reason": null}}
```
The same plain-English reasons also appear in the "Chat status"
indicator on the chatbot page and the About page.

## 5. Train the waste classifier (one time, ~a few minutes)

```bash
cd ml
.venv/bin/python split_dataset.py
.venv/bin/python train.py
cd ..
```

`split_dataset.py` expects the TrashNet dataset already extracted at
`ml/data_raw/dataset-resized/<class>/*.jpg`. Download it once from Hugging
Face:

```bash
mkdir -p ml/data_raw
curl -L -o ml/data_raw/trashnet.zip \
  https://huggingface.co/datasets/garythung/trashnet/resolve/main/dataset-resized.zip
unzip -q ml/data_raw/trashnet.zip -d ml/data_raw
rm ml/data_raw/trashnet.zip
rm -rf ml/data_raw/__MACOSX
```

`train.py` fine-tunes a pretrained MobileNetV3-Large in two phases (frozen
backbone, then full fine-tune), runs on Apple GPU (MPS) automatically if
available, and writes training artifacts plus copies them into
`app/ml_model/` and `app/static/model_report/` so the running app and the
Model Performance page can use them without needing scikit-learn/matplotlib
installed.

If you skip this step, Scan an item still works -- it just uses Amazon
Rekognition for every image, and the Model Performance page shows a
"not trained yet" message instead of charts.

## 6. Run the app

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000, register an account, log in, and explore the
pages listed above from the navbar.

## 7. Run the tests

```bash
.venv/bin/python -m pytest tests/ -q
```

These tests don't touch AWS or Gemini: protected-page tests only exercise
the session-check-then-redirect path, and service-level tests cover the
fallback chatbot (including fuzzy matching and the generic-word guard),
waste-item data, impact-calculator formulas, image validation, Google Maps
URL encoding, gamification logic (goals/challenges/badges), the weekly
report, collection reminders (including `.ics` generation), and i18n
key-completeness -- all pure-logic or mocked, no real AWS/Gemini calls.

## Screenshots for your report

See `docs/SCREENSHOTS.md` for the full list of pages to screenshot and why
each one is worth including.

## Serverless AWS deployment (`aws-deploy` branch)

This `main` branch stays localhost-only. The `aws-deploy` branch adds a
separate, self-contained serverless deployment (CloudFront + API Gateway +
7 Lambda functions + its own Cognito pool and DynamoDB table) via AWS SAM:

```
git checkout aws-deploy
scripts/deploy.sh      # one command: builds (no Docker) and deploys the whole stack
scripts/destroy.sh     # one command: tears all of it back down
```

See `docs/ARCHITECTURE.md` (diagram + design rationale), `docs/SECURITY.md`
(IAM role-by-role breakdown), and `docs/COST.md` (per-service estimate).

## Notes

- Registration auto-confirms the Cognito user immediately (no email link) since this is a localhost demo, not a production deployment.
- The browser session cookie is signed with a `SESSION_SECRET` generated automatically on first run and stored in `.env` -- a local secret for signing cookies, not an AWS credential.
- Dashboard "CO2 saved", Impact Calculator, and Weekly Report figures use simple illustrative per-kg factors -- not a certified life-cycle assessment.
- Scan thumbnails are tiny (~96px) JPEGs stored inline in DynamoDB, not in S3 -- keeps the architecture simple and the cost at $0 for this feature.
- To retrain with different hyperparameters, edit the constants at the top of `ml/train.py` and re-run it.
- To tear down AWS resources when you're done: delete the Cognito user pool and the `WasteMgmt` DynamoDB table from the AWS Console (or CLI) in `ap-south-1`.

## What doesn't work / couldn't be fully verified

- **Gemini chatbot**: requires your own `GEMINI_API_KEY` in `.env.local` or a real environment variable. Without it, the chatbot reports "Gemini: key not set" and falls back automatically.
- **Bedrock chatbot**: as of this build, Bedrock's `Converse` API returns `AccessDenied`/`ValidationException` ("Operation not allowed") for the account this was developed against, consistent with model access still being verified. The chatbot falls back to the next provider automatically -- check the Bedrock console under "Model access" once your account is cleared.
- **NPTEL videos**: we could not independently verify stable YouTube video IDs for individual NPTEL lectures, so the Watch & Learn page links to each course's official NPTEL page/syllabus instead of embedding specific videos.
- **RSS news feeds**: depend on Google News' RSS endpoint being reachable at runtime; falls back to a curated list automatically if not.
- **Local ML model accuracy**: trained on ~2,500 TrashNet images across 6 classes with no dedicated organic/e-waste class -- see the Model Performance page's "Limitations" section.
- **Tamil translations**: cover navigation, the home page, and the UI chrome (headings, buttons, bin-type names) of "Where does it go?", Nearby Centres, and the Sorting Guide. The 124-item database and the 9 Nearby Centres category descriptions are intentionally left in English -- translating that much domain-specific text reliably was out of scope for this pass. A native Tamil speaker should review the translated strings in `app/services/i18n.py` before relying on them beyond a demo.
- **Weekly report PDF**: "Download PDF" opens the browser's print dialog pre-styled for printing; the user chooses "Save as PDF" as the destination. No server-side PDF-generation library is used, by design (keeps dependencies light and cost at $0).
- Camera capture (`getUserMedia`) requires a browser that supports it and permission granted by the user; it falls back cleanly to file upload if denied or unsupported.

## Exact command to start the app

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
