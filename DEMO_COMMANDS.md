# Quick Demo Commands

## Start the App

```powershell
cd "c:\Users\might\OneDrive\Desktop\School\Cloud Computing\Art-Everyday"
python main.py
```

Then open: http://localhost:5000

## View Database (Optional)

Download and install [DB Browser for SQLite](https://sqlitebrowser.org/dl/)

Open file: `instance/database.db`

**Tables to inspect:**
- `user` - See registered accounts
- `subimssion` - See submissions with vote counts and scores
- `vote` - See all votes cast

## Test Accounts (Create These)

**Artist 1:**
- Email: artist1@test.com
- Password: testpass123

**Artist 2:**
- Email: artist2@test.com  
- Password: testpass123

**Voter:**
- Email: voter@test.com
- Password: testpass123

## Demo Flow Checklist

- [ ] Show homepage (empty or with previous winners)
- [ ] Create account 1, login
- [ ] Go to Art Contest, upload image
- [ ] Logout, create account 2, login
- [ ] Upload another image
- [ ] Logout, create voter account, login
- [ ] Go to Art Voting
- [ ] Select top 3, submit vote
- [ ] Try voting again (see "already voted" message)
- [ ] View profile page (shows your submissions/votes)
- [ ] Go to homepage (shows top submissions with scores)
- [ ] Optional: Show database with vote records

## Docker Build & Run (Optional for Demo)

```powershell
# Build the image
docker build -t art-everyday:demo .

# Run the container
docker run --rm -p 5000:5000 art-everyday:demo
```

Then open: http://localhost:5000

## Screenshots to Capture

1. **Signup page** - Clean form
2. **Login success** - Flash message
3. **Contest page** - Upload form with prompt
4. **Upload success** - Green success message
5. **Voting page** - All submissions with radio buttons
6. **Vote success** - "Your vote has been recorded!"
7. **Already voted** - Error message
8. **Profile page** - Submissions with scores and vote breakdown
9. **Home page** - Top 3 winners with images
10. **Database** - SQLite showing vote and submission tables

## Cloud Architecture (for presentation)

Reference: `docs/Midpoint_Report.md`

**Current:** Local SQLite + local file storage + Flask dev server

**Target:** 
- Cloud Run (Flask container)
- Cloud SQL (managed database)
- Cloud Storage (image uploads)
- Cloud Scheduler (daily automation)
- Secret Manager (secrets)
- Cloud Build (CI/CD)

## Troubleshooting

**App won't start:**
```powershell
pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug
```

**Database errors:**
Delete `instance/database.db` and restart (will recreate tables)

**Images not showing:**
Check that `website/static/uploaded_images/` folder exists

**Can't vote:**
Make sure you have multiple submissions from different users
