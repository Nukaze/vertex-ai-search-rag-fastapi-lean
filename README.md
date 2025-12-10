# Vertex AI Search RAG API (Lean)

Standalone FastAPI service for **Vertex AI Search** with **RAG (Retrieval-Augmented Generation)** and **Gemini streaming**.

Extracted from the 9Expert MVP monorepo as a single-purpose, production-ready microservice.

---

## Features

✅ **Dual Mode Support**
- **Streaming Mode**: RAG from Vertex AI → Stream via Gemini (Server-Sent Events)
- **Direct Mode**: Get AI summary directly from Vertex AI (JSON response)

✅ **Production Ready**
- Singleton service pattern (reuse GCP credentials)
- Automatic token refresh (proactive 5-minute buffer)
- Clean citation formatting with metadata parsing
- Comprehensive error handling

✅ **Minimal Dependencies**
- Only essential packages (FastAPI, Gemini, Google Auth, httpx)
- No bloat from other services

---

## Project Structure

```
vertex-ai-search-rag-fastapi-lean/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings & environment variables
│   ├── models/
│   │   ├── __init__.py
│   │   └── vertex_search.py       # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── vertex_search.py       # /api/vertex-search endpoint
│   └── services/
│       ├── __init__.py
│       └── vertex_ai_service.py   # Vertex AI & Gemini integration
├── requirements.txt               # Minimal dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## API Endpoints

### Health Check
```
GET /
Response: {
  "status": "ok",
  "service": "Vertex AI Search RAG API",
  "version": "1.0.0",
  "endpoints": {...}
}
```

### Vertex AI Search (Streaming Mode)
```bash
POST /api/vertex-search
Content-Type: application/json

{
  "query": "คอร์สอะไรเหมาะกับผู้เริ่มต้นเรียน Data Analytics",
  "mode": "streaming",
  "pageSize": 5,
  "model": "gemini-2.0-flash"
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"chunk":"ส","done":false}
data: {"chunk":"ำหรับผู้เริ่มต้น","done":false}
...
data: {"chunk":"","done":true,"citations":[...],"responseTime":5.2}
```

### Vertex AI Search (Direct Mode)
```bash
POST /api/vertex-search
Content-Type: application/json

{
  "query": "เรียน Power BI ต้องมีพื้นฐานอะไรบ้าง",
  "mode": "direct",
  "pageSize": 3
}
```

**Response:** JSON
```json
{
  "success": true,
  "mode": "direct",
  "query": "เรียน Power BI ต้องมีพื้นฐานอะไรบ้าง",
  "summary": "สำหรับการเรียน Power BI คุณควรมีพื้นฐาน Excel...",
  "citations": [
    {
      "id": "ai-faqs",
      "title": "คำถามที่พบบ่อย",
      "source_type": "faq",
      "url": null,
      "snippet": "แบบทดสอบหลังเรียนเกิน 70%..."
    }
  ],
  "totalResults": 8,
  "responseTime": 2.45
}
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- Google Cloud Platform account with Vertex AI Search enabled
- Gemini API key (for streaming mode)

### 1. Clone & Navigate
```bash
cd vertex-ai-search-rag-fastapi-lean
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# Required variables:
# - GEMINI_API_KEY
# - GCP_PROJECT_ID
# - GCP_SERVICE_ACCOUNT_KEY (JSON minified to single line)
# - VERTEX_SEARCH_ENGINE_ID
# - VERTEX_SEARCH_LOCATION (optional, default: global)
```

### 5. Run the API
```bash
uvicorn app.main:app --reload --port 8000
```

API will be available at:
- **Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key (get from [AI Studio](https://aistudio.google.com/app/apikey)) |
| `GCP_PROJECT_ID` | ✅ Yes | Google Cloud Platform project ID |
| `GCP_SERVICE_ACCOUNT_KEY` | ✅ Yes | JSON service account key (minified to single line) |
| `VERTEX_SEARCH_ENGINE_ID` | ✅ Yes | Vertex AI Search engine ID |
| `VERTEX_SEARCH_LOCATION` | ❌ No | Vertex AI Search location (default: `global`) |

### How to Minify GCP Service Account Key
```bash
# Download your service account JSON from GCP Console
# Then minify it (remove all newlines):

# On Linux/Mac:
cat service-account.json | jq -c . > service-account-minified.json

# On Windows (PowerShell):
(Get-Content service-account.json -Raw | ConvertFrom-Json | ConvertTo-Json -Compress) | Out-File service-account-minified.json

# Copy the entire line from service-account-minified.json to .env
```

---

## Mode Comparison

| Aspect | **Streaming Mode** | **Direct Mode** |
|--------|-------------------|-----------------|
| **API Calls** | Vertex Search → Gemini | Vertex Search only |
| **Response Type** | Server-Sent Events (SSE) | JSON |
| **Response Time** | 5-10 seconds | 2-5 seconds |
| **Cost** | Higher (2 APIs) | Lower (1 API) |
| **UX** | Real-time progressive text | Instant complete response |
| **Use Case** | Long-form answers, detailed explanations | Quick answers, FAQs |
| **Customization** | Custom system prompt via Gemini | Vertex AI built-in summarization |

---

## System Prompt (Streaming Mode)

Located in `app/services/vertex_ai_service.py:387-403`

```
คุณเป็นผู้ช่วย AI ของ 9Expert Training
ซึ่งเป็นศูนย์ฝึกอบรมด้าน Data Analytics, Business Intelligence และ AI

โปรดใช้ข้อมูลต่อไปนี้เป็นบริบทในการตอบคำถาม:

<context>
{extracted_context}
</context>

คำถามจากผู้ใช้: {query}

โปรดตอบคำถามเป็นภาษาไทย โดย:
1. ตอบตรงประเด็น ชัดเจน กระชับ
2. ใช้ข้อมูลจาก context ที่ให้มาเท่านั้น
3. ถ้าข้อมูลไม่เพียงพอ บอกได้ว่าไม่มีข้อมูลในส่วนนั้น
4. จัดรูปแบบให้อ่านง่าย ใช้ bullet points ถ้าเหมาะสม
```

**Note:** Direct mode uses Vertex AI's built-in summarization model (no custom prompt).

---

## Architecture

### Streaming Mode Workflow
```
User Query
    ↓
POST /api/vertex-search { mode: "streaming" }
    ↓
search_extractive() → Extract RAG context from Vertex AI
    ↓
generate_streaming_response() → Stream via Gemini with system prompt
    ↓
Server-Sent Events → Frontend receives chunks progressively
    ↓
Real-time UI updates with final citations
```

### Direct Mode Workflow
```
User Query
    ↓
POST /api/vertex-search { mode: "direct" }
    ↓
search_with_summary() → Vertex AI generates summary directly
    ↓
JSON Response → Complete summary + citations
    ↓
Frontend displays immediately
```

---

## CORS Configuration

Default allowed origins (in `app/main.py`):
```python
allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:3000|http://127\.0\.0\.1:3000"
```

To add custom origins, edit `app/main.py:20`.

---

## Deployment

### Deploy to Render (Free Tier)

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: vertex-ai-search-rag-api
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: GCP_PROJECT_ID
        sync: false
      - key: GCP_SERVICE_ACCOUNT_KEY
        sync: false
      - key: VERTEX_SEARCH_ENGINE_ID
        sync: false
      - key: VERTEX_SEARCH_LOCATION
        value: global
```

2. Push to GitHub
3. Connect to Render
4. Set environment variables in Render Dashboard

---

## Testing

### Manual Testing with curl

**Streaming Mode:**
```bash
curl -N -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์สอะไรเหมาะกับผู้เริ่มต้น",
    "mode": "streaming",
    "pageSize": 5,
    "model": "gemini-2.0-flash"
  }'
```

**Direct Mode:**
```bash
curl -X POST http://localhost:8000/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "เรียน Power BI ต้องมีพื้นฐานอะไร",
    "mode": "direct",
    "pageSize": 3
  }'
```

### Testing with Swagger UI
1. Navigate to http://localhost:8000/docs
2. Click on `/api/vertex-search` endpoint
3. Click "Try it out"
4. Modify request body
5. Click "Execute"

---

## Troubleshooting

### 500 Internal Server Error
- **Cause**: Invalid GCP credentials or missing environment variables
- **Fix**: Check `.env` file, ensure `GCP_SERVICE_ACCOUNT_KEY` is minified to single line

### 401 Unauthorized (Vertex AI API)
- **Cause**: Token expired or invalid service account
- **Fix**: Service automatically refreshes tokens; check GCP IAM permissions

### CORS Error
- **Cause**: Frontend origin not in allowed list
- **Fix**: Update `allow_origin_regex` in `app/main.py:20`

### Streaming Not Working
- **Cause**: Missing `GEMINI_API_KEY`
- **Fix**: Add Gemini API key to `.env`

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app initialization, CORS setup |
| `app/config.py` | Environment variables and settings |
| `app/routers/vertex_search.py` | `/api/vertex-search` endpoint logic |
| `app/services/vertex_ai_service.py` | Vertex AI & Gemini integration |
| `app/models/vertex_search.py` | Pydantic request/response schemas |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variables template |

---

## License

Extracted from 9Expert MVP project.

**Developer:** AGICAFET
**Client:** 9Expert Training (https://www.9experttraining.com)

---

## Support

For issues or questions:
1. Check Swagger docs: http://localhost:8000/docs
2. Review logs for detailed error messages
3. Verify environment variables in `.env`
