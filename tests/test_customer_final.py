"""Final regression tests for customer booking workflows."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import create_app
from app.db import get_db


class CustomerFinalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "customer_final.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "customer-test-key",
            "DATABASE": db_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register(self, client, email):
        return client.post("/signup", data={
            "full_name": "Booking Tester",
            "email": email,
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def first_package(self):
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, start_date, end_date FROM tour_packages
                   WHERE is_active = 1 ORDER BY id LIMIT 1"""
            ).fetchone()

    def create_booking(self, client, package):
        response = client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["start_date"], "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, start_date, end_date FROM bookings
                   WHERE package_id = ? AND status = 'booked'
                   ORDER BY id DESC LIMIT 1""",
                (package["id"],),
            ).fetchone()

    def test_reversed_dates_do_not_create_booking(self):
        self.register(self.client, "reversed@example.test")
        package = self.first_package()
        response = self.client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["end_date"], "end_date": package["start_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            count = get_db().execute(
                "SELECT COUNT(*) FROM bookings WHERE user_id = (SELECT id FROM users WHERE email = ?)",
                ("reversed@example.test",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_dates_outside_package_window_are_rejected(self):
        self.register(self.client, "outside@example.test")
        package = self.first_package()
        early_date = (date.fromisoformat(package["start_date"]) - timedelta(days=1)).isoformat()
        response = self.client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": early_date, "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            count = get_db().execute(
                "SELECT COUNT(*) FROM bookings WHERE package_id = ? AND status = 'booked'",
                (package["id"],),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_cancelled_booking_stays_in_history_and_package_returns(self):
        self.register(self.client, "cancel-history@example.test")
        package = self.first_package()
        booking = self.create_booking(self.client, package)

        response = self.client.post(
            f"/customer/bookings/{booking['id']}/cancel", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cancelled bookings", response.data)

        catalogue = self.client.get("/packages/").get_data(as_text=True)
        self.assertIn(f'href="/packages/{package["id"]}"', catalogue)
        with self.app.app_context():
            saved = get_db().execute(
                "SELECT status FROM bookings WHERE id = ?", (booking["id"],)
            ).fetchone()
        self.assertEqual(saved["status"], "cancelled")

    def test_invalid_reschedule_keeps_original_dates(self):
        self.register(self.client, "reschedule-invalid@example.test")
        package = self.first_package()
        booking = self.create_booking(self.client, package)
        response = self.client.post(
            f"/customer/bookings/{booking['id']}/reschedule",
            data={"start_date": package["end_date"], "end_date": package["start_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            saved = get_db().execute(
                "SELECT start_date, end_date FROM bookings WHERE id = ?", (booking["id"],)
            ).fetchone()
        self.assertEqual(saved["start_date"], booking["start_date"])
        self.assertEqual(saved["end_date"], booking["end_date"])


if __name__ == "__main__":
    unittest.main()
