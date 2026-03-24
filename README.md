# 📥 Instagram Reel Downloader API

A production-ready FastAPI backend for downloading Instagram Reels via a simple HTTP endpoint.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Framework** | FastAPI with async support |
| **Downloader** | yt-dlp (battle-tested, actively maintained) |
| **Format** | Best available MP4 (video + audio merged) |
| **CORS** | Configurable via environment variable |
| **Error Handling** | Structured JSON errors with hints |
| **Logging** | Timestamped, leveled, session-tagged logs |
| **Cleanup** | Downloaded files auto-deleted after serving |
| **Docker** | Multi-stage Dockerfile + docker-compose |

---

## 🗂 Project Structure

```
instagram_downloader/
├── app/
│   ├── main.py              # FastAPI app factory & CORS
│   ├── core/
│   │   ├── config.py        # Settings from environment
│   │   ├── exceptions.py    # Custom exception hierarchy
│   │   └── logging.py       # Centralized logger
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   ├── routes/
│   │   └── download.py      # Route handlers (GET /health, POST /download)
│   └── services/
│       └── downloader.py    # yt-dlp async download logic
├── downloads/               # Temporary file storage (auto-created)
├── run.py                   # Local dev server launcher
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# ffmpeg is also required for video+audio merging:
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS:         brew install ffmpeg
# Windows:       https://ffmpeg.org/download.html
```

### 2. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env as needed
```

### 3. Run the server

```bash
python run.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Open the interactive docs

```
http://localhost:8000/docs
```

---

## 🐳 Docker

```bash
# Build and start
docker-compose up --build

# Stop
docker-compose down
```

---

## 📡 API Reference

### `POST /download`  *(also available at `/api/v1/download`)*

Downloads an Instagram Reel and streams it back as an MP4 file.

**Request body:**
```json
{
  "url": "https://www.instagram.com/reel/C_exampleABC/"
}
```

**Success response:**  `200 OK` — binary `video/mp4` stream with `Content-Disposition: attachment`.

**Error responses:**

| HTTP Code | `error` field | Cause |
|---|---|---|
| `422` | `INVALID_URL` | URL doesn't match Instagram Reel pattern |
| `403` | `PRIVATE_CONTENT` | Reel is from a private account |
| `413` | `FILE_TOO_LARGE` | Video exceeds `MAX_FILE_SIZE_MB` |
| `502` | `DOWNLOAD_FAILED` | Network issue or yt-dlp failure |
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected server error |

---

### `GET /health`  *(also at `/api/v1/health`)*

Liveness probe. Returns `200 OK` when the service is running.

```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "Instagram Reel Downloader"
}
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `false` | Enable debug logging & hot-reload |
| `ALLOWED_ORIGINS` | `*` | Comma-separated CORS origins |
| `MAX_FILE_SIZE_MB` | `500` | Max download size in MB |
| `DOWNLOAD_TIMEOUT` | `120` | yt-dlp socket timeout in seconds |

---

## 🧪 cURL Example

```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/XXXXXXXXXX/"}' \
  --output reel.mp4
```

---

## ⚠️ Legal Notice

This tool is for **personal use only**. Downloading content you do not own may violate Instagram's Terms of Service and applicable copyright laws. Always respect the original creator's rights.
