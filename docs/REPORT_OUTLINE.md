# Project Report Outline: Haraa -- A Household Waste Management Web Application

*This outline is filled in with the real details of this project. Expand each section with your own screenshots, reflections, and any course-specific requirements. See `docs/SCREENSHOTS.md` for which pages to capture.*

## Abstract

Haraa is a localhost-deployed waste-management web application for Indian
households, combining cloud services (Amazon Cognito, DynamoDB,
Rekognition, Bedrock) with a locally fine-tuned computer-vision model and
Google Gemini to help users identify, log, and learn about waste
disposal. The system classifies photographed waste items using a
MobileNetV3-Large model fine-tuned on the TrashNet dataset, falling back
to Amazon Rekognition when confidence is low, and provides a
conversational assistant that tries Gemini, then Bedrock, then a
124-item offline knowledge base, in that order. Beyond classification,
the application includes a searchable 124-item disposal database, a
gamified dashboard (weekly goals, 7-day challenges, badges, streaks), a
drag-and-drop segregation game, a 2-minute household waste audit, a
Nearby Centres finder built on plain Google Maps search links, collection
reminders with calendar export, and partial English/Tamil
internationalisation. The entire system is designed to run at near-zero
ongoing cloud cost.

## 1. Introduction

### 1.1 Background
Municipal and household waste management is a growing challenge,
particularly in rapidly urbanising regions. Correct waste segregation at
the source significantly improves recycling rates, yet many people are
unsure which bin or disposal route a given item belongs to, especially
for items specific to Indian households (milk covers, coconut shells,
puja/flower waste, medicine strips) that generic waste-management
resources don't cover.

### 1.2 Problem Statement
Users often lack an easy way to (a) identify what category a waste item
falls into, (b) understand correct segregation and disposal practices
specific to their context, (c) find a physical place to take specialised
waste (e-waste, hazardous, biomedical), and (d) stay motivated to keep
doing it over time.

### 1.3 Objectives
1. Build a photo-based waste classifier that works offline/locally, with
   a text-search fallback over a large item database.
2. Provide an authenticated web experience with a persistent dashboard
   of waste diverted, environmental impact, and engagement features
   (goals, challenges, badges) that encourage sustained use.
3. Provide an educational hub (types of waste, the 3Rs, segregation,
   composting, e-waste, plastic, biomedical waste) with self-assessment
   quizzes, a self-check audit, and a drag-and-drop game.
4. Help users find real, physical disposal locations without relying on
   a paid mapping API.
5. Integrate a conversational assistant with automatic multi-provider
   fallback and transparent status reporting.
6. Support more than one language for the core user journey.
7. Keep the entire system runnable on localhost at near-zero AWS cost.

### 1.4 Scope
The system is a single-user-session, localhost-only demo application. It
is not designed for multi-tenant production deployment, horizontal
scaling, or public internet exposure. Tamil translation covers
navigation and core page chrome, not the full item database (see
Limitations).

## 2. Literature Review

- **TrashNet** (Yang & Thung, 2016) -- the original dataset and baseline
  classifier for 6-class waste image classification, used here as the
  training set.
- **Transfer learning for image classification** -- fine-tuning
  ImageNet-pretrained CNNs is a standard, data-efficient approach when
  the target dataset (~2,500 images here) is too small to train a CNN
  from scratch.
- **MobileNetV3** (Howard et al., 2019) -- a mobile-efficient CNN
  architecture, selected for its balance of accuracy and inference speed
  on consumer hardware (the model runs entirely on the user's own
  machine, including Apple Silicon GPU via MPS).
- **Conversational AI fallback patterns** -- using a chain of providers
  (a primary LLM, a secondary LLM, and a deterministic offline fallback)
  is a common resilience pattern in production AI systems, applied here
  across Google Gemini, Amazon Bedrock, and a rule-based assistant.
- **Gamification in sustainability apps** -- streaks, goals, challenges
  and badges are widely used (e.g. fitness and habit-tracking apps) to
  sustain long-term user engagement with repetitive, low-immediate-reward
  behaviours like waste sorting.
- **Municipal solid waste management practice** -- India's Solid Waste
  Management Rules, 2016, and Bio-Medical Waste Management Rules, 2016,
  which inform this project's Learn, Sorting Guide, and Nearby Centres
  content (bin-colour conventions, segregation categories, hazardous
  item handling).
- **Cloud-native application patterns** -- using managed identity
  (Cognito), managed NoSQL (DynamoDB, as a single table across many
  feature types), and managed AI services (Rekognition, Bedrock, Gemini)
  to avoid operating custom infrastructure.

## 3. System Architecture

```
Browser --> FastAPI app (localhost:8000) --> Amazon Cognito (login/registration)
                                          --> Amazon DynamoDB (dashboard events, scan history,
                                                                goals, game scores, reminders, quiz scores)
                                          --> Amazon Rekognition (fallback image labelling)
                                          --> Google Gemini (chatbot, primary provider)
                                          --> Amazon Bedrock (chatbot fallback, Claude Haiku)
                                          --> Local MobileNetV3 model (primary image classifier, in-process)
```

The application is a single FastAPI process. Session-based authentication
(a signed cookie) gates all pages. The photo-upload endpoint tries the
local PyTorch model first; if its top-class confidence is below 60%, it
calls Amazon Rekognition as a fallback. The chatbot endpoint tries Gemini,
then Bedrock, then a local rule-based responder, classifying any failure
along the way into a short, plain-English reason shown to the user via a
`/api/chatbot/health` endpoint and a "Chat status" indicator. All new
feature state (scan history, goals, game scores, reminders) is stored in
the same single DynamoDB table using distinct partition-key prefixes,
rather than provisioning additional tables.

See `app/templates/about.html` (the About page) for the diagram as
rendered in the app, and its cost summary table for a per-service cost
breakdown.

## 4. Methodology

### 4.1 Dataset
TrashNet (`garythung/trashnet` on Hugging Face), 2,527 labelled images
across 6 classes: cardboard (403), glass (501), metal (410), paper (594),
plastic (482), trash (137). Split 80/10/10 (stratified per class) using
`ml/split_dataset.py`.

### 4.2 Model & Training
- Architecture: MobileNetV3-Large, ImageNet-pretrained, classifier head
  replaced with a `Linear` layer for 6 classes.
- Two-phase transfer learning: (1) backbone frozen, train only the new
  head for 4 epochs at lr=1e-3; (2) unfreeze the full network, fine-tune
  for 10 epochs at lr=1e-4.
- Data augmentation: random resized crop, horizontal flip, rotation,
  colour jitter.
- Class-weighted cross-entropy loss to counter the "trash" class's
  smaller sample count.
- Training hardware: Apple Silicon GPU via PyTorch's MPS backend (falls
  back to CPU automatically if unavailable).
- Best checkpoint selected by validation accuracy; final metrics computed
  on the held-out test set. See the live Model Performance page for the
  actual numbers from the most recent run.

### 4.3 Inference pipeline
Uploaded or camera-captured photos (JPEG/PNG/WebP/HEIC) are decoded and
normalized with Pillow + pillow-heif, resized if oversized, and
re-encoded as JPEG. The local model classifies first; if confidence is
below 60%, the same normalized JPEG is sent to Amazon Rekognition's
`DetectLabels`, and the returned labels are mapped onto the app's waste
categories via keyword matching.

### 4.4 Shared item database
A 124-item household waste database (`app/services/waste_items_data.py`)
is the single source of truth for both the offline chatbot's knowledge
base and the "Where does it go?" search page, so the two features never
disagree. Each item has a title, matching keywords, its correct bin,
step-by-step prep instructions, and a "do not" note.

### 4.5 Offline chatbot matching
The offline assistant matches a user's question against the item database
by exact substring first, then by fuzzy matching (Python's `difflib`) on
individual words, with two safeguards: a blocklist of generic words
(waste, garbage, trash, rubbish, bin...) that can never trigger a match
alone, discovered after a real bug where "how much waste is produced
globally" matched the "e-waste" item purely because "waste" is a
substring of it; and a separate detector for statistics/current-events-
shaped questions, which get a clear "ask the online assistant" response
rather than a fabricated answer.

### 4.6 Gamification
Weekly goals, 7-day challenges, and badges are all computed on read from
existing dashboard events rather than maintaining separate counters,
except for the one user-set value (the weekly goal target itself), which
is stored per user.

### 4.7 AWS integration
- **Cognito**: `sign_up` + `admin_confirm_sign_up` for registration
  (auto-confirmed for localhost convenience), `initiate_auth` with
  `USER_PASSWORD_AUTH` for login.
- **DynamoDB**: a single on-demand table (`WasteMgmt`) with a generic
  `PK`/`SK` design, partition-key prefixes separating dashboard events
  (`EVENT`), aggregate stats (`STATS`), scan history (`SCAN#<email>`),
  weekly/game state (`GOAL#<email>`, `GAME#<email>`), reminder settings
  (`SETTINGS#<email>`), and quiz scores (`QUIZ#<email>`).
- **Rekognition**: `detect_labels` on raw image bytes (no S3 bucket
  needed, including for scan thumbnails, which are stored inline in
  DynamoDB as base64).
- **Bedrock**: `converse` API against `anthropic.claude-haiku-5-5` in
  `ap-south-1`.
- **Gemini**: the `google-genai` SDK's `models.generate_content`, model
  configurable via `GEMINI_MODEL` (default `gemini-3.5-flash-lite`).

## 5. Implementation Details

- **Backend**: Python 3.12, FastAPI, Jinja2 templates (via a single
  shared `Jinja2Templates` instance with a `context_processors` hook for
  i18n, and a custom `icon()` template global for locally bundled SVG
  icons), Starlette session middleware (signed cookie).
- **Frontend**: server-rendered HTML + Bootstrap 5 grid/utilities with a
  fully custom design system on top (Fraunces + Inter fonts, a warm
  forest/clay/sand/marigold palette, Lucide SVG icons bundled locally, no
  icon-font CDN), Chart.js for the dashboard trend chart, vanilla JS for
  interactivity (no build step).
- **Camera capture**: `getUserMedia` + a `<canvas>` to capture a frame,
  converted to a `File` via the `DataTransfer` API so it flows through
  the same multipart form submission as a regular file upload.
- **i18n**: a small dictionary-based translator with English and Tamil
  string tables, injected into every template via a Jinja2
  `context_processor`; the chosen language is stored in both the session
  and a long-lived cookie.
- **ML**: PyTorch + torchvision, trained in an isolated `ml/.venv`
  (Python 3.12) kept separate from the app's own `.venv`; inference
  artifacts are copied into `app/ml_model/` after training.
- **Testing**: pytest + FastAPI's `TestClient`, covering auth-gated route
  redirects and pure-logic services: the fallback chatbot (including the
  generic-word regression test), Google Maps URL encoding, gamification
  logic, the weekly report, collection-reminder `.ics` generation, and
  i18n key-completeness between English and Tamil.

## 6. Results

See the **Model Performance** page in the running app (`/model-performance`)
for the live numbers from the most recent training run: test accuracy,
per-class precision/recall/F1, the confusion matrix, training curves, and
sample predictions. (Fill in your actual run's numbers here for the
written report, e.g. by screenshotting that page.)

## 7. Limitations

- TrashNet's 6 classes don't include a dedicated organic or e-waste
  class; this project maps `cardboard -> paper` and `trash -> other` as
  an approximation.
- ~2,500 training images is small by deep-learning standards; real-world
  photos (varied lighting, backgrounds, phone cameras) will likely see
  lower accuracy than the clean TrashNet test set suggests.
- The CO2/water/energy/trees-saved and weekly-report figures are
  illustrative, rounded, commonly cited factors, not a certified
  life-cycle assessment.
- NPTEL video content could not be linked at the individual-lecture level
  without risking broken/guessed links, so the Watch & Learn page links
  to course pages instead.
- Tamil translation is intentionally partial: navigation, the home page,
  and the UI chrome of three key pages. The 124-item database and the
  Nearby Centres category descriptions remain in English, and the
  translated strings have not been reviewed by a native speaker.
- "Download PDF" on the weekly report uses the browser's native
  print-to-PDF rather than a server-side PDF library, by design (keeps
  the system dependency-light and free).
- This is a single-session, localhost-only demo -- no production
  hardening (rate limiting, multi-tenant isolation, HTTPS termination) is
  included.

## 8. Future Work

- Expand the training dataset with region-specific waste photos to cover
  organic and e-waste classes directly rather than via category mapping.
- Complete Tamil (and potentially Hindi) translation of the full item
  database and Nearby Centres content, reviewed by native speakers.
- Add a server-rendered PDF export for the weekly report, for users whose
  browsers don't support print-to-PDF well.
- Add per-user historical trend comparisons and multi-week goal tracking
  on the dashboard.
- Deploy behind HTTPS with a managed Cognito Hosted UI for a
  production-ready multi-user version.

## 9. References

1. Thung, G., & Yang, M. (2016). *TrashNet: Classification of Trash for
   Recyclability Status.* (Dataset: `garythung/trashnet` on Hugging Face.)
2. Howard, A., et al. (2019). *Searching for MobileNetV3.* ICCV 2019.
3. Government of India, Ministry of Environment, Forest and Climate Change.
   *Solid Waste Management Rules, 2016.*
4. Government of India, Ministry of Environment, Forest and Climate Change.
   *Bio-Medical Waste Management Rules, 2016.*
5. AWS Documentation -- Amazon Cognito, Amazon DynamoDB, Amazon
   Rekognition, Amazon Bedrock (official service documentation,
   docs.aws.amazon.com).
6. Google AI for Developers -- Gemini API documentation (ai.google.dev).
7. NPTEL course pages referenced in `app/services/nptel_data.py`.
8. iCalendar (RFC 5545) -- the `.ics` format used for collection-reminder
   calendar export.
