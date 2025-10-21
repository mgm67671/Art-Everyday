# . = "from current package"
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


# id: the unique id associated with the job
# key: the steganographic key for the file
# date: When the job was performed
# file_name: The name and extension of the plaintext file
# user_id: the id of the user who did the job
class Subimssion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    filename = db.Column(db.String(128))
    submission_name = db.Column(db.String(128))
    contest_date = db.Column(db.DateTime(timezone=True), default=func.now())
    submission_time = db.Column(db.DateTime(timezone=True), default=func.now())
    prompt = db.Column(db.String)
    
    score = db.Column(db.Integer)

    first_place_votes = db.Column(db.Integer)
    second_place_votes = db.Column(db.Integer)
    third_place_votes = db.Column(db.Integer)

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

    submissions = db.relationship('Subimssion')
    
    first_place_wins = db.Column(db.Integer)
    second_place_wins = db.Column(db.Integer)
    third_place_wins = db.Column(db.Integer)


