"""Routes for browsing the available tour packages."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db

bp = Blueprint("packages", __name__, url_prefix="/packages")


@bp.route("/")
def listing():
    db = get_db()
    selected_city = request.args.get("city", "").strip()

    customer_id = None
    if g.user is not None and g.user.role == "customer":
        customer_id = g.user.id

    cities = db.execute(
        """SELECT DISTINCT l.city AS city
           FROM locations l
           JOIN package_locations pl ON pl.location_id = l.id
           JOIN tour_packages p ON p.id = pl.package_id
           WHERE p.is_active = 1
           ORDER BY l.city COLLATE NOCASE"""
    ).fetchall()

    packages = db.execute(
        """SELECT p.id, p.title, p.description, p.start_date, p.end_date,
                  CAST(julianday(p.end_date) - julianday(p.start_date) AS INTEGER) + 1
                      AS duration_days,
                  p.price, p.rating, p.image_url,
                  GROUP_CONCAT(DISTINCT l.city) AS city
           FROM tour_packages p
           LEFT JOIN package_locations pl ON pl.package_id = p.id
           LEFT JOIN locations l ON l.id = pl.location_id
           WHERE p.is_active = 1
             AND (
                 ? = '' OR EXISTS (
                     SELECT 1
                     FROM package_locations pl2
                     JOIN locations l2 ON l2.id = pl2.location_id
                     WHERE pl2.package_id = p.id
                       AND LOWER(l2.city) = LOWER(?)
                 )
             )
             AND (
                 ? IS NULL OR NOT EXISTS (
                     SELECT 1 FROM bookings b
                     WHERE b.package_id = p.id
                       AND b.user_id = ?
                       AND b.status = 'booked'
                 )
             )
           GROUP BY p.id
           ORDER BY p.start_date, p.title""",
        (selected_city, selected_city, customer_id, customer_id),
    ).fetchall()

    return render_template(
        "packages/listing.html",
        packages=packages,
        cities=cities,
        selected_city=selected_city,
        is_customer=customer_id is not None,
    )


@bp.route("/<int:package_id>")
def details(package_id):
    db = get_db()
    package = db.execute(
        """SELECT p.*,
                  CAST(julianday(p.end_date) - julianday(p.start_date) AS INTEGER) + 1
                      AS duration_days,
                  GROUP_CONCAT(DISTINCT l.city) AS city
           FROM tour_packages p
           LEFT JOIN package_locations pl ON pl.package_id = p.id
           LEFT JOIN locations l ON l.id = pl.location_id
           WHERE p.id = ? AND p.is_active = 1
           GROUP BY p.id""",
        (package_id,),
    ).fetchone()
    if package is None:
        abort(404)

    if g.user is not None and g.user.role == "customer":
        existing = db.execute(
            """SELECT id FROM bookings
               WHERE user_id = ? AND package_id = ? AND status = 'booked'""",
            (g.user.id, package_id),
        ).fetchone()
        if existing is not None:
            flash("You have already booked this package. Manage it in My bookings.", "info")
            return redirect(url_for("customer.profile"))

    locations = db.execute(
        """SELECT l.id, l.name, l.city, l.description, l.image_url
           FROM locations l
           JOIN package_locations pl ON pl.location_id = l.id
           WHERE pl.package_id = ?
           ORDER BY pl.position, l.name""",
        (package_id,),
    ).fetchall()
    return render_template("packages/details.html", package=package, locations=locations)
