# 5-Minute Demo Script

## Setup (before you present)

```bash
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Have a test account already registered and logged in, with a couple of
items already logged on the dashboard so it isn't empty. Keep a photo of
a waste item (a plastic bottle, a battery, anything) ready to upload, and
if your laptop has a webcam, test the camera-capture flow once beforehand.

## Script (~5 minutes)

**0:00 -- Home (20s)**
"This is Haraa -- a waste-management app built for Indian households.
One clear call to action: scan an item. Below that, three steps for how
it works, and live stats pulled straight from the dashboard. These three
tips at the bottom are deliberately India-specific: milk covers, coconut
shells, medicine strips."

**0:20 -- Scan an item (50s)**
*Click "Use camera" or upload a photo.* "This goes to a MobileNetV3 model
I fine-tuned locally on the TrashNet dataset -- it runs on this machine,
no cloud cost. If it's not confident, it automatically falls back to
Amazon Rekognition." *Show the result, click "Log to dashboard".*

**1:10 -- Where does it go? (25s)**
*Type "thermometer" in the search.* "This searches a database of 124
household items -- not just what the camera can recognise, but anything
you can type. Each one has the right bin, prep steps, and what not to do."

**1:35 -- Dashboard (45s)**
*Scroll through.* "Total diverted, CO2 saved, a day streak, a weekly goal
with a progress bar, three 7-day challenges, and a badge shelf -- all
computed from the same events, no extra tracking infrastructure. And a
stacked trend chart by category."

**2:20 -- Segregation game (30s)**
*Play a couple of rounds.* "A quick drag-and-drop game -- sort items into
the right bin before the timer runs out. Best score is saved per user."

**2:50 -- Nearby centres (30s)**
*Click "Find a place near me" from a category.* "This opens a plain
Google Maps search -- no API key, no embedded map, and it never stores
your location. Just city/area typed in, or a one-click 'use my location'
that only asks for permission when you tap it."

**3:20 -- Chatbot (40s)**
*Ask a question.* "The chatbot tries Google Gemini first, falls back to
Amazon Bedrock, then a 124-item offline assistant if neither is
available." *Point at the status line at the bottom of the page.* "This
shows exactly which provider is working right now, and why, in plain
language -- not a raw error message."

**4:00 -- Model Performance + About (40s)**
"This page shows the actual training results -- accuracy, confusion
matrix, per-class precision and recall -- and is honest about the
model's limitations." *Switch to About.* "And this is the full
architecture plus a cost breakdown. The whole thing is designed to run
for cents, not dollars."

**4:40 -- Language switch + dark mode (20s)**
*Switch to Tamil, toggle dark mode.* "Navigation, the home page, and a
few key pages are available in Tamil, and dark mode is a proper second
theme, not just an inverted default."

## Likely viva questions & answers

**Q: Why a local ML model instead of just using Rekognition for everything?**
A: Rekognition is a generic label detector, not trained specifically for
waste categories, and every call costs money. A locally fine-tuned model
is purpose-built for this task, runs for free, and only falls back to
Rekognition when it's genuinely unsure (confidence below 60%).

**Q: Why does the chatbot try three different providers?**
A: Resilience and cost. Gemini is free-tier and the default; Bedrock is a
paid backup if Gemini is unavailable; the offline assistant guarantees
the user always gets an answer, even with no internet or AWS account at
all. Each failure is classified into a plain-English reason (e.g. "key
not set", "rate limit reached") rather than a raw exception, both for the
user-facing status line and for debugging.

**Q: How did you fix the chatbot matching "e-waste" for a generic
question about "waste" statistics?**
A: The offline assistant's fuzzy matcher was tokenizing hyphenated
keywords like "e-waste" into separate words, including the bare word
"waste", which then matched almost any question containing that word. I
added a blocklist of generic words (waste, garbage, trash, rubbish...)
that can never trigger a match on their own, and a separate check for
questions that sound like they want statistics or current events, which
get a clear "ask the online assistant" response instead of a guess.

**Q: Why not use a paid maps API for Nearby Centres?**
A: A plain Google Maps search URL (`maps/search/?api=1&query=...`) needs
no API key, no billing account, and no server-side proxying -- it just
opens Maps in a new tab. That matches the project's zero-cost goal
without sacrificing the core feature (finding a real place nearby).

**Q: How do scan thumbnails work without an S3 bucket?**
A: Each thumbnail is resized to about 96 pixels and stored as a base64
string directly inside the DynamoDB item -- a few KB, well under
DynamoDB's 400KB item limit. It avoids standing up a second AWS service
just to hold small images.

**Q: Is the Tamil translation complete?**
A: No, and that's intentional. Navigation, the home page, and the UI
chrome (headings, buttons, labels) of a few key pages are translated.
The 124-item waste database and the Nearby Centres category descriptions
stay in English -- translating that much domain-specific text reliably
was out of scope, and the Tamil strings should be reviewed by a native
speaker before relying on them beyond a demo.

**Q: How do you keep AWS costs down with all these new features?**
A: Every new feature (scan history, weekly goals, game scores, collection
reminders) reuses the same single on-demand DynamoDB table with a
different partition-key prefix, instead of creating new tables or
services. No S3, no PDF-generation service (the "Download PDF" button
uses the browser's own print-to-PDF), no paid maps API, and the camera
capture runs entirely client-side.

**Q: Is this production-ready?**
A: No -- it's a localhost, single-session demo. Production would need
HTTPS, a reverse proxy, rate limiting, and likely Cognito's Hosted UI
with OAuth instead of direct password-grant calls.
