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
2. **Tools Installed:** `gcloud` CLI, Docker
3. **Required Files:**
   * `Dockerfile` (Must expose port 8080)
   * `app/main.py` (With CORS middleware configured)
   * `.env` (Local secrets for reference)

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

### 3.2 Method A: Deployment via Cloud Console UI (Recommended)

Since passing complex JSON keys via CLI is error-prone, using the UI is the most reliable method.

**Steps:**

1. Go to the [Cloud Run Console](https://console.cloud.google.com/run)
2. Click **"CREATE SERVICE"** (or **"EDIT & DEPLOY NEW REVISION"** if updating)
3. **Select Image:** `gcr.io/expert-ai-chatbot/vertex-search-api:latest`
4. **Container, Networking, Security:**
   - **Container Port:** `8080`
   - **Command:** `/usr/local/bin/python`
   - **Args:** `-m uvicorn app.main:app --host 0.0.0.0 --port 8080`

5. **Environment Variables:** Add the following _(Copy values from your local `.env`)_:

   | Variable Name | Example Value |
   |---------------|---------------|
   | `GCP_PROJECT_ID` | `expert-ai-chatbot` |
   | `VERTEX_SEARCH_ENGINE_ID` | `rag-engine-search-app_xxxx` |
   | `VERTEX_SEARCH_LOCATION` | `global` |
   | `GEMINI_API_KEY` | `AIzaSy...` _(Paste actual key)_ |
   | `GCP_SERVICE_ACCOUNT_KEY` | `{"type":"service_account",...}` _(Paste the entire JSON string)_ |

6. **Autoscaling:** Set **Maximum number of instances** to `5`
7. Click **Create/Deploy**

---

### 3.3 Method B: Deployment via CLI (Scripting)

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

### 5.3 Test Request (Postman/cURL)

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

## 🛠️ Troubleshooting Common Errors

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| **Container failed to start** | App crashed on startup. Likely missing ENV vars or wrong Command/Entrypoint. | Check Logs in Cloud Console. Ensure `uvicorn` command args are correct and all 5 ENV vars are present. |
| **403 Forbidden** | Service is Private (IAM blocked). | Run the `add-iam-policy-binding` command in Phase 4. |
| **NameError: Fields must not use names with leading underscores** | Pydantic model bug (`_internal_uri`). | Rename the field in `app/models/vertex_search.py` (remove `_` prefix) and rebuild the image. |
| **429 Too Many Requests** | Vertex AI Quota limit or Cloud Run Max instances reached. | Check Vertex AI quota limits. Keep Max Instances low (5-10) to prevent bill shock. |
| **500 Internal Server Error** | Missing environment variables or invalid service account JSON. | Verify all 5 environment variables are set correctly in Cloud Run. Check logs for details. |
| **Timeout errors** | Request takes longer than 60s (default timeout). | Increase timeout: `--timeout 300` (5 minutes max). |

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

- [ ] GCP account created with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] Docker image built and pushed to GCR
- [ ] Required APIs enabled (Cloud Run, Cloud Build)
- [ ] Environment variables/secrets configured
- [ ] Service deployed to Cloud Run
- [ ] Public access granted (`allUsers` invoker role)
- [ ] Health endpoint tested (`GET /`)
- [ ] API endpoint tested (`POST /api/vertex-search`)
- [ ] Frontend updated with new API URL
- [ ] Monitoring and logging configured
- [ ] (Optional) Custom domain mapped
- [ ] (Optional) CI/CD pipeline set up

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
**Last Updated:** 2025-12-14
