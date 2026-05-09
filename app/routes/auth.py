"""Authentication routes: register, login, logout."""
from urllib.parse import urljoin, urlparse

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint("auth", __name__)


def _is_safe_redirect_target(target: str) -> bool:
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("auth/register.html")

        if not validate_email(email):
            flash("Invalid email address.", "error")
            return render_template("auth/register.html")

        pwd_error = validate_password(password)
        if pwd_error:
            flash(pwd_error, "error")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That username or email is already in use.", "error")
            return render_template("auth/register.html")
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn't create your account right now. Please try again.", "error")
            return render_template("auth/register.html")

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        try:
            user = User.query.filter(
                (User.username == identifier) | (User.email == identifier.lower())
            ).first()
        except SQLAlchemyError:
            db.session.rollback()
            flash("We couldn't complete the login right now. Please try again.", "error")
            return render_template("auth/login.html")

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please try again.", "error")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        next_page = request.args.get("next")
        if next_page and _is_safe_redirect_target(next_page):
            return redirect(next_page)
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
