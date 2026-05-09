"""Request validation helpers."""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Optional[str]:
    """Return error message or None if valid."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."
    return None


def validate_task_data(data: dict, is_update: bool = False) -> Optional[str]:
    """Return error message or None if valid."""
    from app.models.task import Priority, Status

    if not is_update:
        if not isinstance(data.get("title"), str) or not data.get("title", "").strip():
            return "Title is required."

    if "title" in data:
        if not isinstance(data["title"], str):
            return "Title must be a string."
        if not data["title"].strip():
            return "Title is required."
        if len(data["title"]) > 200:
            return "Title must be under 200 characters."

    if "description" in data and data["description"] is not None and not isinstance(data["description"], str):
        return "Description must be a string."

    if "priority" in data and data["priority"] not in Priority.ALL:
        return f"Priority must be one of: {', '.join(Priority.ALL)}."

    if "status" in data and data["status"] not in Status.ALL:
        return f"Status must be one of: {', '.join(Status.ALL)}."

    return None
