from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os
import sqlalchemy

db = SQLAlchemy()
DB_NAME = "database.db"

app = Flask(__name__)

# Configuration from environment variables (GCP-ready)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['IMAGE_UPLOADS'] = os.environ.get('IMAGE_UPLOADS', 'static/uploaded_images')
app.config['GCS_BUCKET'] = os.environ.get('GCS_BUCKET', None)
app.config['MAX_CONTENT_LENGTH'] = 10485760

# Database configuration - supports both SQLite (dev) and Cloud SQL (production)
if os.environ.get('CLOUD_SQL_CONNECTION_NAME'):
    # Production: Cloud SQL with Unix socket
    db_user = os.environ.get('DB_USER', 'postgres')
    db_pass = os.environ.get('DB_PASS', '')
    db_name = os.environ.get('DB_NAME', 'art_everyday')
    db_socket_dir = os.environ.get('DB_SOCKET_DIR', '/cloudsql')
    cloud_sql_connection_name = os.environ['CLOUD_SQL_CONNECTION_NAME']
    
    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_sock": f"{db_socket_dir}/{cloud_sql_connection_name}/.s.PGSQL.5432"}
        ),
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = pool.url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 300}
else:
    # Development: SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def create_app():
    
    db.init_app(app)

    # Add template filter for image URLs
    @app.template_filter('image_url')
    def image_url_filter(filename):
        """Generate the correct URL for an image file."""
        from .storage import get_storage_handler
        if filename:
            storage_handler = get_storage_handler()
            return storage_handler.get_file_url(filename)
        return ''

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



