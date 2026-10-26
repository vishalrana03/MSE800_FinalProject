"""Customer profile, booking, cancellation, and rescheduling routes."""
from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..services.booking_service import (
    BookingServiceError,
    cancel_booking as cancel_booking_service,
    create_booking,
    list_customer_bookings,
    reschedule_booking as reschedule_booking_service,
)

bp = Blueprint("customer", __name__, url_prefix="/customer")


def customer_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to manage your bookings.", "error")
            return redirect(url_for("main.signin"))
        if g.user.role != "customer":
            flash("This page is for customer accounts.", "error")
            return redirect(url_for("admin.dashboard"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/profile")
@customer_required
def profile():
    bookings = list_customer_bookings(g.user.id)
    return render_template("customer/profile.html", bookings=bookings)


@bp.route("/packages/<int:package_id>/book", methods=("POST",))
@customer_required
def book_package(package_id):
    """Create a booking from the POST form on the package details page."""
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()

    try:
        create_booking(g.user.id, package_id, start_date, end_date)
    except BookingServiceError as error:
        flash(str(error), "error")
        return redirect(url_for("packages.details", package_id=package_id))

    flash("Your package has been added to My bookings.", "success")
    return redirect(url_for("customer.profile"))


@bp.route("/bookings/<int:booking_id>/cancel", methods=("POST",))
@customer_required
def cancel_booking(booking_id):
    changed = cancel_booking_service(g.user.id, booking_id)
    if changed:
        flash("Booking cancelled. The package is available to you again.", "success")
    else:
        flash("That active booking was not found in your account.", "error")
    return redirect(url_for("customer.profile"))


@bp.route("/bookings/<int:booking_id>/reschedule", methods=("POST",))
@customer_required
def reschedule_booking(booking_id):
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    try:
        reschedule_booking_service(g.user.id, booking_id, start_date, end_date)
    except BookingServiceError as error:
        flash(str(error), "error")
    else:
        flash("Your booking dates have been updated.", "success")
    return redirect(url_for("customer.profile"))
