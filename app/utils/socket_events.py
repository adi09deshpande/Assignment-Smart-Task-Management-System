"""WebSocket event handlers."""
from flask_login import current_user
from flask_socketio import disconnect, emit, join_room, leave_room

from app import socketio


@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        disconnect()
        return False

    room = f"user_{current_user.id}"
    join_room(room)
    emit("connected", {"message": f"Connected as {current_user.username}", "room": room})


@socketio.on("disconnect")
def handle_disconnect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        leave_room(room)


@socketio.on("ping")
def handle_ping():
    emit("pong", {"message": "Server is alive"})
