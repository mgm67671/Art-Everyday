from flask import Blueprint, render_template, request, flash, redirect
import os
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import app
from.models import User, Subimssion
from . import db

contest = Blueprint('contest', __name__)

@contest.route('/contest', methods=['POST', 'GET'])
def contest_page():
    if request.method == 'POST' and request.files['file'] and request.form.get("action") == "submit":
        print("Submitted: ", request.files['file'].name)
        

    return render_template("contest.html", user=current_user, prompt = "Alien Invasion")