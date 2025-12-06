from flask import Blueprint, render_template, request, flash, redirect, url_for
import os
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from google.cloud import storage
from . import app
from .models import User, Submission
from .prompt_utils import get_daily_prompt
from . import db

contest = Blueprint('contest', __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"}
GCS_BUCKET = "art-everyday-2025-art-submissions"
GCS_PREFIX = "submissions/"


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@contest.route('/contest', methods=['POST', 'GET'])
@login_required
def contest_page():
    filename = None
    if request.method == 'POST' and request.form.get("action") == "submit":
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected', category='error')
            return redirect(url_for('contest.contest_page'))

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload an image (png, jpg, jpeg, gif, bmp, svg, webp).', category='error')
            return redirect(url_for('contest.contest_page'))

        safe_name = secure_filename(file.filename)
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        filename = f"{current_user.id}_{ts}_{safe_name}"
        gcs_path = GCS_PREFIX + filename
        # Upload to GCS
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(gcs_path)
            blob.upload_from_file(file, content_type=file.content_type)
            # Make public (optional)
            blob.make_public()
        except Exception as e:
            flash(f'Error uploading to cloud storage: {e}', category='error')
            return redirect(url_for('contest.contest_page'))

        # Record submission in DB
        submission = Submission(
            user_id=current_user.id,
            filename=filename,  # store just the filename
            user=current_user,
            submission_name=os.path.splitext(safe_name)[0],
            prompt=get_daily_prompt(),
            score=0,
            first_place_votes=0,
            second_place_votes=0,
            third_place_votes=0,
        )
        db.session.add(submission)
        db.session.commit()

        flash('Submission uploaded successfully!', category='success')

    now = datetime.utcnow()
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    if now > end_of_day:
        end_of_day = end_of_day + timedelta(days=1)

    return render_template(
        "contest.html",
        user=current_user,
        prompt=get_daily_prompt(),
        filename=filename,
        is_image=True if filename else False,
        contest_end_time=end_of_day.strftime('%Y-%m-%d %H:%M UTC'),
    )