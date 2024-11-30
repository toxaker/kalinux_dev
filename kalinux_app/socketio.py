from flask_socketio import SocketIO, emit, disconnect
import psutil
import threading
import time
from flask_login import current_user
import requests

socketio = SocketIO(cors_allowed_origins="*")  # Initialize SocketIO

# Background task to emit system metrics to all connected clients
def emit_system_metrics():
    while True:
        metrics = {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "network": {
                "sent": psutil.net_io_counters().bytes_sent,
                "recv": psutil.net_io_counters().bytes_recv,
            },
        }
        socketio.emit("system_metrics", metrics, broadcast=True)  # Broadcast metrics
        time.sleep(1)  # Emit every second

# Start metrics emission in a background thread
def start_background_task():
    thread = threading.Thread(target=emit_system_metrics, daemon=True)
    thread.start()

# Event handlers
@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:  # Check authentication
        emit("error", {"data": "Unauthorized"})
        disconnect()
        return
    emit("my response", {"data": f"Connected as {current_user.get_id()}"})
    print(f"Client connected: {current_user.get_id()}")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

# Start the background task
start_background_task()
