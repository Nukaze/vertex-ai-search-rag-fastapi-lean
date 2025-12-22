# Feedback API Documentation

## Overview

The Feedback API allows users to provide feedback (thumbs up/down) on AI responses. Feedback is stored in Google Cloud Storage (GCS) with datetime-sorted filenames for easy retrieval and analysis.

## API Endpoint

```
POST /api/feedback
```

## Request Body

```typescript
{
  messageId: string        // Unique message ID from chat session
  feedback: "up" | "down"  // Thumbs up or down
  reason?: string          // Optional reason for thumbs down (max 500 chars)
  timestamp: string        // ISO 8601 timestamp (e.g., "2025-01-22T14:30:25.456Z")
  messageContent?: string  // First 200 chars of AI message for context
}
```

## Response

```typescript
{
  success: boolean         // Whether feedback was logged successfully
  message: string          // Human-readable status message
  feedbackId?: string      // Unique ID (filename in GCS)
  storedAt?: string        // ISO timestamp when stored
  error?: string           // Error message if success=false
}
```

## Example Request

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "messageId": "msg-1705932625456-abc123",
    "feedback": "down",
    "reason": "คำตอบไม่ตรงกับคำถาม",
    "timestamp": "2025-01-22T14:30:25.456Z",
    "messageContent": "สวัสดีครับ! ยินดีให้คำปรึกษาเรื่องเส้นทางอาชีพด้าน IT ครับ..."
  }'
```

## Example Response (Success)

```json
{
  "success": true,
  "message": "ขอบคุณสำหรับคำติชมครับ! เราจะนำไปปรับปรุง AI ให้ดีขึ้น",
  "feedbackId": "feedback_20250122_143025_456.json",
  "storedAt": "2025-01-22T14:30:26.123Z",
  "error": null
}
```

## GCS Storage

### Bucket Configuration

- **Bucket Name**: `9expert-feedback-storage`
- **Location**: `ASIA-SOUTHEAST1` (Bangkok)
- **Auto-creation**: Bucket is created automatically if it doesn't exist

### File Structure

Feedback is stored as NDJSON (Newline Delimited JSON) with datetime-based filenames:

```
gs://9expert-feedback-storage/
└── feedback/
    ├── feedback_20250122_143025_456.json
    ├── feedback_20250122_143530_789.json
    ├── feedback_20250122_144012_123.json
    └── ...
```

### Filename Format

```
feedback_YYYYMMDD_HHMMSS_milliseconds.json
```

**Benefits:**
- Files are automatically sorted by datetime in GCS
- Easy to filter by date range (e.g., all feedback from 2025-01-22)
- Collision-resistant (millisecond precision)
- Human-readable

### File Content (NDJSON)

Each file contains a single-line JSON object:

```json
{"messageId":"msg-1705932625456-abc123","feedback":"down","reason":"คำตอบไม่ตรงกับคำถาม","timestamp":"2025-01-22T14:30:25.456Z","messageContent":"สวัสดีครับ! ยินดีให้คำปรึกษาเรื่องเส้นทางอาชีพด้าน IT ครับ...","storedAt":"2025-01-22T14:30:26.123Z"}
```

**NDJSON Benefits:**
- Easy to stream and process line-by-line
- Compatible with BigQuery, Dataflow, and other GCP data tools
- Efficient for large-scale analytics

## Setup Instructions

### 1. Install Dependencies

```bash
cd vertex-ai-search-rag-fastapi-lean
pip install -r requirements.txt
```

This installs:
- `google-cloud-storage==2.18.2` (for GCS operations)
- Other existing dependencies

### 2. Configure Environment Variables

Ensure your `.env` file has the required GCP credentials:

```env
GCP_PROJECT_ID=your-project-id
GCP_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}
GEMINI_API_KEY=your-gemini-api-key
VERTEX_SEARCH_ENGINE_ID=your-search-engine-id
VERTEX_SEARCH_LOCATION=global
```

### 3. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Test the Endpoint

**Using curl:**

```bash
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "messageId": "test-msg-123",
    "feedback": "up",
    "reason": null,
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'",
    "messageContent": "Test message content"
  }'
```

**Using the Nuxt frontend:**

1. Start the FastAPI backend (port 8000)
2. Start the Nuxt frontend (port 3000)
3. Navigate to `/chat` or use the global chat bubble
4. Send a message to the AI
5. Click thumbs up/down on the AI response
6. Check the backend logs for feedback submission
7. Verify GCS bucket has the feedback file

## Architecture

### Frontend → Backend Flow

```
ChatMessage.vue (Frontend)
  ↓ submitFeedback()
  ↓ POST /api/feedback
  ↓
feedback.py (Router)
  ↓ Depends(get_feedback_service)
  ↓
gcs_feedback_service.py (Service)
  ↓ log_feedback()
  ↓
Google Cloud Storage
  ↓
gs://9expert-feedback-storage/feedback/feedback_20250122_143025_456.json
```

### Code Structure

```
app/
├── models/
│   └── feedback.py              # Pydantic models (FeedbackRequest, FeedbackResponse)
├── routers/
│   └── feedback.py              # API endpoint (POST /api/feedback)
├── services/
│   └── gcs_feedback_service.py  # GCS storage logic
└── main.py                      # Register feedback router
```

## Error Handling

### Backend Errors

- **500 Internal Server Error**: GCS logging failed or unexpected error
- **422 Validation Error**: Invalid request body (Pydantic validation)

### Frontend Graceful Degradation

If the API call fails, the frontend still shows a thank-you message to the user to maintain good UX. Errors are logged to the console for debugging.

```typescript
try {
  await fetch('/api/feedback', { ... })
} catch (error) {
  console.error('Failed to submit feedback:', error)
  // Still show thank you message (graceful degradation)
  feedbackSubmitted.value = true
}
```

## Security Considerations

1. **Service Account Permissions**: Ensure the service account has the following IAM roles:
   - `roles/storage.objectCreator` (to write feedback files)
   - `roles/storage.bucketCreator` (optional, to auto-create bucket)

2. **CORS**: The API allows requests from:
   - `http://localhost:3000` (development)
   - `https://*.vercel.app` (production deployments)
   - `https://*.9expert.com` (custom domain)

3. **Input Validation**:
   - `messageId`: Max 200 chars
   - `reason`: Max 500 chars
   - `messageContent`: Max 200 chars
   - `timestamp`: Must be valid ISO 8601 format

## Future Enhancements

1. **Analytics Dashboard**: Build a dashboard to visualize feedback trends
2. **BigQuery Integration**: Stream feedback to BigQuery for advanced analytics
3. **Sentiment Analysis**: Use NLP to analyze feedback reasons
4. **Auto-tagging**: Automatically categorize feedback by topic/issue
5. **Email Alerts**: Notify team when negative feedback exceeds threshold

## Troubleshooting

### Bucket Creation Failed

**Error**: `Permission 'storage.buckets.create' denied`

**Solution**: Either:
1. Manually create the bucket in GCS Console
2. Grant `roles/storage.bucketCreator` to the service account

### Feedback Not Saved

**Error**: `Failed to log feedback to GCS: 403 Forbidden`

**Solution**: Ensure service account has `roles/storage.objectCreator` permission

### Import Error

**Error**: `ModuleNotFoundError: No module named 'google.cloud.storage'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation and testing tools.
