# 🔄 CI/CD Setup Guide: GitHub Actions → Cloud Run

**Automated deployment pipeline for Vertex AI Search API**

---

## 📋 Overview

This CI/CD workflow automatically deploys your FastAPI service to Google Cloud Run whenever you push to the `main` branch.

**What it does:**
1. ✅ Authenticates with Google Cloud
2. 🏗️ Builds Docker image using Cloud Build
3. 📦 Pushes image to Google Container Registry (GCR)
4. 🚀 Deploys to Cloud Run with zero downtime
5. ✅ Runs health checks
6. 📊 Outputs deployment summary

**Deployment Time:** ~3-5 minutes per deploy

---

## 🔐 Step 1: Create Google Cloud Service Account

### 1.1 Create Service Account

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions-deployer \
    --display-name="GitHub Actions Deployer" \
    --description="Service account for automated Cloud Run deployments" \
    --project=expert-ai-chatbot
```

### 1.2 Grant Required Roles

```bash
# Set project ID
PROJECT_ID="expert-ai-chatbot"
SA_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Cloud Run Admin (deploy services)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.admin"

# Grant Service Account User (allow Cloud Run to use service accounts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.serviceAccountUser"

# Grant Cloud Build Editor (build Docker images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudbuild.builds.editor"

# Grant Storage Admin (push to GCR)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin"

# Grant Artifact Registry Writer (push images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/artifactregistry.writer"
```

### 1.3 Create and Download Service Account Key

```bash
# Create JSON key
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account="${SA_EMAIL}" \
    --project=$PROJECT_ID

# The file github-actions-key.json is now downloaded
# ⚠️ IMPORTANT: Keep this file secure! Never commit it to Git!
```

**Output:**
```
created key [xxxxx] of type [json] as [github-actions-key.json] for [github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com]
```

---

## 🔑 Step 2: Configure GitHub Secrets

Go to your GitHub repository settings and add these secrets:

### 2.1 Navigate to Secrets

1. Go to your GitHub repo: `https://github.com/YOUR_USERNAME/vertex-ai-search-rag-fastapi-lean`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

### 2.2 Add Required Secrets

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| **GCP_SA_KEY** | `{entire JSON content from github-actions-key.json}` | Copy the entire JSON file content |
| **GEMINI_API_KEY** | `AIzaSy...` | From Google AI Studio or Cloud Console |
| **VERTEX_SEARCH_ENGINE_ID** | `rag-engine-search-app_xxxx` | From Vertex AI Search console |
| **GCP_SERVICE_ACCOUNT_KEY** | `{your app service account JSON}` | The service account used by the app (not GitHub Actions SA) |

### 2.3 Secret Details

#### GCP_SA_KEY (GitHub Actions Service Account)
```json
{
  "type": "service_account",
  "project_id": "expert-ai-chatbot",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com",
  "client_id": "xxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/github-actions-deployer%40expert-ai-chatbot.iam.gserviceaccount.com"
}
```

#### GCP_SERVICE_ACCOUNT_KEY (Application Service Account)
This is the service account your app uses to call Vertex AI Search (not the GitHub Actions deployer account).

```json
{
  "type": "service_account",
  "project_id": "expert-ai-chatbot",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "YOUR-APP-SA@expert-ai-chatbot.iam.gserviceaccount.com",
  ...
}
```

---

## ✅ Step 3: Verify Workflow File

Ensure `.github/workflows/deploy-cloud-run.yml` exists in your repository:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
  workflow_dispatch:  # Allow manual trigger

env:
  PROJECT_ID: expert-ai-chatbot
  SERVICE_NAME: vertex-search-api
  REGION: asia-southeast1
  IMAGE_NAME: gcr.io/expert-ai-chatbot/vertex-search-api
```

**The workflow is already created for you!** ✅

---

## 🚀 Step 4: Deploy

### Option 1: Automatic Deployment (Push to Main)

```bash
# Make a change to your code
echo "# Updated" >> README.md

# Commit and push to main
git add .
git commit -m "Trigger CI/CD deployment"
git push origin main
```

**GitHub Actions will automatically:**
1. Detect the push to `main`
2. Run the workflow
3. Build and deploy to Cloud Run

### Option 2: Manual Deployment (Workflow Dispatch)

1. Go to **Actions** tab in GitHub
2. Select **Deploy to Cloud Run** workflow
3. Click **Run workflow** → **Run workflow**

---

## 📊 Step 5: Monitor Deployment

### 5.1 Watch GitHub Actions

1. Go to **Actions** tab in your GitHub repo
2. Click on the latest workflow run
3. Watch real-time logs:
   - 📥 Checkout code
   - 🔐 Authenticate to Google Cloud
   - 🏗️ Build Docker image
   - 🚀 Deploy to Cloud Run
   - ✅ Health check

### 5.2 Expected Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 Deployment Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Service:    vertex-search-api
🌍 Region:     asia-southeast1
🔗 URL:        https://vertex-search-api-xxxxx-an.a.run.app
📦 Image:      gcr.io/expert-ai-chatbot/vertex-search-api:latest
🏷️  Commit:     abc123def456
👤 Triggered:  your-github-username
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 API Documentation: https://vertex-search-api-xxxxx-an.a.run.app/docs
🔍 Logs: https://console.cloud.google.com/run/detail/asia-southeast1/vertex-search-api/logs?project=expert-ai-chatbot
```

### 5.3 Check Cloud Run Console

Visit: https://console.cloud.google.com/run?project=expert-ai-chatbot

You should see:
- **Service:** vertex-search-api
- **Status:** ✅ Healthy
- **Latest Revision:** Deployed X minutes ago
- **Traffic:** 100% to latest revision

---

## 🧪 Step 6: Test Deployed Service

### 6.1 Health Check

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe vertex-search-api \
  --region asia-southeast1 \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/
```

**Expected Response:**
```json
{
  "service": "Vertex AI Search RAG API",
  "version": "2.0",
  "status": "healthy"
}
```

### 6.2 Test API Endpoint

```bash
# Test vertex-search endpoint
curl -X POST $SERVICE_URL/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "คอร์ส Data Science",
    "mode": "direct",
    "pageSize": 5
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "mode": "direct",
  "query": "คอร์ส Data Science",
  "summary": "...",
  "citations": [...],
  "totalResults": 10,
  "responseTime": 1.23
}
```

### 6.3 Test Swagger UI

Visit: `https://[YOUR-SERVICE-URL].run.app/docs`

You should see the interactive API documentation.

---

## 🔧 Configuration Options

### Environment Variables (Modify in workflow file)

```yaml
env:
  PROJECT_ID: expert-ai-chatbot        # Change to your project
  SERVICE_NAME: vertex-search-api      # Change service name
  REGION: asia-southeast1              # Change region
  IMAGE_NAME: gcr.io/expert-ai-chatbot/vertex-search-api  # Change image path
```

### Cloud Run Settings (Modify deploy step)

```yaml
--memory 512Mi          # Change to: 256Mi, 1Gi, 2Gi, 4Gi
--cpu 1                 # Change to: 2, 4, 8
--max-instances 5       # Change to: 1, 10, 100
--min-instances 0       # Change to: 1 (keep warm)
--timeout 300           # Change to: 60, 600, 3600 (seconds)
```

---

## 🛡️ Security Best Practices

### 1. Protect Service Account Keys

```bash
# Add to .gitignore
echo "github-actions-key.json" >> .gitignore
echo "*.json" >> .gitignore  # Ignore all JSON keys

# Verify not tracked
git status
```

### 2. Rotate Keys Regularly

```bash
# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account="github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"

# Create new key
gcloud iam service-accounts keys create new-key.json \
    --iam-account="github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"

# Update GitHub secret
# Go to GitHub → Settings → Secrets → Update GCP_SA_KEY
```

### 3. Use Workload Identity Federation (Advanced)

For production, consider using Workload Identity Federation instead of service account keys:

https://cloud.google.com/iam/docs/workload-identity-federation

---

## 🔄 Workflow Triggers

### Automatic Triggers

- **Push to main branch:** Any commit to `main` triggers deployment
- **Pull request merge:** Merging PR to `main` triggers deployment

### Manual Triggers

```bash
# Using GitHub CLI
gh workflow run deploy-cloud-run.yml

# Or via GitHub UI
# Actions → Deploy to Cloud Run → Run workflow
```

### Disable Auto-Deploy (Manual Only)

Edit `.github/workflows/deploy-cloud-run.yml`:

```yaml
on:
  # push:  # Comment out auto-deploy
  #   branches:
  #     - main
  workflow_dispatch:  # Keep manual trigger only
```

---

## 🐛 Troubleshooting

### Issue 1: Authentication Failed

**Error:**
```
Error: google-github-actions/auth failed with: retry function failed after 3 attempts
```

**Solution:**
1. Verify `GCP_SA_KEY` secret is valid JSON (copy entire file content)
2. Check service account has required roles:
```bash
gcloud projects get-iam-policy expert-ai-chatbot \
    --flatten="bindings[].members" \
    --filter="bindings.members:github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"
```

### Issue 2: Cloud Build Failed

**Error:**
```
ERROR: build step 0 failed: error pulling build step
```

**Solution:**
1. Check Dockerfile exists and is valid
2. Verify Cloud Build API is enabled:
```bash
gcloud services enable cloudbuild.googleapis.com --project=expert-ai-chatbot
```

### Issue 3: Deployment Failed (Permission Denied)

**Error:**
```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'run.services.update' denied
```

**Solution:**
Grant missing roles:
```bash
gcloud projects add-iam-policy-binding expert-ai-chatbot \
    --member="serviceAccount:github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

### Issue 4: Health Check Failed

**Error:**
```
❌ Health check failed after 60 seconds
```

**Solution:**
1. Check Cloud Run logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" \
    --limit 50 \
    --format json
```

2. Common causes:
   - Missing environment variables
   - Invalid service account key
   - App crashed on startup

### Issue 5: Environment Variable Not Set

**Error:**
```
KeyError: 'GEMINI_API_KEY'
```

**Solution:**
1. Verify all 4 secrets are set in GitHub
2. Check workflow file passes them:
```yaml
--set-env-vars "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }},..."
```

---

## 📊 Monitoring & Logging

### View Logs

```bash
# Real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" \
    --format json

# Recent errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND severity>=ERROR" \
    --limit 50 \
    --format json
```

### Cloud Console

**Service Dashboard:**
https://console.cloud.google.com/run/detail/asia-southeast1/vertex-search-api?project=expert-ai-chatbot

**Logs Explorer:**
https://console.cloud.google.com/logs/query?project=expert-ai-chatbot

---

## 💰 Cost Optimization

### Free Tier Limits (Always Free)

- **Requests:** 2 million/month
- **Memory:** 360,000 GB-seconds
- **CPU:** 180,000 vCPU-seconds

### Cost Control Tips

1. **Set Max Instances:**
```yaml
--max-instances 5  # Prevent runaway costs
```

2. **Use Min Instances = 0:**
```yaml
--min-instances 0  # Pay only when used
```

3. **Right-size Resources:**
```yaml
--memory 512Mi --cpu 1  # Start small, scale if needed
```

4. **Monitor Usage:**
```bash
# View current month usage
gcloud run services describe vertex-search-api \
    --region asia-southeast1 \
    --format="table(metadata.name, status.traffic)"
```

---

## 🎯 Best Practices

### 1. Branch Protection

Protect your `main` branch:
- Go to **Settings** → **Branches**
- Add rule for `main`
- Enable:
  - ✅ Require pull request reviews
  - ✅ Require status checks to pass
  - ✅ Require branches to be up to date

### 2. Staging Environment

Create a staging workflow:

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches:
      - develop

env:
  SERVICE_NAME: vertex-search-api-staging
  # ... other settings
```

### 3. Semantic Versioning

Tag releases:

```bash
# Tag version
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Deploy specific version
gcloud run deploy vertex-search-api \
    --image gcr.io/expert-ai-chatbot/vertex-search-api:v1.0.0
```

### 4. Rollback Strategy

The workflow keeps previous revisions for rollback:

```bash
# List revisions
gcloud run revisions list --service vertex-search-api --region asia-southeast1

# Rollback to specific revision
gcloud run services update-traffic vertex-search-api \
    --to-revisions REVISION-NAME=100 \
    --region asia-southeast1
```

---

## 📚 Additional Resources

- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **Cloud Run CI/CD:** https://cloud.google.com/run/docs/continuous-deployment
- **Service Account Best Practices:** https://cloud.google.com/iam/docs/best-practices-service-accounts
- **Workload Identity Federation:** https://cloud.google.com/iam/docs/workload-identity-federation

---

## ✅ Setup Checklist

- [ ] Created GitHub Actions service account
- [ ] Granted required IAM roles (run.admin, cloudbuild.builds.editor, storage.admin)
- [ ] Downloaded service account key JSON
- [ ] Added 4 secrets to GitHub repository
  - [ ] GCP_SA_KEY
  - [ ] GEMINI_API_KEY
  - [ ] VERTEX_SEARCH_ENGINE_ID
  - [ ] GCP_SERVICE_ACCOUNT_KEY
- [ ] Verified workflow file exists (`.github/workflows/deploy-cloud-run.yml`)
- [ ] Pushed code to `main` branch
- [ ] Monitored deployment in GitHub Actions
- [ ] Tested deployed service (health check + API endpoint)
- [ ] Verified Swagger UI is accessible
- [ ] Set up branch protection (optional)
- [ ] Created staging environment (optional)

---

## 🎉 Success!

Your CI/CD pipeline is now active! Every push to `main` will automatically deploy to Cloud Run.

**Next Steps:**
1. Make a code change
2. Push to `main`
3. Watch GitHub Actions deploy automatically
4. Test the updated service

**Deployment Flow:**
```
Code Push → GitHub Actions → Cloud Build → GCR → Cloud Run → Live! 🚀
```

---

**Last Updated:** 2025-12-14
**Maintained By:** 9Expert Development Team
