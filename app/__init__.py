"""
Smart Task Manager application factory.
"""
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, request, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.utils.response import error, is_api_request

load_dotenv(override=True)

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()
bcrypt = Bcrypt()


def get_socketio_async_mode() -> str:
    """Choose a Socket.IO backend that works reliably in local development."""
    configured_mode = os.getenv("SOCKETIO_ASYNC_MODE")
    if configured_mode:
        return configured_mode

    # Python 3.13 on Windows is more predictable with threading mode.
    if os.name == "nt":
        return "threading"

    return "threading"


def create_app(config_name: str = "development") -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/task_manager_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode=get_socketio_async_mode(),
    )

    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.tasks import tasks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    with app.app_context():
        from app.models.task import Task  # noqa: F401
        from app.models.user import User  # noqa: F401

        db.create_all()

    @login_manager.unauthorized_handler
    def unauthorized():
        if is_api_request():
            return error("Authentication required.", 401)
        flash(login_manager.login_message, login_manager.login_message_category)
        return redirect(url_for(login_manager.login_view, next=request.url))

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        if is_api_request():
            return error(exc.description, exc.code or 500)
        return exc

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(exc: SQLAlchemyError):
        app.logger.exception("Database error: %s", exc)
        db.session.rollback()
        if is_api_request():
            return error("A database error occurred. Please try again.", 500)
        return "A database error occurred. Please try again.", 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        app.logger.exception("Unexpected error: %s", exc)
        db.session.rollback()
        if is_api_request():
            return error("An unexpected server error occurred.", 500)
        return "An unexpected server error occurred.", 500

    return app
