from flask import Blueprint, render_template, request, flash, redirect, url_for
import os
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import app
from .models import User, Submission
from . import db
from .storage import get_storage_handler

contest = Blueprint('contest', __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "svg", "webp"}
MAX_FILE_SIZE = 10485760


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@contest.route('/contest', methods=['POST', 'GET'])
@login_required
def contest_page():
    # Get storage handler (GCS or local)
    storage_handler = get_storage_handler()
    
    # Ensure local upload directory exists (dev mode)
    upload_dir = os.path.join(app.root_path, app.config.get('IMAGE_UPLOADS', 'static/uploaded_images'))
    if not app.config.get('GCS_BUCKET'):
        os.makedirs(upload_dir, exist_ok=True)

    filename = None

    if request.method == 'POST' and request.form.get("action") == "submit":
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No file selected', category='error')
            return redirect(url_for('contest.contest_page'))

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload an image (png, jpg, jpeg, gif, bmp, svg, webp).', category='error')
            return redirect(url_for('contest.contest_page'))

        # Determine uploaded file size safely
        size = request.content_length or 0
        if not size:
            try:
                file.stream.seek(0, os.SEEK_END)
                size = file.stream.tell()
                file.stream.seek(0)
            except Exception:
                size = 0

        if size > MAX_FILE_SIZE:
            flash('The file is too large. Please upload an image of 10MB or less.', category='error')
            return redirect(url_for('contest.contest_page'))

        safe_name = secure_filename(file.filename)
        # Make filename unique by prefixing timestamp and user id
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        filename = f"{current_user.id}_{ts}_{safe_name}"
        
        # Upload to storage (GCS or local)
        file_url = storage_handler.upload_file(file, filename, upload_dir)

        # Record submission in DB
        submission = Submission(
            user_id=current_user.id,
            filename=filename,
            user=current_user,
            submission_name=os.path.splitext(safe_name)[0],
            prompt="Alien Invasion",  # placeholder for now
            score=0,
            first_place_votes=0,
            second_place_votes=0,
            third_place_votes=0,
        )
        db.session.add(submission)
        db.session.commit()

        flash('Submission uploaded successfully!', category='success')

    # Compute an example end-of-day contest time in local terms (UTC shown)
    now = datetime.utcnow()
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    if now > end_of_day:
        end_of_day = end_of_day + timedelta(days=1)

    return render_template(
        "contest.html",
        user=current_user,
        prompt="Alien Invasion",
        filename=filename,
        is_image=True if filename else False,
        contest_end_time=end_of_day.strftime('%Y-%m-%d %H:%M UTC'),
    )