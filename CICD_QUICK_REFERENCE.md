# 🚀 CI/CD Quick Reference Card

Quick commands for managing your automated Cloud Run deployment.

---

## 📦 Deploy

### Auto Deploy (Push to Main)
```bash
git add .
git commit -m "Your changes"
git push origin main
# ✅ Auto-deploys to Cloud Run
```

### Manual Deploy (GitHub CLI)
```bash
gh workflow run deploy-cloud-run.yml
```

### Manual Deploy (GitHub UI)
1. Go to **Actions** tab
2. Click **Deploy to Cloud Run**
3. Click **Run workflow**

---

## 🔍 Monitor

### Watch Deployment
```bash
# GitHub Actions logs (requires gh CLI)
gh run watch

# Cloud Run logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" --format json
```

### Check Service Status
```bash
gcloud run services describe vertex-search-api \
    --region asia-southeast1 \
    --format="value(status.url,status.conditions)"
```

### View Recent Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" \
    --limit 50 \
    --format json
```

---

## 🧪 Test

### Get Service URL
```bash
SERVICE_URL=$(gcloud run services describe vertex-search-api \
  --region asia-southeast1 \
  --format 'value(status.url)')

echo $SERVICE_URL
```

### Health Check
```bash
curl $SERVICE_URL/
```

### Test API
```bash
curl -X POST $SERVICE_URL/api/vertex-search \
  -H "Content-Type: application/json" \
  -d '{"query": "คอร์ส Python", "mode": "direct"}'
```

### Open Swagger UI
```bash
# macOS
open "$SERVICE_URL/docs"

# Linux
xdg-open "$SERVICE_URL/docs"

# Windows (Git Bash)
start "$SERVICE_URL/docs"
```

---

## 🔄 Rollback

### List Revisions
```bash
gcloud run revisions list \
    --service vertex-search-api \
    --region asia-southeast1
```

### Rollback to Previous Revision
```bash
# Get previous revision name from list above
PREVIOUS_REVISION="vertex-search-api-00002-xyz"

gcloud run services update-traffic vertex-search-api \
    --to-revisions $PREVIOUS_REVISION=100 \
    --region asia-southeast1
```

### Rollback to Specific Git Commit
```bash
# Build specific commit
git checkout abc123def456

gcloud builds submit --tag gcr.io/expert-ai-chatbot/vertex-search-api:rollback

# Deploy rollback image
gcloud run deploy vertex-search-api \
    --image gcr.io/expert-ai-chatbot/vertex-search-api:rollback \
    --region asia-southeast1
```

---

## 🔐 Secrets Management

### Update GitHub Secret
```bash
# Using GitHub CLI
gh secret set GEMINI_API_KEY < gemini-key.txt

# Or via GitHub UI
# Settings → Secrets and variables → Actions → Update
```

### Update Environment Variable (No Rebuild)
```bash
gcloud run services update vertex-search-api \
    --region asia-southeast1 \
    --set-env-vars "NEW_VAR=value,EXISTING_VAR=updated_value"
```

### Rotate Service Account Key
```bash
# 1. Create new key
gcloud iam service-accounts keys create new-key.json \
    --iam-account="github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"

# 2. Update GitHub secret
gh secret set GCP_SA_KEY < new-key.json

# 3. Delete old key (get KEY_ID from list below)
gcloud iam service-accounts keys list \
    --iam-account="github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"

gcloud iam service-accounts keys delete KEY_ID \
    --iam-account="github-actions-deployer@expert-ai-chatbot.iam.gserviceaccount.com"
```

---

## 📊 Monitoring

### View Deployment History
```bash
# GitHub Actions runs
gh run list --workflow=deploy-cloud-run.yml --limit 10

# Cloud Run revisions
gcloud run revisions list --service vertex-search-api --region asia-southeast1
```

### Check Resource Usage
```bash
# CPU and Memory metrics
gcloud monitoring time-series list \
    --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="vertex-search-api"' \
    --format=json
```

### Set Up Alerts
```bash
# Create alert policy (via Cloud Console is easier)
# Navigate to: Monitoring → Alerting → Create Policy
# Metric: Cloud Run Revision → Request latency
# Condition: > 2000ms for 1 minute
# Notification: Email
```

---

## 🛠️ Troubleshooting

### Deployment Failed - View Logs
```bash
# GitHub Actions logs
gh run view --log-failed

# Cloud Build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### Service Unhealthy - Check Errors
```bash
# View errors only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND severity>=ERROR" \
    --limit 50 \
    --format json
```

### Container Won't Start - Check Startup
```bash
# View startup logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND textPayload=~'Uvicorn running'" \
    --limit 10 \
    --format json
```

### Environment Variable Missing
```bash
# List current env vars
gcloud run services describe vertex-search-api \
    --region asia-southeast1 \
    --format="get(spec.template.spec.containers[0].env)"
```

---

## 🎯 Common Tasks

### Deploy Feature Branch (Manual)
```bash
# Build from feature branch
git checkout feature/new-feature

gcloud builds submit --tag gcr.io/expert-ai-chatbot/vertex-search-api:feature-test

# Deploy to staging service
gcloud run deploy vertex-search-api-staging \
    --image gcr.io/expert-ai-chatbot/vertex-search-api:feature-test \
    --region asia-southeast1
```

### Update Max Instances
```bash
gcloud run services update vertex-search-api \
    --region asia-southeast1 \
    --max-instances 10
```

### Update Memory/CPU
```bash
gcloud run services update vertex-search-api \
    --region asia-southeast1 \
    --memory 1Gi \
    --cpu 2
```

### Enable Cloud Run Cold Start Prevention
```bash
# Keep 1 instance warm (costs ~$8/month)
gcloud run services update vertex-search-api \
    --region asia-southeast1 \
    --min-instances 1
```

### Disable Auto-Deploy (Manual Only)
Edit `.github/workflows/deploy-cloud-run.yml`:
```yaml
on:
  # push:  # Comment out
  #   branches:
  #     - main
  workflow_dispatch:  # Keep manual only
```

---

## 📈 Performance Tuning

### View Request Latency
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND httpRequest.latency!=''" \
    --limit 100 \
    --format="table(httpRequest.latency, httpRequest.status)"
```

### Analyze Slow Requests
```bash
# Find requests > 2 seconds
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api AND httpRequest.latency>'2s'" \
    --limit 50 \
    --format json
```

### Enable Request Tracing
```bash
# Cloud Trace automatically enabled
# View traces: https://console.cloud.google.com/traces/list?project=expert-ai-chatbot
```

---

## 💰 Cost Control

### View Current Month Costs
```bash
# Cloud Run costs (via Cloud Console is more detailed)
# Navigate to: Billing → Reports → Filter by Cloud Run
```

### Set Budget Alert
```bash
# Via Cloud Console (recommended)
# Billing → Budgets & alerts → Create budget
# Set threshold: $50/month
# Alert at: 50%, 90%, 100%
```

### Reduce Costs
```bash
# 1. Reduce max instances
gcloud run services update vertex-search-api --max-instances 3

# 2. Set min instances to 0
gcloud run services update vertex-search-api --min-instances 0

# 3. Reduce memory
gcloud run services update vertex-search-api --memory 512Mi

# 4. Set timeout lower
gcloud run services update vertex-search-api --timeout 120
```

---

## 🔒 Security

### Check IAM Permissions
```bash
# List service permissions
gcloud run services get-iam-policy vertex-search-api \
    --region asia-southeast1 \
    --format json
```

### Make Service Private (Require Auth)
```bash
# Remove public access
gcloud run services remove-iam-policy-binding vertex-search-api \
    --region asia-southeast1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# Grant access to specific service account
gcloud run services add-iam-policy-binding vertex-search-api \
    --region asia-southeast1 \
    --member="serviceAccount:your-app@project.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Scan for Vulnerabilities
```bash
# Scan Docker image
gcloud container images scan gcr.io/expert-ai-chatbot/vertex-search-api:latest

# View scan results
gcloud container images describe gcr.io/expert-ai-chatbot/vertex-search-api:latest \
    --show-package-vulnerability
```

---

## 🎛️ Configuration

### Update Workflow Settings

Edit `.github/workflows/deploy-cloud-run.yml`:

```yaml
env:
  PROJECT_ID: expert-ai-chatbot        # Your project
  SERVICE_NAME: vertex-search-api      # Service name
  REGION: asia-southeast1              # Region
  IMAGE_NAME: gcr.io/expert-ai-chatbot/vertex-search-api
```

### Update Cloud Run Settings

```yaml
# In deploy step:
--memory 512Mi          # 256Mi, 1Gi, 2Gi, 4Gi
--cpu 1                 # 1, 2, 4, 8
--max-instances 5       # 1-100
--min-instances 0       # 0-100
--timeout 300           # seconds (max 3600)
```

---

## 📚 Useful Links

- **Cloud Run Console:** https://console.cloud.google.com/run?project=expert-ai-chatbot
- **GitHub Actions:** https://github.com/YOUR_USERNAME/vertex-ai-search-rag-fastapi-lean/actions
- **Cloud Build:** https://console.cloud.google.com/cloud-build/builds?project=expert-ai-chatbot
- **Logs Explorer:** https://console.cloud.google.com/logs/query?project=expert-ai-chatbot
- **Monitoring:** https://console.cloud.google.com/monitoring?project=expert-ai-chatbot

---

## ⌨️ Shell Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Cloud Run shortcuts
alias cr-logs='gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vertex-search-api" --format json'
alias cr-status='gcloud run services describe vertex-search-api --region asia-southeast1'
alias cr-url='gcloud run services describe vertex-search-api --region asia-southeast1 --format "value(status.url)"'
alias cr-deploy='gh workflow run deploy-cloud-run.yml'
alias cr-watch='gh run watch'
alias cr-revisions='gcloud run revisions list --service vertex-search-api --region asia-southeast1'

# Test shortcuts
alias test-health='curl $(cr-url)/'
alias test-api='curl -X POST $(cr-url)/api/vertex-search -H "Content-Type: application/json" -d "{\"query\": \"test\", \"mode\": \"direct\"}"'
alias open-docs='open "$(cr-url)/docs"'
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Usage:
```bash
cr-logs          # Tail logs
cr-status        # Show service status
cr-deploy        # Trigger deployment
test-health      # Test health endpoint
open-docs        # Open Swagger UI
```

---

**Quick Actions:**
- 🚀 Deploy: `git push origin main`
- 📊 Monitor: `gh run watch`
- 🧪 Test: `curl $(cr-url)/`
- 🔄 Rollback: `gcloud run services update-traffic vertex-search-api --to-revisions REVISION=100`
- 📝 Logs: `cr-logs` (if using aliases above)

---

**Last Updated:** 2025-12-14
