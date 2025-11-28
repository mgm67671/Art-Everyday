# PowerShell deployment script for Windows
# GCP Infrastructure Setup Script for Art-Everyday

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [string]$Region = "us-central1",
    [string]$DbInstanceName = "art-everyday-db",
    [string]$DbName = "art_everyday",
    [string]$DbUser = "art_everyday_user",
    [string]$ServiceAccountName = "art-everyday-sa"
)

$ErrorActionPreference = "Stop"

$GcsBucket = "$ProjectId-art-submissions"

Write-Host "Setting up Art-Everyday infrastructure on GCP..." -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"

# Set project
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "`nEnabling required APIs..." -ForegroundColor Yellow
gcloud services enable `
    cloudbuild.googleapis.com `
    run.googleapis.com `
    sqladmin.googleapis.com `
    storage.googleapis.com `
    cloudscheduler.googleapis.com `
    cloudfunctions.googleapis.com `
    secretmanager.googleapis.com

# Create service account
Write-Host "`nCreating service account..." -ForegroundColor Yellow
gcloud iam service-accounts create $ServiceAccountName `
    --display-name="Art Everyday Service Account" `
    --description="Service account for Art-Everyday application"

$ServiceAccountEmail = "$ServiceAccountName@$ProjectId.iam.gserviceaccount.com"

# Grant necessary permissions
Write-Host "`nGranting IAM permissions..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/secretmanager.secretAccessor"

# Create Cloud SQL instance
Write-Host "`nCreating Cloud SQL PostgreSQL instance (this may take several minutes)..." -ForegroundColor Yellow
gcloud sql instances create $DbInstanceName `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=$Region `
    --network=default `
    --no-assign-ip `
    --database-flags=cloudsql.iam_authentication=on

# Generate random password
Add-Type -AssemblyName System.Web
$RootPassword = [System.Web.Security.Membership]::GeneratePassword(32, 10)

# Set root password
Write-Host "`nSetting database root password..." -ForegroundColor Yellow
gcloud sql users set-password postgres `
    --instance=$DbInstanceName `
    --password=$RootPassword

# Create database
Write-Host "`nCreating database..." -ForegroundColor Yellow
gcloud sql databases create $DbName `
    --instance=$DbInstanceName

# Create database user
Write-Host "`nCreating database user..." -ForegroundColor Yellow
$DbPassword = [System.Web.Security.Membership]::GeneratePassword(32, 10)
gcloud sql users create $DbUser `
    --instance=$DbInstanceName `
    --password=$DbPassword

# Store database password in Secret Manager
Write-Host "`nStoring database password in Secret Manager..." -ForegroundColor Yellow
$DbPassword | gcloud secrets create db-password `
    --data-file=- `
    --replication-policy="automatic"

gcloud secrets add-iam-policy-binding db-password `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/secretmanager.secretAccessor"

# Generate and store Flask secret key
Write-Host "`nGenerating Flask secret key..." -ForegroundColor Yellow
$FlaskSecret = [System.Web.Security.Membership]::GeneratePassword(64, 20)
$FlaskSecret | gcloud secrets create flask-secret-key `
    --data-file=- `
    --replication-policy="automatic"

gcloud secrets add-iam-policy-binding flask-secret-key `
    --member="serviceAccount:$ServiceAccountEmail" `
    --role="roles/secretmanager.secretAccessor"

# Create Cloud Storage bucket
Write-Host "`nCreating Cloud Storage bucket..." -ForegroundColor Yellow
gsutil mb -p $ProjectId -c STANDARD -l $Region gs://$GcsBucket/
gsutil uniformbucketlevelaccess set on gs://$GcsBucket/
gsutil iam ch serviceAccount:${ServiceAccountEmail}:objectAdmin gs://$GcsBucket/

# Set bucket to allow public read for images
gsutil iam ch allUsers:objectViewer gs://$GcsBucket/

# Build and push container image
Write-Host "`nBuilding container image..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/${ProjectId}/art-everyday:latest"

# Deploy to Cloud Run
Write-Host "`nDeploying to Cloud Run..." -ForegroundColor Yellow
$CloudSqlConnection = "{0}:{1}:{2}" -f $ProjectId, $Region, $DbInstanceName

gcloud run deploy art-everyday `
    --image "gcr.io/${ProjectId}/art-everyday:latest" `
    --platform managed `
    --region $Region `
    --service-account $ServiceAccountEmail `
    --add-cloudsql-instances $CloudSqlConnection `
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CloudSqlConnection},DB_USER=${DbUser},DB_NAME=${DbName},GCS_BUCKET=${GcsBucket},FLASK_ENV=production" `
    --set-secrets "DB_PASS=db-password:latest,SECRET_KEY=flask-secret-key:latest" `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 10 `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300

# Deploy Cloud Functions
Write-Host "`nDeploying Cloud Functions..." -ForegroundColor Yellow

# Deploy finalize contest function
gcloud functions deploy finalize-daily-contest `
    --gen2 `
    --runtime python311 `
    --region $Region `
    --source ./cloud_functions `
    --entry-point finalize_daily_contest `
    --trigger-http `
    --service-account $ServiceAccountEmail `
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CloudSqlConnection},DB_USER=${DbUser},DB_NAME=${DbName},GCP_PROJECT=${ProjectId}" `
    --set-secrets "DB_PASS=db-password:latest" `
    --no-allow-unauthenticated

# Deploy cleanup function
gcloud functions deploy cleanup-old-data `
    --gen2 `
    --runtime python311 `
    --region $Region `
    --source ./cloud_functions `
    --entry-point cleanup_old_data `
    --trigger-http `
    --service-account $ServiceAccountEmail `
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CloudSqlConnection},DB_USER=${DbUser},DB_NAME=${DbName},GCP_PROJECT=${ProjectId}" `
    --set-secrets "DB_PASS=db-password:latest" `
    --no-allow-unauthenticated

# Create Cloud Scheduler jobs
Write-Host "`nCreating Cloud Scheduler jobs..." -ForegroundColor Yellow

# Job to finalize daily contest at 11:59 PM UTC
gcloud scheduler jobs create http finalize-daily-contest `
    --location $Region `
    --schedule "59 23 * * *" `
    --time-zone "UTC" `
    --uri "https://${Region}-${ProjectId}.cloudfunctions.net/finalize-daily-contest" `
    --http-method POST `
    --oidc-service-account-email $ServiceAccountEmail `
    --oidc-token-audience "https://${Region}-${ProjectId}.cloudfunctions.net/finalize-daily-contest"

# Job to cleanup old data weekly
gcloud scheduler jobs create http cleanup-old-data `
    --location $Region `
    --schedule "0 2 * * 0" `
    --time-zone "UTC" `
    --uri "https://${Region}-${ProjectId}.cloudfunctions.net/cleanup-old-data" `
    --http-method POST `
    --oidc-service-account-email $ServiceAccountEmail `
    --oidc-token-audience "https://${Region}-${ProjectId}.cloudfunctions.net/cleanup-old-data"

# Get Cloud Run URL
$ServiceUrl = gcloud run services describe art-everyday --platform managed --region $Region --format 'value(status.url)'

Write-Host "`n================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "Cloud Run URL: $ServiceUrl"
Write-Host "Cloud SQL Instance: $CloudSqlConnection"
Write-Host "GCS Bucket: gs://$GcsBucket"
Write-Host "`nNext steps:"
Write-Host "1. Visit $ServiceUrl to access your application"
Write-Host "2. Create your first user account"
Write-Host "3. Monitor logs: gcloud run logs tail art-everyday --region $Region"
Write-Host "4. View Cloud SQL: gcloud sql instances describe $DbInstanceName"
