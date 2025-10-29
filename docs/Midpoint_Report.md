# Art-Everyday — Midpoint Report

Date: 2025-10-22

Team: Tristan Moses, Matthew Moran

Repo: https://github.com/mgm67671/Art-Everyday

Demo video: [Add unlisted URL]

---

## 1) Project Overview

- Title: Art-Everyday — Daily Art Contest Platform
- Summary: Art-Everyday is a web app that hosts a daily prompt-based art contest. Users sign up, view the daily prompt, submit their artwork, and later vote on submissions. The system highlights daily winners and tracks user stats.
- Problem: Creative communities lack lightweight, automated daily challenges with fair submissions/voting and persistent leaderboards.
- Solution: A containerized Flask web app with authentication, daily prompt scheduling, image uploads to object storage, relational database for users/submissions/votes, and a managed serverless runtime for low-ops hosting.

## 2) Current Architecture and Implementation

### 2.1 Architecture diagram (current + target)

```mermaid
flowchart LR
  subgraph Client
    B[Browser]
  end

  B -->|HTTPS| CR[Cloud Run: Flask API + UI]

  subgraph Google Cloud (target)
    CR -->|SQL Proxy| SQL[(Cloud SQL: Postgres/MySQL)]
    CR -->|Images| CS[(Cloud Storage: uploads)]
    SCH[Cloud Scheduler] --> CF[Cloud Function: Daily jobs]
    CF --> SQL
    CF --> CS
    SM[Secret Manager] -.-> CR
    CB[Cloud Build CI] --> CR
  end

  classDef cloud fill:#eef6ff,stroke:#6aa1ff,stroke-width:1px
  class CR,SQL,CS,SCH,CF,SM,CB cloud
```

Notes:
- Current state: local SQLite DB, local filesystem for uploads, Dockerfile to containerize Flask app.
- Target state: Cloud Run hosting, Cloud SQL (managed DB), Cloud Storage (images), Cloud Scheduler + Cloud Function (daily prompt rotation, winner finalization), Secret Manager for keys, Cloud Build for CI/CD.

### 2.2 Services implemented so far

- Flask (Python) web app with Blueprints and Jinja templates
  - Routes:
    - `/` Home (static placeholders for winners)
    - `/login`, `/signup`, `/logout` (Flask-Login auth)
    - `/contest` (daily prompt page; now accepts image uploads)
    - `/profile` (placeholder)
    - `/voting` (placeholder template)
  - Templates and Bootstrap-based UI
- Data layer: SQLAlchemy models with SQLite (local development)
  - `User`: id, email, username, password_hash, timestamps, win counters
  - `Submission` (sic): id, user_id, filename, prompt, timestamps, score and vote counters
- Containerization: Dockerfile (python:3.11-slim) and `main.py` entrypoint exposing port 5000

### 2.3 DevOps and automation to date

- Container build works locally with Docker
- Planned CI: GitHub Actions workflow to build the Docker image on push (added as placeholder)
- Next: Cloud Build trigger or Actions to build and deploy to Cloud Run (requires project/registry creds)

### 2.4 Evidence of partial functionality

Include screenshots in this section before submission (replace placeholders):

- [ ] Screenshot: Signup, then Login success flash message
- [ ] Screenshot: Contest page showing today’s prompt and upload form
- [ ] Screenshot: Post-upload success flash and the uploaded filename visible on page
- [ ] Screenshot: SQLite DB entries (e.g., DB Browser for SQLite) showing a `Submission` row
- [ ] Log snippet: Flask startup and POST /contest handling in the terminal

```
Example log snippet
 * Serving Flask app 'website'
 * Debug mode: on
 POST /contest 200 - Submission uploaded successfully (user 1)
```

## 3) Demonstration Video (5–10 min)

Suggested flow:
1. Brief intro (goal, features, tech stack)
2. Run locally via Docker and open the app
3. Walkthrough:
   - Signup + login
   - Navigate to Contest page; show prompt
   - Upload an image file; show success flash and DB record
   - Briefly show code for upload validation and save path
4. Architecture overview: explain diagram and target cloud services
5. Status + next steps

Recording tips: use Loom/Zoom/OBS; 1080p; keep terminal and browser visible side by side.

## 4) Progress Summary

Completed so far:
- Core Flask app scaffold with auth (login/signup/logout)
- Basic pages and navigation
- SQLAlchemy models and database init (SQLite dev)
- Image upload implemented on `/contest` with validation and DB record
- Dockerfile for containerization
- CI stub (GitHub Actions) to build image on push

Met milestones:
- Prototype app running locally in a container
- Working auth and at least one meaningful workflow (image upload)

Challenges encountered:
- Initial code contained placeholders/incomplete routes (contest/voting)
- Hardcoded SECRET_KEY and SQLite path (to be migrated to cloud secrets/DB)
- Naming inconsistency: `Submission` typo in model name retained for compatibility

## 5) Remaining Work

Features and improvements:
- Voting flow: display submissions, capture ranked votes, compute winners daily
- Daily prompt scheduling and winner selection (Scheduler + Function/Job)
- User profile page: show submissions and stats
- Admin or automated moderation checks (file size/type, content restrictions)
- Replace SQLite with Cloud SQL; add migrations (Alembic/Flask-Migrate)
- Store uploads in Cloud Storage and serve via signed URLs/CDN
- Authentication hardening (password policy, email verification optional)

DevOps/Cloud:
- Deploy to Cloud Run (build + deploy actions; artifact registry)
- Secrets in Secret Manager (Flask secret key, DB creds)
- VPC connector for Cloud SQL
- Monitoring (Cloud Logging/Trace) and error reporting
- IaC (Terraform) for reproducible environments (optional if time allows)

Risks:
- Schedule risk for full voting + daily automation
- Cloud SQL networking and IAM configuration
- Handling user-uploaded content safely and at scale
- Time for testing and polish (screenshots/video/UX tweaks)

Short plan to complete:
- Week 1: Voting pages + DB schema for votes; Cloud Storage integration
- Week 2: Winner calculation + daily job (Scheduler + Function); Cloud SQL migration
- Week 3: Cloud Run deployment + Secrets; E2E test + demo polish
- Buffer: Fixes, docs, and final presentation prep

## 6) Appendix

### 6.1 How to run locally

See the root README for commands. In short:
- Python venv: install requirements and run `python main.py`
- Docker: build image and run container exposing port 5000

### 6.2 Data model (current)

- User(id, email, username, password_hash, account_creation_date, first/second/third_place_wins)
- Submission(id, user_id, filename, submission_name, contest_date, submission_time, prompt, score, vote counters)

### 6.3 Security notes

- Do not commit real secrets. Move SECRET_KEY and DB URL to environment variables and Secret Manager for cloud deploys.
- Validate and sanitize uploads; restrict size and content types. Consider scanning for malicious content.
