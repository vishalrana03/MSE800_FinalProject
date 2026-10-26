"""Booking rules shared by the customer booking routes."""
from datetime import date

from ..db import get_db


class BookingServiceError(ValueError):
    """Raised when a booking does not meet the booking rules."""


def _read_date(value, label):
    if not value:
        raise BookingServiceError(f"Please choose a {label}.")
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise BookingServiceError(f"Please enter a valid {label}.") from error


def _get_package(package_id):
    package = get_db().execute(
        "SELECT id, start_date, end_date, is_active FROM tour_packages WHERE id = ?",
        (package_id,),
    ).fetchone()
    if package is None or not package["is_active"]:
        raise BookingServiceError("This package is not available right now.")
    return package


def _check_dates(package, start_date, end_date):
    start = _read_date(start_date, "start date")
    end = _read_date(end_date, "end date")
    package_start = _read_date(package["start_date"], "package start date")
    package_end = _read_date(package["end_date"], "package end date")

    if end < start:
        raise BookingServiceError("The end date must be on or after the start date.")
    if start < package_start or end > package_end:
        raise BookingServiceError("Choose dates inside the package's advertised date range.")


def list_customer_bookings(user_id):
    """Return the active bookings belonging to one customer."""
    return get_db().execute(
        """SELECT b.id AS booking_id, b.start_date, b.end_date, b.status,
                  b.created_at, p.id AS package_id, p.title AS package_title,
                  p.image_url, p.price, p.rating,
                  p.start_date AS package_start_date,
                  p.end_date AS package_end_date
           FROM bookings b
           JOIN tour_packages p ON p.id = b.package_id
           WHERE b.user_id = ? AND b.status = 'booked'
           ORDER BY b.created_at DESC, b.id DESC""",
        (user_id,),
    ).fetchall()


def create_booking(user_id, package_id, start_date, end_date):
    """Create one booking after checking availability, dates, and duplicates."""
    db = get_db()
    package = _get_package(package_id)
    _check_dates(package, start_date, end_date)

    existing = db.execute(
        "SELECT id FROM bookings WHERE user_id = ? AND package_id = ? AND status = 'booked'",
        (user_id, package_id),
    ).fetchone()
    if existing:
        raise BookingServiceError("You already have an active booking for this package.")

    cursor = db.execute(
        """INSERT INTO bookings (user_id, package_id, start_date, end_date, status)
           VALUES (?, ?, ?, ?, 'booked')""",
        (user_id, package_id, start_date, end_date),
    )
    db.commit()
    return cursor.lastrowid


def cancel_booking(user_id, booking_id):
    """Cancel an active booking only when it belongs to this customer."""
    db = get_db()
    result = db.execute(
        """UPDATE bookings SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
           WHERE id = ? AND user_id = ? AND status = 'booked'""",
        (booking_id, user_id),
    )
    db.commit()
    return result.rowcount == 1


def reschedule_booking(user_id, booking_id, start_date, end_date):
    """Change the dates for an active booking owned by the signed-in customer."""
    db = get_db()
    booking = db.execute(
        """SELECT b.package_id, p.start_date AS package_start,
                  p.end_date AS package_end, p.is_active
           FROM bookings b JOIN tour_packages p ON p.id = b.package_id
           WHERE b.id = ? AND b.user_id = ? AND b.status = 'booked'""",
        (booking_id, user_id),
    ).fetchone()
    if booking is None:
        raise BookingServiceError("Active booking not found in your account.")
    if not booking["is_active"]:
        raise BookingServiceError("This package is no longer available for rescheduling.")

    _check_dates(
        {"start_date": booking["package_start"], "end_date": booking["package_end"]},
        start_date,
        end_date,
    )
    db.execute(
        """UPDATE bookings SET start_date = ?, end_date = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ? AND user_id = ? AND status = 'booked'""",
        (start_date, end_date, booking_id, user_id),
    )
    db.commit()
    return True
