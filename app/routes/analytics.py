"""Analytics endpoint using Pandas & NumPy."""
import numpy as np
import pandas as pd
from flask import Blueprint
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from app.models.task import Task
from app.utils.response import success, error

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/", methods=["GET"])
@login_required
def get_analytics():
    try:
        tasks = Task.query.filter_by(user_id=current_user.id).all()
    except SQLAlchemyError:
        return error("Unable to load analytics right now.", 500)

    if not tasks:
        return success(
            {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "in_progress_tasks": 0,
                "cancelled_tasks": 0,
                "completion_percentage": 0.0,
                "priority_distribution": {},
                "status_distribution": {},
                "avg_daily_rate": 0.0,
                "tasks_this_week": 0,
            }
        )

    # Build DataFrame
    try:
        df = pd.DataFrame([t.to_dict() for t in tasks])
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        df["updated_at"] = pd.to_datetime(df["updated_at"], utc=True)
    except (KeyError, ValueError, TypeError):
        return error("Unable to process analytics data.", 500)

    # Basic counts using NumPy / Pandas
    total = len(df)
    completed = int((df["status"] == "completed").sum())
    pending = int((df["status"] == "pending").sum())
    in_progress = int((df["status"] == "in_progress").sum())
    cancelled = int((df["status"] == "cancelled").sum())

    # Completion percentage (NumPy)
    completion_pct = float(np.round((completed / total) * 100, 2)) if total else 0.0

    # Priority distribution
    priority_dist = df["priority"].value_counts().to_dict()
    priority_dist = {k: int(v) for k, v in priority_dist.items()}

    # Status distribution
    status_dist = df["status"].value_counts().to_dict()
    status_dist = {k: int(v) for k, v in status_dist.items()}

    # Tasks created this week
    now = pd.Timestamp.now(tz="UTC")
    week_ago = now - pd.Timedelta(days=7)
    tasks_this_week = int((df["created_at"] >= week_ago).sum())

    # Average daily task creation rate (NumPy)
    if total > 1:
        date_range = (df["created_at"].max() - df["created_at"].min()).days or 1
        avg_daily_rate = float(np.round(total / date_range, 2))
    else:
        avg_daily_rate = float(total)

    return success(
        {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "in_progress_tasks": in_progress,
            "cancelled_tasks": cancelled,
            "completion_percentage": completion_pct,
            "priority_distribution": priority_dist,
            "status_distribution": status_dist,
            "avg_daily_rate": avg_daily_rate,
            "tasks_this_week": tasks_this_week,
        }
    )
