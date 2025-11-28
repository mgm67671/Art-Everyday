#!/bin/bash
# GCP Infrastructure Setup Script for Art-Everyday
# This script sets up all required GCP resources

set -e  # Exit on error

# Configuration - UPDATE THESE VALUES
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
DB_INSTANCE_NAME="art-everyday-db"
DB_NAME="art_everyday"
DB_USER="art_everyday_user"
SERVICE_ACCOUNT_NAME="art-everyday-sa"
GCS_BUCKET="${PROJECT_ID}-art-submissions"

echo "Setting up Art-Everyday infrastructure on GCP..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    cloudscheduler.googleapis.com \
    cloudfunctions.googleapis.com \
    secretmanager.googleapis.com

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Art Everyday Service Account" \
    --description="Service account for Art-Everyday application"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions
echo "Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Create Cloud SQL instance
echo "Creating Cloud SQL PostgreSQL instance (this may take several minutes)..."
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --network=default \
    --no-assign-ip \
    --database-flags=cloudsql.iam_authentication=on

# Set root password
echo "Setting database root password..."
gcloud sql users set-password postgres \
    --instance=$DB_INSTANCE_NAME \
    --password=$(openssl rand -base64 32)

# Create database
echo "Creating database..."
gcloud sql databases create $DB_NAME \
    --instance=$DB_INSTANCE_NAME

# Create database user
echo "Creating database user..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

# Store database password in Secret Manager
echo "Storing database password in Secret Manager..."
echo -n "$DB_PASSWORD" | gcloud secrets create db-password \
    --data-file=- \
    --replication-policy="automatic"

gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Generate and store Flask secret key
echo "Generating Flask secret key..."
FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
echo -n "$FLASK_SECRET" | gcloud secrets create flask-secret-key \
    --data-file=- \
    --replication-policy="automatic"

gcloud secrets add-iam-policy-binding flask-secret-key \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

# Create Cloud Storage bucket
echo "Creating Cloud Storage bucket..."
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$GCS_BUCKET/
gsutil uniformbucketlevelaccess set on gs://$GCS_BUCKET/
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT_EMAIL}:objectAdmin gs://$GCS_BUCKET/

# Set bucket to allow public read for images
gsutil iam ch allUsers:objectViewer gs://$GCS_BUCKET/

# Build and push container image
echo "Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/art-everyday:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"

gcloud run deploy art-everyday \
    --image gcr.io/$PROJECT_ID/art-everyday:latest \
    --platform managed \
    --region $REGION \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --add-cloudsql-instances $CLOUD_SQL_CONNECTION \
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION},DB_USER=${DB_USER},DB_NAME=${DB_NAME},GCS_BUCKET=${GCS_BUCKET},FLASK_ENV=production" \
    --set-secrets "DB_PASS=db-password:latest,SECRET_KEY=flask-secret-key:latest" \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300

# Deploy Cloud Functions
echo "Deploying Cloud Functions..."

# Deploy finalize contest function
gcloud functions deploy finalize-daily-contest \
    --gen2 \
    --runtime python311 \
    --region $REGION \
    --source ./cloud_functions \
    --entry-point finalize_daily_contest \
    --trigger-http \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION},DB_USER=${DB_USER},DB_NAME=${DB_NAME},GCP_PROJECT=${PROJECT_ID}" \
    --set-secrets "DB_PASS=db-password:latest" \
    --no-allow-unauthenticated

# Deploy cleanup function
gcloud functions deploy cleanup-old-data \
    --gen2 \
    --runtime python311 \
    --region $REGION \
    --source ./cloud_functions \
    --entry-point cleanup_old_data \
    --trigger-http \
    --service-account $SERVICE_ACCOUNT_EMAIL \
    --set-env-vars "CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION},DB_USER=${DB_USER},DB_NAME=${DB_NAME},GCP_PROJECT=${PROJECT_ID}" \
    --set-secrets "DB_PASS=db-password:latest" \
    --no-allow-unauthenticated

# Create Cloud Scheduler jobs
echo "Creating Cloud Scheduler jobs..."

# Job to finalize daily contest at 11:59 PM UTC
gcloud scheduler jobs create http finalize-daily-contest \
    --location $REGION \
    --schedule "59 23 * * *" \
    --time-zone "UTC" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/finalize-daily-contest" \
    --http-method POST \
    --oidc-service-account-email $SERVICE_ACCOUNT_EMAIL \
    --oidc-token-audience "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/finalize-daily-contest"

# Job to cleanup old data weekly
gcloud scheduler jobs create http cleanup-old-data \
    --location $REGION \
    --schedule "0 2 * * 0" \
    --time-zone "UTC" \
    --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/cleanup-old-data" \
    --http-method POST \
    --oidc-service-account-email $SERVICE_ACCOUNT_EMAIL \
    --oidc-token-audience "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/cleanup-old-data"

# Get Cloud Run URL
SERVICE_URL=$(gcloud run services describe art-everyday --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "================================"
echo "Deployment Complete!"
echo "================================"
echo "Cloud Run URL: $SERVICE_URL"
echo "Cloud SQL Instance: $CLOUD_SQL_CONNECTION"
echo "GCS Bucket: gs://$GCS_BUCKET"
echo ""
echo "Next steps:"
echo "1. Visit $SERVICE_URL to access your application"
echo "2. Create your first user account"
echo "3. Monitor logs: gcloud run logs tail art-everyday --region $REGION"
echo "4. View Cloud SQL: gcloud sql instances describe $DB_INSTANCE_NAME"
echo ""
