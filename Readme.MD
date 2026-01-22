# Realtime Speech → Notes (Deepgram + FastAPI)

This project provides **real-time speech-to-text notes** using **Deepgram Live Streaming** with:

- ��️ One **speaker** streaming microphone audio
- �� Multiple **anonymous viewers**
- �� Real-time transcription broadcast via WebSockets
- �� Static frontend (S3-hostable)
- �� FastAPI backend (WebSocket-based)

---

## Architecture Overview

Browser (Speaker / Viewer)
│
│ WebSocket (audio / text)
▼
FastAPI Backend (WebSocket Server)
│
│ WebSocket (audio stream)
▼
Deepgram Live Transcription


- Frontend = static (HTML + JS)
- Backend = FastAPI (must run on a server)
- Deepgram handles speech-to-text in real time

---

## Directory Structure

deepgram-realtime-notes/
│
├── .env
├── requirements.txt
├── server.py
│
└── public/
├── index.html
└── client.js

> ⚠️ There is **NO `static/` directory on disk**
> `/static` is a **URL mount**, mapped to the `public/` folder.

---

## Prerequisites

- Python **3.10+** (tested with 3.11 / 3.13)
- A **Deepgram API key**
- Chrome / Edge browser (for MediaRecorder WebM/Opus support)

---

## 1. Clone & Setup Environment

```bash
git clone <your-repo-url>
cd deepgram-realtime-notes

Create virtual environment:
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# OR
.venv\Scripts\activate           # Windows

2. Install Dependencies
pip install -r requirements.txt

requirements.txt

fastapi
uvicorn[standard]
websockets
python-dotenv

⚠️ Important

The websockets package recently changed its API.
This project includes compatibility logic so it works across versions.

3. Configure Environment Variables

Create a .env file:

DEEPGRAM_API_KEY=YOUR_DEEPGRAM_API_KEY

Do NOT put this key in frontend code.

4. Run the Backend Server

uvicorn server:app --host 0.0.0.0 --port 3000 --reload
You should see:
INFO:     Uvicorn running on http://127.0.0.1:3000

5. Open the Application

Open two browser tabs:

http://localhost:3000

Tab A (Speaker)

Room: demo

Mode: Speaker (mic)

Click Connect

Allow microphone access

Start talking ��

Tab B (Viewer)

Room: demo

Mode: Viewer

Click Connect

Watch notes appear in real time ��

6. How It Works (Important Details)
Audio Format

Browser uses: audio/webm;codecs=opus

Deepgram automatically detects this format

Do NOT set encoding or sample_rate on the backend

WebSocket KeepAlive

Deepgram closes idle connections after ~10s

Backend sends {"type": "KeepAlive"} every ~3.5s

One Deepgram Connection Per Room

All viewers subscribe to the same transcription stream

One active speaker recommended per room

Common Errors & Fixes
❌ App closes immediately on connect

Cause: websockets.connect() API mismatch

Fix:
This project includes a compatibility layer that automatically switches between:

extra_headers

additional_headers

No action needed unless you removed it.

❌ AssertionError: scope["type"] == "http"

Cause: Static files mounted at /

Fix:
Static files are mounted at /static, not /.

app.mount("/static", StaticFiles(directory="public"), name="static")

❌ No transcription appears

Check:

Microphone permission granted

Browser supports WebM/Opus (Chrome does)

Deepgram API key is valid

You are actually speaking (Deepgram won’t transcribe silence)

Hosting in Production
Frontend (Static)

✅ Can be hosted on:

Amazon S3

CloudFront

Any static hosting provider

Backend (Required)

❌ Cannot be hosted on S3
✅ Must run on:

EC2

ECS Fargate (recommended)

App Runner

Elastic Beanstalk

WebSockets are required for real-time audio streaming.

Security Considerations (Important)

If your UI is public:

Anyone can connect and stream audio

You are billed by Deepgram usage

Recommended protections:

Single active speaker per room

Room access tokens

Rate limiting

IP throttling

Next Enhancements (Optional)

✅ Deepgram built-in translation (translate=es)

�� Transcript persistence (late join replay)

�� Speaker lock / moderator mode

�� Multiple languages per viewer

�� Docker + ECS deployment

License

MIT (or your preferred license)

Support

If you hit issues:

Copy the exact error log

Include your Python version

Include pip show websockets

This will allow fast debugging.
