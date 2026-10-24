"""Admin pages for managing the tour package catalogue."""
from datetime import date
from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..db import get_db

bp = Blueprint("admin", __name__, url_prefix="/admin")


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


def read_destinations(raw_text, package_image):
    """Read one destination per line: name | city | description | image URL."""
    destinations = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError("Each destination line needs at least a place name and city, separated by |.")
        name = parts[0]
        city = parts[1]
        description = parts[2] if len(parts) > 2 else ""
        image_url = parts[3] if len(parts) > 3 and parts[3] else package_image
        destinations.append((name, city, description, image_url))

    if not destinations:
        raise ValueError("Enter at least one destination.")
    return destinations


@bp.route("/")
@admin_required
def dashboard():
    packages = get_db().execute(
        """SELECT p.id, p.title, p.start_date, p.end_date, p.price, p.rating,
                  GROUP_CONCAT(DISTINCT l.city) AS cities
           FROM tour_packages p
           LEFT JOIN package_locations pl ON pl.package_id = p.id
           LEFT JOIN locations l ON l.id = pl.location_id
           WHERE p.is_active = 1
           GROUP BY p.id ORDER BY p.created_at DESC"""
    ).fetchall()
    return render_template("admin/dashboard.html", packages=packages)


@bp.route("/packages/new", methods=("GET", "POST"))
@admin_required
def add_package():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        image_url = request.form.get("image_url", "").strip()
        destinations_text = request.form.get("destinations", "").strip()
        error = None

        try:
            start_value = date.fromisoformat(start_date)
            end_value = date.fromisoformat(end_date)
            price = float(request.form.get("price", ""))
            rating = float(request.form.get("rating", "0"))
            destinations = read_destinations(destinations_text, image_url)
        except (TypeError, ValueError) as problem:
            error = str(problem) or "Enter valid dates, price, rating, and destinations."
        else:
            if not title:
                error = "Enter a package title."
            elif end_value < start_value:
                error = "End date must be on or after the start date."
            elif price < 0:
                error = "Price cannot be negative."
            elif not 0 <= rating <= 5:
                error = "Rating must be between 0 and 5."

        if error:
            flash(error, "error")
            return render_template("admin/add_package.html", form=request.form)

        db = get_db()
        cursor = db.execute(
            """INSERT INTO tour_packages
               (title, description, start_date, end_date, price, rating, image_url, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, start_date, end_date, price, rating, image_url, g.user.id),
        )
        package_id = cursor.lastrowid
        seen_locations = set()

        for position, (name, city, place_description, place_image) in enumerate(destinations, start=1):
            existing = db.execute(
                """SELECT id FROM locations
                   WHERE LOWER(name) = LOWER(?) AND LOWER(city) = LOWER(?)""",
                (name, city),
            ).fetchone()
            if existing:
                location_id = existing["id"]
            else:
                location_cursor = db.execute(
                    """INSERT INTO locations (name, city, description, image_url)
                       VALUES (?, ?, ?, ?)""",
                    (name, city, place_description, place_image),
                )
                location_id = location_cursor.lastrowid

            if location_id not in seen_locations:
                db.execute(
                    """INSERT INTO package_locations (package_id, location_id, position)
                       VALUES (?, ?, ?)""",
                    (package_id, location_id, position),
                )
                seen_locations.add(location_id)

        db.commit()
        flash("Tour package created successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_package.html", form={})
