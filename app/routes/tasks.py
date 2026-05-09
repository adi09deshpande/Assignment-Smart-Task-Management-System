"""REST API for task CRUD operations."""
from datetime import datetime, timezone

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

from app import db, socketio
from app.models.task import Priority, Status, Task
from app.utils.validators import validate_task_data
from app.utils.response import success, error

tasks_bp = Blueprint("tasks", __name__)


def _emit_update(event: str, payload: dict) -> None:
    """Broadcast a task event to all connected clients in the user's room."""
    socketio.emit(event, payload, room=f"user_{current_user.id}")


def _get_json_payload(*, require_body: bool) -> tuple[dict | None, tuple | None]:
    """Validate JSON request bodies and return either the payload or an API error."""
    if not request.is_json:
        return None, error("Request body must be valid JSON.", 415)

    data = request.get_json(silent=True)
    if data is None:
        return None, error("Malformed JSON request body.", 400)
    if not isinstance(data, dict):
        return None, error("JSON request body must be an object.", 400)
    if require_body and not data:
        return None, error("Request body cannot be empty.", 400)
    return data, None


def _parse_due_date(value: str | None):
    """Parse ISO 8601 due dates sent by the frontend."""
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid due_date format. Use ISO 8601.") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


# ── GET all tasks ──────────────────────────────────────────────────────────────
@tasks_bp.route("/", methods=["GET"])
@login_required
def get_tasks():
    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    search = request.args.get("search", "").strip()

    if status_filter and status_filter not in Status.ALL:
        return error(f"Status must be one of: {', '.join(Status.ALL)}.")
    if priority_filter and priority_filter not in Priority.ALL:
        return error(f"Priority must be one of: {', '.join(Priority.ALL)}.")

    query = Task.query.filter_by(user_id=current_user.id)

    if status_filter:
        query = query.filter_by(status=status_filter)
    else:
        query = query.filter(Task.status != Status.CANCELLED)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )

    tasks = query.order_by(Task.created_at.desc()).all()
    return success([t.to_dict() for t in tasks])


# ── GET single task ────────────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["GET"])
@login_required
def get_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return error("Task not found.", 404)
    return success(task.to_dict())


# ── POST create task ───────────────────────────────────────────────────────────
@tasks_bp.route("/", methods=["POST"])
@login_required
def create_task():
    data, payload_error = _get_json_payload(require_body=True)
    if payload_error:
        return payload_error

    err = validate_task_data(data)
    if err:
        return error(err)

    try:
        task = Task(
            title=data["title"].strip(),
            description=(data.get("description") or "").strip(),
            priority=data.get("priority", "medium"),
            status=data.get("status", "pending"),
            user_id=current_user.id,
            due_date=_parse_due_date(data.get("due_date")),
        )
        db.session.add(task)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return error(str(exc))
    except SQLAlchemyError:
        db.session.rollback()
        return error("Unable to create the task right now.", 500)

    _emit_update("task_created", task.to_dict())
    return success(task.to_dict(), "Task created successfully.", 201)


# ── PUT update task ────────────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return error("Task not found.", 404)

    data, payload_error = _get_json_payload(require_body=True)
    if payload_error:
        return payload_error

    err = validate_task_data(data, is_update=True)
    if err:
        return error(err)

    if task.status == "cancelled":
        allowed_keys = {"status"}
        if any(key not in allowed_keys for key in data.keys()):
            return error("Cancelled tasks cannot be edited. Restore the task first.", 400)
        if "status" in data and data["status"] == "cancelled":
            return error("Task is already cancelled.", 400)

    if "title" in data:
        task.title = data["title"].strip()
    if "description" in data:
        task.description = (data["description"] or "").strip()
    if "priority" in data:
        task.priority = data["priority"]
    if "status" in data:
        task.status = data["status"]
    if "due_date" in data:
        try:
            task.due_date = _parse_due_date(data["due_date"])
        except ValueError as exc:
            return error(str(exc))

    task.updated_at = datetime.now(timezone.utc)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("Unable to update the task right now.", 500)

    _emit_update("task_updated", task.to_dict())
    return success(task.to_dict(), "Task updated successfully.")


# ── DELETE task ────────────────────────────────────────────────────────────────
@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id: int):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return error("Task not found.", 404)

    task_data = task.to_dict()
    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("Unable to delete the task right now.", 500)

    _emit_update("task_deleted", {"id": task_id})
    return success(task_data, "Task deleted successfully.")
