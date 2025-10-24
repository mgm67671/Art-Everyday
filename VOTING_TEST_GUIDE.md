# Voting Feature Testing Guide

## Quick Test Flow

The voting feature is now fully functional! Here's how to test it locally:

### 1. Start the Application
The app is already running at: http://localhost:5000

### 2. Create Test Accounts

You'll need at least 2 accounts to test voting (since you can't vote for your own submission):

**Account 1 (Artist):**
- Go to http://localhost:5000/signup
- Email: artist1@test.com
- Password: testpass123

**Account 2 (Voter):**
- Logout (click Logout in nav)
- Go to http://localhost:5000/signup
- Email: voter1@test.com
- Password: testpass123

### 3. Submit Artwork (as Account 1)

1. Login as artist1@test.com
2. Navigate to "Art Contest" in the menu
3. Upload a test image (any PNG, JPG, GIF, or BMP file)
4. Click "Submit"
5. You should see a success message

**Repeat with more accounts** if you want multiple submissions to vote on.

### 4. Vote on Submissions (as Account 2)

1. Logout and login as voter1@test.com
2. Navigate to "Art Voting" in the menu
3. You should see all submitted artworks for today
4. Select your top 3 choices:
   - 1st Place: 3 points
   - 2nd Place: 2 points
   - 3rd Place: 1 point
5. Click "Submit Vote"
6. You should see "Your vote has been recorded!" message

### 5. Verify Vote Recording

You can verify votes were recorded:

1. Try voting again (same account) - you should see "You have already voted today!"
2. Check the submission scores - they should update with points
3. Open the SQLite database (`instance/database.db`) with DB Browser for SQLite to see:
   - `vote` table: your vote record
   - `submission` table: updated vote counts and scores

## Features Implemented

✅ **Vote Model:** Tracks user votes with 1st/2nd/3rd place selections
✅ **Voting Route:** `/voting` displays submissions and handles vote submission
✅ **Vote Validation:**
  - Users can only vote once per day
  - Cannot vote for their own submission
  - Must select 3 different submissions
  - All selections are required
✅ **Score Tracking:** Automatic score calculation (3/2/1 points)
✅ **Vote Counters:** Tracks first/second/third place votes per submission
✅ **UI:** Clean voting interface with image display and radio buttons

## What to Screenshot for Demo

1. **Contest page:** Upload interface with success message
2. **Voting page:** Display of submissions with voting options
3. **Vote success:** "Your vote has been recorded!" message
4. **Already voted:** "You have already voted today" error message
5. **Database:** SQLite DB showing vote and submission records with updated scores

## Potential Issues & Solutions

**Issue:** No submissions show on voting page
- **Solution:** Make sure you uploaded at least one image via the contest page first

**Issue:** Can't vote (all options grayed out)
- **Solution:** You may be logged in as the only submitter. Create another account to vote.

**Issue:** Database errors
- **Solution:** Delete `instance/database.db` and restart the app to recreate tables with the new Vote model

## Next Steps

After local testing works well:
- Add profile page to show user's submissions and voting history
- Implement daily winner calculation and announcement on home page
- Add Cloud Storage for image uploads
- Deploy to Cloud Run with Cloud SQL
- Add Cloud Scheduler to automate daily contest resets
