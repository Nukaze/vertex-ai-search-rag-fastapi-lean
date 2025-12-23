@echo off
echo ========================================================
echo [DEPLOY] Vertex AI Search API to Cloud Run SERVICE
echo ========================================================
echo.

REM ===== CONFIGURATION =====
REM TODO: Update these values before running!
set PROJECT_ID=expert-ai-chatbot
set REGION=asia-southeast1
set SERVICE_NAME=vertex-search-api
set IMAGE_NAME=gcr.io/%PROJECT_ID%/vertex-search-api

REM Environment variables file
set ENV_VARS_FILE=env_vars.yaml

echo [CONFIG] Project ID: %PROJECT_ID%
echo [CONFIG] Region: %REGION%
echo [CONFIG] Service Name: %SERVICE_NAME%
echo [CONFIG] Image: %IMAGE_NAME%
echo [CONFIG] Env Vars File: %ENV_VARS_FILE%
echo.

REM ===== STEP 1: Check Authentication =====
echo [STEP 1/3] Checking Google Cloud authentication...
call gcloud auth print-access-token --quiet >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [!] You are not logged in.
    echo [!] Opening browser to authenticate...
    echo.
    call gcloud auth login
)

REM Set active project
call gcloud config set project %PROJECT_ID% --quiet
echo [OK] Authenticated and project set to %PROJECT_ID%
echo.

REM ===== STEP 2: Build Docker Image =====
echo [STEP 2/3] Building Docker image with Cloud Build...
echo This may take 2-3 minutes...
echo.

call gcloud builds submit --tag %IMAGE_NAME% --quiet

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Docker build failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [OK] Docker image built successfully: %IMAGE_NAME%
echo.

REM ===== STEP 3: Deploy to Cloud Run Service =====
echo [STEP 3/3] Deploying to Cloud Run Service...
echo.

call gcloud run deploy %SERVICE_NAME% ^
  --image %IMAGE_NAME% ^
  --region %REGION% ^
  --port 8080 ^
  --memory 512Mi ^
  --cpu 1 ^
  --min-instances 0 ^
  --max-instances 5 ^
  --timeout 60s ^
  --allow-unauthenticated ^
  --env-vars-file %ENV_VARS_FILE% ^
  --quiet

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Cloud Run deployment failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [SUCCESS] Deployment Complete!
echo ========================================================
echo.
echo Service Name: %SERVICE_NAME%
echo Region: %REGION%
echo Image: %IMAGE_NAME%
echo.
echo Next steps:
echo   1. Get service URL:
echo      gcloud run services describe %SERVICE_NAME% --region %REGION% --format "value(status.url)"
echo.
echo   2. Test the API:
echo      curl [SERVICE_URL]/health
echo.
echo   3. View logs:
echo      gcloud logging read "resource.type=cloud_run_revision" --limit 20
echo.
echo ========================================================

pause
