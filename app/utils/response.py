"""Standardised JSON response helpers."""
from flask import jsonify, request


def success(data=None, message: str = "Success", status_code: int = 200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error(message: str = "An error occurred", status_code: int = 400):
    return jsonify({"success": False, "message": message}), status_code


def is_api_request() -> bool:
    """Return True when the current request targets the JSON API."""
    return request.path.startswith("/api/")
