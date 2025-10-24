# Art-Everyday

Daily prompt-based art contest platform built with Flask and Docker.

## Run locally (Python)

Prereqs: Python 3.11+

1. Create a virtual environment and install deps
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2. Start the app
```
python main.py
```
3. Open http://localhost:5000

## Run with Docker

1. Build the image
```
docker build -t art-everyday:local .
```
2. Run the container
```
docker run --rm -p 5000:5000 art-everyday:local
```
3. Open http://localhost:5000

## Midpoint Report and Demo

- Midpoint Report (draft): docs/Midpoint_Report.md
- Demo Video: [add unlisted link]

## Notes

- Default dev DB is SQLite (`instance/database.db`) created automatically on first run.
- Uploads are stored under `website/static/uploaded_images` during development.
- For production, plan to migrate to Cloud Run + Cloud SQL + Cloud Storage and move secrets to environment variables/Secret Manager.
