from flask import Blueprint, render_template, request, flash, redirect, url_for
from.models import User
from . import db
from werkzeug.security import gen_salt, generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import string
import secrets


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        t_email = request.form.get('email')
        t_pass = request.form.get('password')

        t_user = User.query.filter_by(email=t_email).first()

        if t_user:
            if check_password_hash(t_user.password_hash, t_pass):
                login_user(t_user, remember=True)
                flash('Logged in successfully', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again', category='error')
        else:
            flash('Email not in use, try again', category='error')



    return render_template("login.html", text="Testing", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    flash("Logged out", category='success')
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST' and request.form.get("action") == "submit":
        t_email = request.form.get('email')
        password = request.form.get('password')
        user = request.form.get('username')
        confirm_password = request.form.get('confirmpassword')

        if User.query.filter_by(email=t_email).first():
            flash("Your email is already in use.", category='error')
        elif len(t_email) < 4:
            flash("Your email must be 4 characters or longer.", category='error')
        elif len(t_email) >150:
            flash("Your email must be shorter than 150 characters", category='error')
        elif len(user) < 4:
            flash("Your user name must be 4 characters or longer.", category='error')
        elif len(user) > 32:
            flash("Your user name must be shorter than 32 characters", category='error')
        elif password != confirm_password:
            flash("Your passwords must match.", category='error')
        elif len(password) < 7:
            flash("Your password must be 7 characters or longer.", category='error')
        elif len(password) > 32:
            flash("Your password must be shorter than 32 characters", category='error')
        else:
            t_user = User(email=t_email, password_hash=generate_password_hash(password, method='pbkdf2:sha256', salt_length=32), username=user)
            db.session.add(t_user)
            db.session.commit()
            login_user(t_user, remember=True)
            flash("Account created!", category='success')
            return redirect(url_for('views.home'))
    elif request.method == 'POST' and request.form.get("action") == "generate_pass":
        return render_template("signup.html", user=current_user, generated_pass = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20)))
    return render_template("signup.html", user=current_user)
