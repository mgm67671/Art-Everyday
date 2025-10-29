# Art-Everyday

Daily prompt-based art contest platform built with Flask and Docker.

## Run with Docker
1. Start Docker Engine

2. Build the image
```
docker build -t art-everyday:local .
```
3. Run the container
```
docker run --rm -p 5000:5000 art-everyday:local
```
4. Open http://localhost:5000

## Notes

- Default dev DB is SQLite (`instance/database.db`) created automatically on first run.
- Uploads are stored under `website/static/uploaded_images` during development.
- For production, plan to migrate to Cloud Run + Cloud SQL + Cloud Storage and move secrets to environment variables/Secret Manager.
