# Art-Everyday

Daily prompt-based art contest platform built with Flask, Docker, and Google Cloud Platform.

## Highlights
- 🎨 Daily prompts with image submissions
- 🗳️ Rank-based voting (1st/2nd/3rd)
- 🏆 Automatic winner tracking and profiles
- ☁️ Cloud-native: Cloud Run + Cloud SQL + Cloud Storage

## Teammate Quick Guide
- Prod URL: copy the Cloud Run Service URL from the console or output (e.g., `https://<service>-<project>.us-central1.run.app`).
- Local run:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
- Deploy (Windows PowerShell):
   ```powershell
   .\deploy-gcp.ps1 -ProjectId "YOUR_PROJECT_ID"
   ```
- Environment (prod): Cloud Run sets `CLOUD_SQL_CONNECTION_NAME`, `DB_*`, `SECRET_KEY`, `GCS_BUCKET`.
- Images: stored in GCS at `submissions/<filename>`; templates use `{{ filename | image_url }}`.
- Logs:
   ```powershell
   gcloud run services logs read art-everyday --region us-central1 --project YOUR_PROJECT_ID --limit 100
   ```

## Quick Start (Local)
- Prereqs: Python 3.11+
- Install and run:
   ```bash
   pip install -r requirements.txt
   python main.py
   # open http://localhost:5000
   ```

Optional Docker
```bash
docker build -t art-everyday:local .
docker run --rm -p 5000:5000 art-everyday:local
```

## Deploy to Google Cloud
Quickest path (Windows PowerShell):
```powershell
.\deploy-gcp.ps1 -ProjectId "YOUR_PROJECT_ID"
```
What it sets up:
- Cloud Run service for the Flask app
- Cloud SQL (PostgreSQL) + connection via Unix socket
- Cloud Storage bucket for image uploads (uniform access)
- Secret Manager (DB password, Flask secret)
- Cloud Functions + Cloud Scheduler for daily finalize and weekly cleanup

Environment variables (Cloud Run):
```
CLOUD_SQL_CONNECTION_NAME=project:region:instance
DB_USER=art_everyday_user
DB_NAME=art_everyday
DB_PASS=from-Secret-Manager
SECRET_KEY=from-Secret-Manager
GCS_BUCKET=your-bucket-name
FLASK_ENV=production
```

## How Images Work
- Local (dev): files saved under `website/static/uploaded_images/`.
- Production (GCP): files saved to GCS at `submissions/<filename>`.
- Templates use a filter `image_url` to generate the correct URL automatically.
   - For GCS, returns a public URL like `https://storage.googleapis.com/<bucket>/submissions/<filename>`.
   - Ensure the bucket has uniform access ON and `allUsers:objectViewer` if you want public reads.

## Project Structure
```
Art-Everyday/
├── website/
│   ├── __init__.py          # App factory, config, image_url filter
│   ├── auth.py              # Login/signup
│   ├── contest.py           # Image upload flow
│   ├── voting.py            # Voting logic
│   ├── views.py             # Home/profile
│   ├── models.py            # SQLAlchemy models
│   ├── storage.py           # Local+GCS storage abstraction
│   ├── static/
│   └── templates/
├── cloud_functions/
│   └── main.py              # finalize_daily_contest, cleanup_old_data
├── main.py                  # Entrypoint
├── Dockerfile               # Production container
├── requirements.txt
└── deploy-gcp.ps1           # Windows deploy helper
```

## Troubleshooting (Common)
- Cloud SQL auth error mentioning control characters:
   - Likely due to a newline in the DB password. Recreate the secret by writing the password without a trailing newline.
- Cloud Storage error about legacy ACL with uniform access:
   - Do not call `blob.make_public()`; set bucket-level public read if needed and rely on public URLs.
- Service unavailable after deploy:
   - Tail logs and look for import/config issues.
   ```powershell
   gcloud run services logs read art-everyday --project YOUR_PROJECT_ID --region us-central1 --limit 50
   ```

## Monitoring & Ops
```powershell
# Logs
gcloud run services logs read art-everyday --project YOUR_PROJECT_ID --region us-central1 --limit 100

# Check Cloud SQL
gcloud sql instances describe art-everyday-db --project YOUR_PROJECT_ID

# List uploaded images in GCS
gsutil ls gs://YOUR_BUCKET/submissions/
```

## Security
- Password hashing (Flask-Login)
- SQLAlchemy ORM queries
- Secret Manager for credentials
- HTTPS via Cloud Run

## License
MIT
