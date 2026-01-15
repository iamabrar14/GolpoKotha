from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import Config

import sqlite3  # Keep for SQLite check
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()  # Add this line
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# SQLite foreign key enforcement (only for SQLite)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Only execute for SQLite, not PostgreSQL
    if isinstance(dbapi_connection, sqlite3.Connection):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Add this line

    # Import models
    from .models import User, Post, Comment, Notification

    # Create tables - Remove this as migrations will handle it
    # with app.app_context():
    #     db.create_all()

    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app