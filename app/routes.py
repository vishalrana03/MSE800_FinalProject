"""Authentication and starter dashboard routes."""
from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
import sqlite3

from .db import get_db
from .models import User

bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("main.signin"))
        return view(**kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in first.", "error")
            return redirect(url_for("main.signin"))
        if g.user.role != "admin":
            flash("Admin access is required for that page.", "error")
            return redirect(url_for("main.dashboard"))
        return view(**kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = User.find_by_id(user_id) if user_id is not None else None


@bp.route("/")
def home():
    if g.user is not None:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        error = None

        if not full_name:
            error = "Please enter your full name."
        elif not email or "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address."
        elif len(password) < 8:
            error = "Your password must contain at least 8 characters."
        elif password != confirm_password:
            error = "The passwords do not match."
        elif User.find_by_email(email) is not None:
            error = "An account with that email already exists."

        if error is None:
            try:
                user = User.create_customer(full_name, email, password)
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
            else:
                session.clear()
                session["user_id"] = user.id
                flash("Your account has been created.", "success")
                return redirect(url_for("main.dashboard"))

        flash(error, "error")

    return render_template("signup.html")


@bp.route("/signin", methods=("GET", "POST"))
def signin():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.authenticate(email, password)
        if user is None:
            flash("Incorrect email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome back, {user.full_name}.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("signin.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("main.home"))


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@bp.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")
