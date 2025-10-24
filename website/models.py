# . = "from current package"
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


# id: the unique id associated with the job
# key: the steganographic key for the file
# date: When the job was performed
# file_name: The name and extension of the plaintext file
# user_id: the id of the user who did the job
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    filename = db.Column(db.String(128))
    submission_name = db.Column(db.String(128))
    contest_date = db.Column(db.DateTime(timezone=True), default=func.now())
    submission_time = db.Column(db.DateTime(timezone=True), default=func.now())
    prompt = db.Column(db.String)
    
    score = db.Column(db.Integer, default=0)

    first_place_votes = db.Column(db.Integer, default=0)
    second_place_votes = db.Column(db.Integer, default=0)
    third_place_votes = db.Column(db.Integer, default=0)


# Vote model to track user votes
# Each user can vote once per contest date, ranking 3 submissions
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    contest_date = db.Column(db.DateTime(timezone=True), default=func.now())
    vote_time = db.Column(db.DateTime(timezone=True), default=func.now())
    
    # The submissions voted for (1st, 2nd, 3rd place)
    first_place_submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))
    second_place_submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))
    third_place_submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))

# id: the unique id associated with the user
# email: the email of the user
# password_hash: the hashed password
# password_salt: the salt for the hash
# submissions: all submissions made by the user
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(150))
    account_creation_date = db.Column(db.DateTime(timezone=True), default=func.now())

    submissions = db.relationship('Submission')
    votes = db.relationship('Vote')
    
    first_place_wins = db.Column(db.Integer, default=0)
    second_place_wins = db.Column(db.Integer, default=0)
    third_place_wins = db.Column(db.Integer, default=0)




