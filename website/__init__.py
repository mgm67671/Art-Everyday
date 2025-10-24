from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
db = SQLAlchemy()
DB_NAME = "database.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gndilbkcxtbivglojxxkhjgjojpgzgcbcejrjfxsezzegqltjrjryglvhljdteyqfvcszqvembjrzztearazxoaixjcwqwyguapsabfahmyerntekukprmupdewltlsu'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['IMAGE_UPLOADS'] = 'static/uploaded_images'

def create_app():
    
    db.init_app(app)

    

    from.views import views
    from.auth import auth
    from.contest import contest
    from.voting import voting

    # these register the auth and views routes, the url prefix is anything before the / that must be there to get into the route
    app.register_blueprint(views, url_prefix = '/')
    app.register_blueprint(auth, url_prefix = '/')
    app.register_blueprint(contest, url_prefix = '/')
    app.register_blueprint(voting, url_prefix = '/')

    from.models import User, Submission, Vote

    create_db(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    return app

def create_db(app):
    with app.app_context():
        db.create_all()

def get_app():
    print("getting: ", app)
    return app



