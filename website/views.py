from flask import Blueprint, render_template, send_from_directory
from flask_login import login_required, current_user
import os
from.__init__ import get_app
# a blueprint is a collection of routes
views = Blueprint('views', __name__)
# this runs whenever we go to the url '/'

@views.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(get_app().root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@views.route('/')
def home():
    return render_template("home.html", user=current_user)

@views.route('/profile')
def prev_jobs():
    return render_template("profile.html", user=current_user)



