"""Task model."""
from datetime import datetime, timezone
from app import db


class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class Status:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL = [PENDING, IN_PROGRESS, COMPLETED, CANCELLED]


class Task(db.Model):
    """Represents a user task."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(
        db.String(20),
        nullable=False,
        default=Priority.MEDIUM,
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=Status.PENDING,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "user_id": self.user_id,
        }

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title}>"
