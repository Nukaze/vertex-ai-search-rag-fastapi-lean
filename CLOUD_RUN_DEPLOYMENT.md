# 🚀 Cloud Run Deployment Guide: Vertex AI Search API (FastAPI)

Complete step-by-step guide for deploying the Retrieval-Augmented Generation (RAG) API service to Google Cloud Run.

**Project:** Expert AI Chatbot
**Stack:** FastAPI, Python 3.11, Docker, Google Cloud Run
**Integrations:** Vertex AI Search, Google Gemini API
**Region:** `asia-southeast1` (Singapore)
**Environment:** Dev / Demo

---

## 📋 Prerequisites

1. **Google Cloud Project:** `expert-ai-chatbot`
2. **Tools Installed:** `gcloud` CLI, Docker (optional - Cloud Build can be used instead)
3. **Required Files:**
   * `Dockerfile` (Must expose port 8080)
   * `app/main.py` (With CORS middleware configured)
   * `.env` (Local secrets for reference)
   * `env_vars.yaml` (Environment variables for deployment)
   * `deploy_to_cloudrun.bat` (Automated deployment script)
4. **GCS Buckets:**
   * `9expert-feedback-storage` (For user feedback storage - must be created manually)
5. **Service Account:**
   * Must have `storage.objectAdmin` role on feedback bucket

---

## 🪣 Phase 0: GCS Bucket Setup (Feedback Storage)

The API includes a feedback system that stores user feedback (thumbs up/down) in Google Cloud Storage.

### 0.1 Create Feedback Bucket

**Option A: Via gcloud CLI**
```bash
gcloud storage buckets create gs://9expert-feedback-storage --location=asia-southeast1
```

**Option B: Via Cloud Console**
1. Go to [Cloud Storage Console](https://console.cloud.google.com/storage)
2. Click **"CREATE BUCKET"**
3. Name: `9expert-feedback-storage`
4. Location: `asia-southeast1` (Singapore)
5. Storage class: `Standard`
6. Access control: `Uniform` (recommended)
7. Click **"CREATE"**

---

### 0.2 Grant Service Account Permissions

The Cloud Run service uses a service account to write feedback to GCS. Grant it the necessary permissions:

```bash
gcloud storage buckets add-iam-policy-binding gs://9expert-feedback-storage \
  --member="serviceAccount:rag-vertex-ai-search-service@expert-ai-chatbot.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

**Verify permissions:**
```bash
gcloud storage buckets get-iam-policy gs://9expert-feedback-storage
```

**Expected output:**
```yaml
bindings:
- members:
  - serviceAccount:rag-vertex-ai-search-service@expert-ai-chatbot.iam.gserviceaccount.com
  role: roles/storage.objectAdmin
```

**⚠️ Important:** Wait 30 seconds after granting permissions for IAM changes to propagate globally.

---

### 0.3 Feedback Storage Structure

Once deployed, user feedback will be stored in this structure:

```
9expert-feedback-storage/
├── chat-feedback/
│   ├── 2025-12-23/                          # Archive by date
│   │   ├── positive_20251223_143025_456.json
│   │   └── negative_20251223_150130_789.json
│   └── latest/                              # Today's data only (cleared daily)
│       ├── positive_20251223_143025_456.json
│       ├── negative_20251223_150130_789.json
│       └── .last_cleared                    # Marker file for cleanup
```

**File naming convention:**
- `positive_YYYYMMDD_HHMMSS_ms.json` - Thumbs up feedback
- `negative_YYYYMMDD_HHMMSS_ms.json` - Thumbs down feedback

---

## 🛠️ Phase 1: Build & Push Docker Image

We use **Cloud Build** to build the Docker image and store it in the Artifact Registry (GCR).

### 1.1 Run Build Command

Execute this in your project root directory:

```bash
gcloud builds submit --tag gcr.io/expert-ai-chatbot/vertex-search-api:latest
```

**Output:** SUCCESS
**Image Location:** `gcr.io/expert-ai-chatbot/vertex-search-api:latest`

---

## 🔐 Phase 2: Secret Management (Optional but Recommended)

For production security, sensitive keys should be stored in Secret Manager.

_(If deploying via UI Variables directly for Dev/Demo, you can skip to Phase 3)._

### 2.1 Create Secrets

```bash
# Create Gemini API Key Secret
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-

# Create Service Account JSON Secret
echo -n '{"type":"service_account",...}' | gcloud secrets create gcp-service-account-key --data-file=-
```

### 2.2 Grant Access to Cloud Run

Ensure the Cloud Run Service Account (usually the Compute Engine default SA) has the Secret Accessor role (`roles/secretmanager.secretAccessor`).

```bash
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gcp-service-account-key \
  --member="serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 🚀 Phase 3: Deploy to Cloud Run

We configure the service with minimal instances to control costs during the Dev environment phase.

### 3.0 Method Overview

There are three ways to deploy:
- **Method A (Recommended):** Cloud Console UI - Most reliable for complex environment variables
- **Method B:** Manual gcloud CLI - For scripting and CI/CD
- **Method C (Fastest):** Automated batch script - One-command deployment with `env_vars.yaml`

Choose Method C if you have `deploy_to_cloudrun.bat` and `env_vars.yaml` already configured.

---

### 3.1 Configuration Specs

| Setting | Value | Reason |
|---------|-------|--------|
| **Region** | `asia-southeast1` | Singapore (closest to Thailand) |
| **Port** | `8080` | Standard Cloud Run port |
| **Memory** | `512Mi` | Sufficient for API logic |
| **CPU** | `1` | Single vCPU for cost efficiency |
| **Max Instances** | `5` | Safety net for Dev/Demo |
| **Authentication** | Allow unauthenticated | Public Access |

---

### 3.2 Method C: Automated Deployment Script (Fastest) ⚡

**Best for:** Quick deployments with pre-configured environment variables

This method uses the automated batch script that handles authentication, build, and deployment in one command.

**Prerequisites:**
- `deploy_to_cloudrun.bat` exists in project root
- `env_vars.yaml` is configured with all required variables

**Steps:**

1. **Verify `env_vars.yaml` has all required variables:**

```yaml
GEMINI_API_KEY: "YOUR_GEMINI_API_KEY"
GCP_PROJECT_ID: "expert-ai-chatbot"
VERTEX_SEARCH_ENGINE_ID: "rag-engine-search-app_xxxxx"
VERTEX_SEARCH_LOCATION: "global"
GCP_SERVICE_ACCOUNT_KEY: '{"type":"service_account",...}'  # Full JSON
FEEDBACK_BUCKET_NAME: "9expert-feedback-storage"
```

2. **Run the deployment script:**

```bash
cd C:\GitHubRepo\9expert-mvp\vertex-ai-search-rag-fastapi-lean
.\deploy_to_cloudrun.bat
```

3. **Wait for completion (~5 minutes):**
   - ✅ Authentication check
   - ✅ Docker build via Cloud Build (2-3 min)
   - ✅ Cloud Run deployment (1-2 min)
   - ✅ Service URL output

**Expected output:**
```
========================================================
[SUCCESS] Deployment Complete!
========================================================

Service Name: vertex-search-api
Region: asia-southeast1
Image: gcr.io/expert-ai-chatbot/vertex-search-api

Next steps:
   1. Get service URL:
      gcloud run services describe vertex-search-api --region asia-southeast1 --format "value(status.url)"

   2. Test the API:
      curl [SERVICE_URL]/health
```

**Advantages:**
- ✅ One-command deployment
- ✅ Handles authentication automatically
- ✅ Uses `env_vars.yaml` for clean variable management
- ✅ No JSON escaping issues
- ✅ Includes all deployment flags (memory, CPU, scaling)

---

### 3.3 Method A: Deployment via Cloud Console UI

Since passing complex JSON keys via CLI is error-prone, using the UI is the most reliable method.

**Steps:**

1. Go to the [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"CREATE SERVICE"** (or **"EDIT & DEPLOY NEW REVISION"** if updating)
3. **Select Image:** `gcr.io/expert-ai-chatbot/vertex-search-api:latest`
4. **Container, Networking, Security:**
   - **Container Port:** `8080`
   - **Command:** `/usr/local/bin/python`
   - **Args:** `-m uvicorn app.main:app --host 0.0.0.0 --port 8080`

5. **Environment Variables:** Add the following _(Copy values from your local `.env` or `env_vars.yaml`)_:

   | Variable Name | Example Value | Required |
   |---------------|---------------|----------|
   | `GCP_PROJECT_ID` | `expert-ai-chatbot` | ✅ Yes |
   | `VERTEX_SEARCH_ENGINE_ID` | `rag-engine-search-app_xxxx` | ✅ Yes |
   | `VERTEX_SEARCH_LOCATION` | `global` | ✅ Yes |
   | `GEMINI_API_KEY` | `AIzaSy...` | ✅ Yes |
   | `GCP_SERVICE_ACCOUNT_KEY` | `{"type":"service_account",...}` | ✅ Yes (Full JSON) |
   | `FEEDBACK_BUCKET_NAME` | `9expert-feedback-storage` | Optional (defaults to `9expert-feedback-storage`) |

   **⚠️ Important:** `GCP_SERVICE_ACCOUNT_KEY` must be the complete JSON string (2000+ characters), not truncated.

6. **Autoscaling:** Set **Maximum number of instances** to `5`
7. Click **Create/Deploy**

---

### 3.4 Method B: Deployment via CLI (Scripting)

**Note:** This creates the service but might require updating secrets via UI later if JSON parsing fails.

```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/expert-ai-chatbot/vertex-search-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --set-env-vars "GCP_PROJECT_ID=expert-ai-chatbot,VERTEX_SEARCH_ENGINE_ID=rag-engine-search-app_xxxx,VERTEX_SEARCH_LOCATION=global,GEMINI_API_KEY=YOUR_KEY_HERE"
  # Add secrets mapping here if using Secret Manager
```

**With Secret Manager:**

```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/expert-ai-chatbot/vertex-search-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --set-env-vars "GCP_PROJECT_ID=expert-ai-chatbot,VERTEX_SEARCH_ENGINE_ID=rag-engine-search-app_xxxx,VERTEX_SEARCH_LOCATION=global" \
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,GCP_SERVICE_ACCOUNT_KEY=gcp-service-account-key:latest"
```

---

## 🌐 Phase 4: Public Access Configuration

If the service returns **403 Forbidden**, you must explicitly allow public access (Internet accessible).

### 4.1 Grant Invoker Role

Run this command to open the service to `allUsers`:

```bash
gcloud run services add-iam-policy-binding vertex-search-api \
    --region asia-southeast1 \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --project expert-ai-chatbot
```

**Expected Output:**
```
Updated IAM policy for service [vertex-search-api].
bindings:
- members:
  - allUsers
  role: roles/run.invoker
```

---

## ✅ Phase 5: Verification

### 5.1 Get Service URL

```bash
gcloud run services describe vertex-search-api \
  --region asia-southeast1 \
  --format 'value(status.url)'
```

**Output Example:**
```
https://vertex-search-api-xxxxx-an.a.run.app
```

---

### 5.2 Health Check & Documentation

Visit the Swagger UI to verify the service is running:

**URL:** `https://[YOUR-SERVICE-URL].run.app/docs`

**Expected Response:** Interactive API documentation

---

### 5.3 Test Vertex Search Endpoint

**Endpoint:** `POST /api/vertex-search`
**Headers:** `Content-Type: application/json`
**Body (JSON):**

```json
{
  "query": "ขอข้อมูลเกี่ยวกับ Data Science Roadmap",
  "mode": "direct"
}
```

**cURL Command:**

```bash
curl -X POST https://[YOUR-SERVICE-URL].run.app/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ขอข้อมูลเกี่ยวกับ Data Science Roadmap",
    "mode": "direct",
    "pageSize": 5
  }'
```

**Expected Response:**

```json
{
  "success": true,
  "mode": "direct",
  "query": "ขอข้อมูลเกี่ยวกับ Data Science Roadmap",
  "summary": "Data Science Roadmap...",
  "citations": [...],
  "totalResults": 10,
  "responseTime": 1.23
}
```

---

### 5.4 Test Feedback Endpoint

**Endpoint:** `POST /api/feedback`
**Headers:** `Content-Type: application/json`

**Test thumbs up:**

```bash
curl -X POST https://[YOUR-SERVICE-URL].run.app/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "messageId": "test-msg-123",
    "feedback": "up",
    "reason": null,
    "userQuestion": "What courses do you recommend for Data Science?",
    "aiAnswer": "I recommend starting with our Data Analytics course."
  }'
```

**Expected Success Response:**

```json
{
  "success": true,
  "message": "ขอบคุณสำหรับคำติชมครับ! เราจะนำไปปรับปรุง AI ให้ดีขึ้น",
  "feedbackId": "chat-feedback/2025-12-23/positive_20251223_182814_192.json",
  "storedAt": "2025-12-23T18:28:14.192506Z",
  "error": null
}
```

**Test thumbs down with reason:**

```bash
curl -X POST https://[YOUR-SERVICE-URL].run.app/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "messageId": "test-msg-456",
    "feedback": "down",
    "reason": "The answer was too technical",
    "userQuestion": "What is machine learning?",
    "aiAnswer": "Machine learning is a subset of artificial intelligence..."
  }'
```

**Verify in GCS:**
1. Go to: https://console.cloud.google.com/storage/browser/9expert-feedback-storage
2. Navigate to `chat-feedback/YYYY-MM-DD/`
3. You should see `positive_*.json` and `negative_*.json` files

---

## 🛠️ Troubleshooting Common Errors

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| **Container failed to start** | App crashed on startup. Likely missing ENV vars or wrong Command/Entrypoint. | Check Logs in Cloud Console. Ensure `uvicorn` command args are correct and all environment variables are present. |
| **403 Forbidden (Public access)** | Service is Private (IAM blocked). | Run the `add-iam-policy-binding` command in Phase 4 to allow public access. |
| **403 GET storage.googleapis.com/storage/v1/b/...** | Service account doesn't have `storage.buckets.get` permission. | **Fix:** Use `client.bucket(name)` instead of `client.get_bucket(name)` in code. Already fixed in latest version. |
| **403 POST storage.googleapis.com/upload/storage/v1/b/...** | Service account missing `storage.objects.create` permission. | **Solution:** Grant `storage.objectAdmin` role:<br>`gcloud storage buckets add-iam-policy-binding gs://9expert-feedback-storage --member="serviceAccount:rag-vertex-ai-search-service@expert-ai-chatbot.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"`<br>Wait 30 seconds for IAM propagation. |
| **403 storage.buckets.create** | Service account trying to create bucket automatically. | **Fix:** Create bucket manually before deployment (see Phase 0). Code should use `client.bucket()` not `get_bucket()`. |
| **Field required, loc: ["body"]** | Postman/API client not sending request body or missing Content-Type header. | Ensure:<br>1. Request method is POST<br>2. Body type is "raw" (not form-data)<br>3. Header: `Content-Type: application/json`<br>4. JSON format dropdown selected |
| **NameError: Fields must not use names with leading underscores** | Pydantic model bug (`_internal_uri`). | Rename the field in `app/models/vertex_search.py` (remove `_` prefix) and rebuild the image. |
| **429 Too Many Requests** | Vertex AI Quota limit or Cloud Run Max instances reached. | Check Vertex AI quota limits. Keep Max Instances low (5-10) to prevent bill shock. |
| **500 Internal Server Error (Generic)** | Missing environment variables or invalid service account JSON. | Verify all environment variables are set correctly in Cloud Run. Check logs for details. Enable debug error responses in development. |
| **Timeout errors** | Request takes longer than 60s (default timeout). | Increase timeout: `--timeout 300` (5 minutes max). |

---

### Debugging 500 Errors with Enhanced Error Details

If you get a 500 error, check the response body for debug information:

**Example error response (with debug enabled):**
```json
{
  "detail": {
    "message": "ขออภัย ไม่สามารถบันทึกคำติชมได้ กรุณาลองใหม่อีกครั้ง",
    "error": "Failed to log feedback to GCS: 403 Permission denied",
    "debug": "GCS logging failed"
  }
}
```

**Steps to debug:**
1. Look at the `error` field for the actual error message
2. Check Cloud Run logs for full Python traceback:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND severity>=ERROR" --limit 10
   ```
3. Filter out request logs to see only application errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND severity>=ERROR AND NOT logName:requests" --limit 10
   ```

---

### GCS Permission Troubleshooting Checklist

If feedback endpoint returns 403 errors:

✅ **Step 1: Verify bucket exists**
```bash
gcloud storage buckets describe gs://9expert-feedback-storage
```

✅ **Step 2: Check service account permissions**
```bash
gcloud storage buckets get-iam-policy gs://9expert-feedback-storage
```

You should see:
```yaml
- members:
  - serviceAccount:rag-vertex-ai-search-service@expert-ai-chatbot.iam.gserviceaccount.com
  role: roles/storage.objectAdmin
```

✅ **Step 3: Grant permissions if missing**
```bash
gcloud storage buckets add-iam-policy-binding gs://9expert-feedback-storage \
  --member="serviceAccount:rag-vertex-ai-search-service@expert-ai-chatbot.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

✅ **Step 4: Wait for IAM propagation (30 seconds)**

✅ **Step 5: Test feedback endpoint again**

---

## 📊 Viewing Logs

### Real-time Logs

```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" --format json
```

### Recent Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" --limit 50 --format json
```

### Via Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on `vertex-search-api`
3. Click **"LOGS"** tab
4. Filter by severity (Error, Warning, Info)

---

## 🔄 Updating the Service

### Step 1: Rebuild Image

```bash
gcloud builds submit --tag gcr.io/expert-ai-chatbot/vertex-search-api:latest
```

### Step 2: Deploy New Revision

```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/expert-ai-chatbot/vertex-search-api:latest \
  --region asia-southeast1
```

Cloud Run will:
1. Create a new revision
2. Gradually shift traffic to new revision (zero downtime)
3. Keep old revision for rollback

---

### Step 3: Rollback (if needed)

```bash
# List all revisions
gcloud run revisions list --service vertex-search-api --region asia-southeast1

# Rollback to specific revision
gcloud run services update-traffic vertex-search-api \
  --to-revisions REVISION-NAME=100 \
  --region asia-southeast1
```

---

## 💰 Cost Management

### Free Tier Limits (Always Free)

- **Requests:** 2 million/month
- **Memory:** 360,000 GB-seconds
- **CPU:** 180,000 vCPU-seconds

### Estimated Costs (Beyond Free Tier)

**Low Traffic (10K requests/month):**
- Cost: **$0/month** (within free tier)

**Medium Traffic (100K requests/month):**
- Cost: **~$2-5/month**

**High Traffic (1M requests/month):**
- Cost: **~$20-30/month**

### Cost Optimization Tips

1. **Set Max Instances:** Limit to 5-10 during dev
2. **Use Minimum Instances: 0** - Pay only when used
3. **Optimize Memory:** Use 512Mi instead of 1Gi
4. **Monitor Usage:** Set up billing alerts

---

## 🔐 Security Best Practices

### 1. Use Secret Manager (Production)

Never hardcode secrets in environment variables for production.

### 2. Enable Cloud Armor (Optional)

Protect against DDoS attacks:

```bash
# Requires Cloud Run with Load Balancer
# See: https://cloud.google.com/armor/docs/integrating-cloud-armor
```

### 3. Set up VPC Connector (Optional)

For private backend services:

```bash
gcloud run services update vertex-search-api \
  --vpc-connector YOUR-CONNECTOR \
  --region asia-southeast1
```

### 4. Enable Binary Authorization

Ensure only trusted images are deployed:

```bash
# See: https://cloud.google.com/binary-authorization
```

---

## 🌐 Custom Domain Setup (Optional)

### Step 1: Map Domain

```bash
gcloud run domain-mappings create \
  --service vertex-search-api \
  --domain api.9expert.com \
  --region asia-southeast1
```

### Step 2: Add DNS Records

Follow instructions in Cloud Console to add DNS records to your domain registrar.

**Required Records:**
- Type: `A` or `CNAME`
- Value: Provided by GCP

### Step 3: Wait for SSL Certificate

Cloud Run automatically provisions a free SSL certificate (Let's Encrypt).

---

## 📚 Additional Resources

- **Cloud Run Documentation:** https://cloud.google.com/run/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **Vertex AI Search:** https://cloud.google.com/generative-ai-app-builder/docs/introduction
- **Pricing Calculator:** https://cloud.google.com/products/calculator

---

## ✅ Deployment Checklist

### Phase 0: Infrastructure Setup
- [ ] GCP account created with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] GCS feedback bucket created (`9expert-feedback-storage`)
- [ ] Service account permissions granted (`storage.objectAdmin` on feedback bucket)
- [ ] Wait 30 seconds for IAM propagation

### Phase 1: Build
- [ ] Docker image built and pushed to GCR (via Cloud Build or `deploy_to_cloudrun.bat`)
- [ ] Required APIs enabled (Cloud Run, Cloud Build, Cloud Storage)

### Phase 2: Environment Configuration
- [ ] `env_vars.yaml` created with all required variables:
  - [ ] `GEMINI_API_KEY`
  - [ ] `GCP_PROJECT_ID`
  - [ ] `VERTEX_SEARCH_ENGINE_ID`
  - [ ] `VERTEX_SEARCH_LOCATION`
  - [ ] `GCP_SERVICE_ACCOUNT_KEY` (full JSON)
  - [ ] `FEEDBACK_BUCKET_NAME` (optional)

### Phase 3: Deployment
- [ ] Service deployed to Cloud Run (via script, CLI, or UI)
- [ ] Public access granted (`allUsers` invoker role)
- [ ] Service URL obtained

### Phase 4: Testing
- [ ] Health endpoint tested (`GET /health`)
- [ ] Swagger docs accessible (`GET /docs`)
- [ ] Vertex search endpoint tested (`POST /api/vertex-search`)
- [ ] Feedback endpoint tested (`POST /api/feedback`)
- [ ] Verify feedback appears in GCS bucket

### Phase 5: Frontend Integration
- [ ] Frontend updated with new API URL (`NUXT_PUBLIC_API_BASE_URL`)
- [ ] End-to-end feedback flow tested from frontend
- [ ] Monitoring and logging configured

### Optional
- [ ] Custom domain mapped
- [ ] CI/CD pipeline set up
- [ ] Production error handling (disable debug error messages)

---

## 🎉 Success!

Your Vertex AI Search RAG API is now live on GCP Cloud Run!

**Service URL:** `https://vertex-search-api-xxxxx-an.a.run.app`

**Next Steps:**
1. Update frontend environment variable: `NUXT_PUBLIC_API_BASE_URL=https://YOUR-SERVICE-URL.run.app`
2. Test all API endpoints with enhanced parameters
3. Monitor costs and performance
4. Set up alerts and auto-scaling policies

---

**Developer:** 9Expert Development Team
**Client:** 9Expert Training
**Last Updated:** 2025-12-23

---

## 📝 Changelog

### 2025-12-23
- ✅ Added Phase 0: GCS Bucket Setup for feedback storage
- ✅ Added Method C: Automated deployment script (`deploy_to_cloudrun.bat`)
- ✅ Updated environment variables list to include `FEEDBACK_BUCKET_NAME`
- ✅ Added feedback endpoint testing instructions
- ✅ Enhanced troubleshooting section with GCS permission errors (403)
- ✅ Added debugging guide for 500 errors with enhanced error details
- ✅ Added GCS Permission Troubleshooting Checklist
- ✅ Updated deployment checklist with new phases

### 2025-12-14
- Initial documentation created
- Basic deployment methods (UI and CLI)
