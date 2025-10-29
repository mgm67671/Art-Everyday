from flask import Blueprint, render_template, send_from_directory
from flask_login import login_required, current_user
from datetime import date, timedelta
import os
from.__init__ import get_app
from .models import Submission, User
from . import db
# a blueprint is a collection of routes
views = Blueprint('views', __name__)
# this runs whenever we go to the url '/'

@views.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(get_app().root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@views.route('/')
def home():
    # Get yesterday's date for "yesterday's winners"
    yesterday = date.today() - timedelta(days=1)
    
    # Get top 3 submissions from yesterday (or most recent if none yesterday)
    top_submissions = Submission.query.filter(
        db.func.date(Submission.contest_date) == yesterday
    ).order_by(Submission.score.desc()).limit(3).all()
    
    # If no submissions from yesterday, get the top 3 overall most recent
    if not top_submissions or len(top_submissions) < 3:
        top_submissions = Submission.query.order_by(
            Submission.score.desc(), 
            Submission.contest_date.desc()
        ).limit(3).all()
    
    # Pad with None if we don't have 3 submissions
    while len(top_submissions) < 3:
        top_submissions.append(None)
    
    return render_template(
        "home.html", 
        user=current_user,
        first_place=top_submissions[0],
        second_place=top_submissions[1],
        third_place=top_submissions[2],
        prompt="Alien Invasion"  # TODO: Make this dynamic
    )

@views.route('/profile')
def prev_jobs():
    return render_template("profile.html", user=current_user)



