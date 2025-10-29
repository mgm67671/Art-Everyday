# Art-Everyday — AI Coding Agent Instructions

## Architecture Overview

Flask web app with Blueprint-based modular design. Current stack: SQLite + local file storage. Target: Google Cloud (Cloud Run, Cloud SQL, Cloud Storage).

**Core pattern**: Flask app factory in `website/__init__.py` creates app with 4 blueprints:
- `views` (homepage, profile) - `website/views.py`
- `auth` (login/signup/logout) - `website/auth.py`
- `contest` (daily art submissions) - `website/contest.py`
- `voting` (rank top 3 submissions) - `website/voting.py`

**Data models** (`website/models.py`):
- `User`: email, username, password_hash, win counters
- `Submission`: user_id, filename, prompt, score, vote counters (first/second/third)
- `Vote`: user_id, contest_date, first/second/third_place_submission_id

## Critical Conventions

### Database patterns
- **SQLAlchemy initialization**: `db` imported from `website/__init__.py`, models use `db.Model`
- **Date filtering**: Always use `db.func.date()` for comparing datetime columns to dates
  ```python
  # Correct way to filter by today's date
  Vote.query.filter(db.func.date(Vote.contest_date) == date.today())
  ```
- **Relationships**: Use `db.relationship()` for foreign keys, `lazy=True` for performance

### File uploads
- Uploads stored in `website/static/uploaded_images/` (hardcoded in `__init__.py` config)
- Filenames prefixed with `{user_id}_{timestamp}_{secure_filename}` for uniqueness
- Allowed extensions: png, jpg, jpeg, gif, bmp, svg, webp (enforced in `contest.py`)
- Templates reference uploads via `/static/uploaded_images/{filename}`

### Authentication
- Flask-Login handles sessions via `LoginManager` in `__init__.py`
- Passwords hashed with `werkzeug.security.generate_password_hash(method='pbkdf2:sha256', salt_length=32)`
- `@login_required` decorator protects routes; `current_user` provides logged-in user context
- SECRET_KEY is hardcoded in `__init__.py` (migrate to Secret Manager for production)

### Voting rules (enforced in `voting.py`)
1. One vote per user per day (checked via `Vote.query.filter_by(user_id).filter(db.func.date(contest_date) == today)`)
2. Cannot vote for own submission
3. Cannot select same submission multiple times
4. Scoring: 1st place = +3, 2nd = +2, 3rd = +1 points to `Submission.score`

## Development Workflow

**Local setup**:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py  # Runs on localhost:5000
```

**Database**: SQLite auto-created at `instance/database.db` on first run via `create_db()` in `__init__.py`. Delete to reset.

**Docker**:
```powershell
docker build -t art-everyday:local .
docker run --rm -p 5000:5000 art-everyday:local
```

**Testing flow**: See `DEMO_COMMANDS.md` for complete demo sequence (create accounts → upload submissions → vote → view winners).

## Important Gotchas

- **Blueprint imports**: Use relative imports (`from . import db`, `from .models import User`) inside `website/` package
- **Template paths**: Flask looks in `website/templates/`, reference with just filename (`"home.html"`)
- **Static files**: Prefix with `/static/` in templates (`/static/uploaded_images/`)
- **Flash messages**: Two categories used: `'success'` (green) and `'error'` (red)
- **Prompt hardcoded**: All routes use `"Alien Invasion"` placeholder - TODO: make dynamic
- **Time handling**: Uses `func.now()` for DB defaults, `datetime.utcnow()` for timestamps

## Cloud Migration Path

Current architecture (local dev) → Target (production):
- SQLite → Cloud SQL (Postgres/MySQL)
- Local file storage → Cloud Storage buckets
- `python main.py` → Cloud Run container
- Manual prompts → Cloud Scheduler + Cloud Functions
- Hardcoded secrets → Secret Manager

See `docs/Midpoint_Report.md` for full migration plan and architecture diagram.
