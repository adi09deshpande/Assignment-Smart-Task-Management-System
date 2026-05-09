"""Application entry point."""
import os

from app import create_app, socketio
from app.utils.socket_events import *  # noqa: F401,F403 - registers handlers

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    async_mode = getattr(socketio.server, "async_mode", "unknown")

    print(f"\nTaskFlow running at http://{host}:{port}")
    print(f"Socket.IO async mode: {async_mode}\n")
    socketio.run(app, host=host, port=port, debug=debug)
