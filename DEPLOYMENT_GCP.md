# 🚀 GCP Cloud Run Deployment Guide

Complete step-by-step guide to deploy the **Vertex AI Search RAG API** to Google Cloud Platform (GCP) Cloud Run.

---

## 📋 Prerequisites

### 1. Google Cloud Platform Account
- Create account at: https://console.cloud.google.com
- Free tier includes: $300 credit (90 days) + Always Free services
- Cloud Run Always Free: 2 million requests/month

### 2. Install Google Cloud CLI
**Windows:**
```powershell
# Download installer from:
https://cloud.google.com/sdk/docs/install

# Or use Chocolatey:
choco install gcloudsdk
```

**macOS:**
```bash
brew install --cask google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 3. Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop
- Verify installation: `docker --version`

### 4. Have Your Environment Variables Ready
- `GEMINI_API_KEY` - Get from https://aistudio.google.com/app/apikey
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_SERVICE_ACCOUNT_KEY` - Service account JSON (minified)
- `VERTEX_SEARCH_ENGINE_ID` - Vertex AI Search engine ID
- `VERTEX_SEARCH_LOCATION` - Default: `global`

---

## 🔧 Phase 1: GCP Project Setup

### Step 1.1: Authenticate with Google Cloud
```bash
gcloud auth login
```
This opens your browser to sign in with your Google account.

### Step 1.2: Create a New Project (or use existing)
```bash
# Create new project
gcloud projects create YOUR-PROJECT-ID --name="9Expert Vertex Search API"

# Or list existing projects
gcloud projects list
```

**Example:**
```bash
gcloud projects create expert-api-prod --name="9Expert Vertex Search API"
```

### Step 1.3: Set Active Project
```bash
gcloud config set project YOUR-PROJECT-ID
```

**Example:**
```bash
gcloud config set project expert-api-prod
```

### Step 1.4: Enable Billing
```bash
# Link billing account (required for Cloud Run)
gcloud beta billing projects link YOUR-PROJECT-ID --billing-account=BILLING-ACCOUNT-ID

# Find your billing account ID:
gcloud beta billing accounts list
```

### Step 1.5: Enable Required APIs
```bash
# Enable Cloud Run, Cloud Build, and Container Registry
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

**Verification:**
```bash
gcloud services list --enabled
```

---

## 🐳 Phase 2: Build and Push Docker Image

### Step 2.1: Navigate to Project Directory
```bash
cd C:\GitHubRepo\9expert-mvp\vertex-ai-search-rag-fastapi-lean
```

### Step 2.2: Configure Docker for GCP
```bash
gcloud auth configure-docker
```

### Step 2.3: Build Docker Image with Cloud Build (Recommended)
**Option A: Cloud Build (Faster, uses GCP servers)**
```bash
gcloud builds submit --tag gcr.io/<YOUR-PROJECT-ID>/vertex-search-api:latest
```

**Example:**
```bash
gcloud builds submit --tag gcr.io/expert-ai-chatbot/vertex-search-api:latest
```

**Build time:** ~2-3 minutes
**Output:** Image URL: `gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest`

---

**Option B: Local Build + Push (Alternative)**
```bash
# Build locally
docker build -t gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest .

# Push to Google Container Registry
docker push gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest
```

### Step 2.4: Verify Image in Container Registry
```bash
gcloud container images list
gcloud container images describe gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest
```

---

## 🚀 Phase 3: Deploy to Cloud Run

### Step 3.1: Deploy the Service

**Basic Deployment (Manual Environment Variables):**
```bash
# skeleton command to Add environment variables later on GCP GUI
gcloud run deploy vertex-search-api \
  --image gcr.io/expert-ai-chatbot/vertex-search-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080
```

```powershell
gcloud run deploy vertex-search-api --image gcr.io/expert-ai-chatbot/vertex-search-api:latest --platform managed --region asia-southeast1 --allow-unauthenticated --port 8080
```

```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GEMINI_API_KEY=your_key_here,GCP_PROJECT_ID=your_project,VERTEX_SEARCH_ENGINE_ID=your_engine_id,VERTEX_SEARCH_LOCATION=global \
  --set-env-vars GCP_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
```

**⚠️ Important:** Replace placeholders:
- `YOUR-PROJECT-ID` → Your actual GCP project ID
- `your_key_here` → Your Gemini API key
- `your_project` → Your GCP project ID (yes, same as above)
- `your_engine_id` → Your Vertex AI Search engine ID
- `{"type":"service_account",...}` → Your minified service account JSON

---

### Step 3.2: Deploy with Secret Manager (Recommended for Production)

**Create Secrets:**
```bash
# Create secret for Gemini API key
echo -n "your_gemini_api_key" | gcloud secrets create gemini-api-key --data-file=-

# Create secret for Service Account Key
echo -n '{"type":"service_account",...}' | gcloud secrets create gcp-service-account-key --data-file=-
```

**Deploy with Secrets:**
```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GCP_PROJECT_ID=your_project,VERTEX_SEARCH_ENGINE_ID=your_engine_id,VERTEX_SEARCH_LOCATION=global \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest,GCP_SERVICE_ACCOUNT_KEY=gcp-service-account-key:latest
```

---

### Step 3.3: Deployment Parameters Explained

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `--image` | `gcr.io/...` | Docker image to deploy |
| `--platform managed` | - | Use fully managed Cloud Run |
| `--region` | `asia-southeast1` | Deployment region (Bangkok, Thailand) |
| `--allow-unauthenticated` | - | Public API (no auth required) |
| `--port` | `8080` | Container port (must match Dockerfile) |
| `--memory` | `512Mi` | RAM allocation (256Mi-8Gi available) |
| `--cpu` | `1` | CPU cores (0.5-4 available) |
| `--timeout` | `300` | Request timeout (5 minutes max) |
| `--max-instances` | `10` | Auto-scaling limit (0-1000) |
| `--set-env-vars` | - | Environment variables (plain text) |
| `--set-secrets` | - | Environment variables (from Secret Manager) |

**Common Regions:**
- `asia-southeast1` - Singapore
- `asia-northeast1` - Tokyo, Japan
- `us-central1` - Iowa, USA
- `europe-west1` - Belgium

---

## ✅ Phase 4: Verify Deployment

### Step 4.1: Get Service URL
```bash
gcloud run services describe vertex-search-api --region asia-southeast1 --format 'value(status.url)'
```

**Output:**
```
https://vertex-search-api-xxxxx-xx.a.run.app
```

### Step 4.2: Test Health Endpoint
```bash
curl https://YOUR-SERVICE-URL.run.app/
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "Vertex AI Search RAG API",
  "version": "1.0.0",
  "endpoints": {
    "vertex_search": "/api/vertex-search",
    "docs": "/docs",
    "redoc": "/redoc"
  }
}
```

### Step 4.3: Test API Endpoint
```bash
curl -X POST https://YOUR-SERVICE-URL.run.app/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์สอะไรเหมาะกับผู้เริ่มต้น",
    "mode": "direct",
    "pageSize": 3
  }'
```

### Step 4.4: Open Interactive Docs
```
https://YOUR-SERVICE-URL.run.app/docs
```

---

## 🔄 Phase 5: Update Deployment (After Code Changes)

### Step 5.1: Rebuild Image
```bash
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest
```

### Step 5.2: Deploy New Version
```bash
gcloud run deploy vertex-search-api \
  --image gcr.io/YOUR-PROJECT-ID/vertex-search-api:latest \
  --region asia-southeast1
```

Cloud Run will:
1. Deploy new version (no downtime)
2. Gradually shift traffic to new version
3. Keep old version as backup (for rollback)

### Step 5.3: Rollback (if needed)
```bash
# List revisions
gcloud run revisions list --service vertex-search-api --region asia-southeast1

# Rollback to previous revision
gcloud run services update-traffic vertex-search-api \
  --to-revisions REVISION-NAME=100 \
  --region asia-southeast1
```

---

## 🔐 Phase 6: Security Best Practices

### 6.1: Use Secret Manager (Not Environment Variables)
```bash
# Create secrets
gcloud secrets create gemini-api-key --data-file=-
gcloud secrets create gcp-service-account-key --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member=serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### 6.2: Enable Cloud Armor (Optional - DDoS Protection)
```bash
# Requires Cloud Run with Load Balancer (not direct deployment)
# See: https://cloud.google.com/armor/docs/integrating-cloud-armor
```

### 6.3: Set up Cloud Monitoring
```bash
# Logs are automatically sent to Cloud Logging
# View logs:
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" --limit 50
```

---

## 💰 Cost Estimation

### Cloud Run Pricing (as of 2024)

**Always Free Tier:**
- 2 million requests/month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**Beyond Free Tier:**
- Requests: $0.40 per 1M requests
- Memory: $0.0000025 per GB-second
- CPU: $0.00002400 per vCPU-second

### Example Cost (Low Traffic)
- **5,000 requests/month**
- **Average response time: 3 seconds**
- **Memory: 512MB**
- **CPU: 1 vCPU**

**Cost:** $0/month (within free tier)

### Example Cost (Medium Traffic)
- **100,000 requests/month**
- **Average response time: 3 seconds**
- **Memory: 512MB**
- **CPU: 1 vCPU**

**Cost:** ~$2-5/month

---

## 🛠️ Troubleshooting

### Error: "Service account does not exist"
```bash
# Grant permissions to default compute service account
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
  --member=serviceAccount:YOUR-PROJECT-NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/run.admin
```

### Error: "Container failed to start"
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json

# Common causes:
# - Missing environment variables
# - Port mismatch (must be 8080)
# - Application crashes on startup
```

### Error: "Memory limit exceeded"
```bash
# Increase memory allocation
gcloud run services update vertex-search-api \
  --memory 1Gi \
  --region asia-southeast1
```

### Error: "Timeout"
```bash
# Increase timeout (max 3600s for 2nd gen)
gcloud run services update vertex-search-api \
  --timeout 600 \
  --region asia-southeast1
```

---

## 📊 Monitoring & Logs

### View Logs (Real-time)
```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api"
```

### View Metrics (Cloud Console)
```
https://console.cloud.google.com/run/detail/asia-southeast1/vertex-search-api/metrics
```

**Available Metrics:**
- Request count
- Request latency
- Container CPU utilization
- Container memory utilization
- Billable container instance time

---

## 🌐 Custom Domain Setup (Optional)

### Step 1: Map Custom Domain
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

## 🔄 CI/CD Setup (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy-gcp.yml`:

```yaml
name: Deploy to GCP Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Build and Push
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/vertex-search-api

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy vertex-search-api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/vertex-search-api \
            --region asia-southeast1 \
            --platform managed
```

**Required GitHub Secrets:**
- `GCP_PROJECT_ID`
- `GCP_SA_KEY` (Service account JSON with Cloud Run permissions)

---

## 📚 Additional Resources

- **Cloud Run Documentation:** https://cloud.google.com/run/docs
- **Container Registry:** https://cloud.google.com/container-registry
- **Secret Manager:** https://cloud.google.com/secret-manager
- **Cloud Build:** https://cloud.google.com/build
- **Pricing Calculator:** https://cloud.google.com/products/calculator

---

## ✅ Deployment Checklist

- [ ] GCP account created with billing enabled
- [ ] gcloud CLI installed and authenticated
- [ ] Docker image built and pushed to GCR
- [ ] Required APIs enabled (Cloud Run, Cloud Build)
- [ ] Environment variables/secrets configured
- [ ] Service deployed to Cloud Run
- [ ] Health endpoint tested (`GET /`)
- [ ] API endpoint tested (`POST /api/vertex-search`)
- [ ] Frontend updated with new API URL
- [ ] Monitoring and logging configured
- [ ] (Optional) Custom domain mapped
- [ ] (Optional) CI/CD pipeline set up

---

## 🎉 Success!

Your Vertex AI Search RAG API is now live on GCP Cloud Run!

**Next Steps:**
1. Update frontend environment variable: `NUXT_PUBLIC_API_BASE_URL=https://YOUR-SERVICE-URL.run.app`
2. Deploy frontend to Vercel
3. Test end-to-end
4. Monitor costs and performance
5. (Optional) Set up alerts and auto-scaling policies

---

**Developer:** AGICAFET
**Client:** 9Expert Training
**Last Updated:** 2025-01-14
