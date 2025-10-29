from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime, date
from flask_login import login_required, current_user
from .models import User, Submission, Vote
from . import db

voting = Blueprint('voting', __name__)


@voting.route('/voting', methods=['GET', 'POST'])
@login_required
def voting_page():
    # Get today's date for filtering
    today = date.today()
    
    if request.method == 'POST':
        # Get the submission IDs from the form
        first_place_id = request.form.get('first_place')
        second_place_id = request.form.get('second_place')
        third_place_id = request.form.get('third_place')
        
        # Validation
        if not first_place_id or not second_place_id or not third_place_id:
            flash('Please select all three places.', category='error')
            return redirect(url_for('voting.voting_page'))
        
        # Check if the user already voted today
        existing_vote = Vote.query.filter_by(user_id=current_user.id).filter(
            db.func.date(Vote.contest_date) == today
        ).first()
        
        if existing_vote:
            flash('You have already voted today!', category='error')
            return redirect(url_for('voting.voting_page'))
        
        # Check for duplicate selections
        if first_place_id == second_place_id or first_place_id == third_place_id or second_place_id == third_place_id:
            flash('You cannot select the same submission multiple times.', category='error')
            return redirect(url_for('voting.voting_page'))
        
        # Check that user isn't voting for their own submission
        user_submission_ids = [str(s.id) for s in current_user.submissions if s.contest_date.date() == today]
        if first_place_id in user_submission_ids or second_place_id in user_submission_ids or third_place_id in user_submission_ids:
            flash('You cannot vote for your own submission.', category='error')
            return redirect(url_for('voting.voting_page'))
        
        # Create the vote record
        new_vote = Vote(
            user_id=current_user.id,
            first_place_submission_id=int(first_place_id),
            second_place_submission_id=int(second_place_id),
            third_place_submission_id=int(third_place_id),
            contest_date=datetime.utcnow()
        )
        db.session.add(new_vote)
        
        # Update vote counts on submissions
        first_submission = Submission.query.get(int(first_place_id))
        second_submission = Submission.query.get(int(second_place_id))
        third_submission = Submission.query.get(int(third_place_id))
        
        if first_submission:
            first_submission.first_place_votes += 1
            first_submission.score += 5  # 3 points for first place
        
        if second_submission:
            second_submission.second_place_votes += 1
            second_submission.score += 3  # 3 points for second place
        
        if third_submission:
            third_submission.third_place_votes += 1
            third_submission.score += 1  # 1 point for third place
        
        db.session.commit()
        
        flash('Your vote has been recorded!', category='success')
        return redirect(url_for('views.home'))
    
    # GET request - display submissions
    # Get all submissions from today (or recent if none today)
    submissions = Submission.query.filter(
        db.func.date(Submission.contest_date) == today
    ).all()
    
    # If no submissions today, get the most recent submissions
    if not submissions:
        submissions = Submission.query.order_by(Submission.contest_date.desc()).limit(10).all()
    
    # Check if user has already voted
    user_has_voted = Vote.query.filter_by(user_id=current_user.id).filter(
        db.func.date(Vote.contest_date) == today
    ).first() is not None
    
    return render_template(
        "voting.html",
        user=current_user,
        submissions=submissions,
        has_voted=user_has_voted,
        prompt="Alien Invasion"  # TODO: Make this dynamic
    )
