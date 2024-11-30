from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import requests
import logging
from logging.handlers import RotatingFileHandler


db = SQLAlchemy()
socketio = SocketIO()  # Initialize SocketIO


def setup_logging():
    """Set up logging for the application."""
    log_file = "/var/www/kalinuxsec/kalinux_dev/app.log"
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Stream handler for stderr
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )

setup_logging()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)  # Bind SocketIO to the Flask app

    with app.app_context():
         try:
             db.create_all()  # Ensure tables exist
         except Exception as e:
             print(f"Database initialization failed: {e}")


    # Create database tables
#    with app.app_context():
#        db.create_all()

    # Register blueprints
    from .api import api_bp
    from .routes import api_bp as routes_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(routes_bp)

    return app

#    from .api import api_bp
#    from .routes import routes_bp  # Renamed to avoid conflict

#    app.register_blueprint(api_bp, url_prefix="/api")  # API routes
#    app.register_blueprint(routes_bp)  # General application routes

#    return app
