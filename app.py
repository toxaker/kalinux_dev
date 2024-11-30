from flask.cli import with_appcontext
import os
import sys
import logging
from kalinux_app import create_app
from kalinux_app.socketio_app import start_background_task, socketio
from kalinux_app.log_analyzer import LogAnalyzer
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = create_app()

socketio.init_app(app, cors_allowed_origins="*")  # Initialize with Flask app

start_background_task(app)

if __name__ == "__main__":
    socketio.run(app, debug=False)
