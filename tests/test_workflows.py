"""End-to-end checks for booking, rescheduling, cancellation, and availability."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import create_app
from app.db import get_db


class CustomerWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temp_dir.name) / "customer_workflows.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE": database_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_customer(self, client=None, email="workflow@example.test"):
        client = client or self.client
        return client.post("/signup", data={
            "full_name": "Workflow Customer",
            "email": email,
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def package_with_longest_window(self):
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, start_date, end_date
                   FROM tour_packages
                   WHERE is_active = 1 AND end_date > start_date
                   ORDER BY julianday(end_date) - julianday(start_date) DESC
                   LIMIT 1"""
            ).fetchone()

    def book_package(self, package):
        response = self.client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["start_date"], "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, start_date, end_date FROM bookings
                   WHERE package_id = ? AND status = 'booked' ORDER BY id DESC LIMIT 1""",
                (package["id"],),
            ).fetchone()

    def test_cancelled_package_returns_to_customer_catalogue(self):
        self.register_customer()
        package = self.package_with_longest_window()
        booking = self.book_package(package)

        response = self.client.get("/packages/")
        self.assertNotIn(f'href="/packages/{package["id"]}"', response.get_data(as_text=True))

        response = self.client.post(
            f"/customer/bookings/{booking['id']}/cancel", follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cancelled bookings", response.data)

        response = self.client.get("/packages/")
        self.assertIn(f'href="/packages/{package["id"]}"', response.get_data(as_text=True))

    def test_customer_can_reschedule_an_active_booking(self):
        self.register_customer()
        package = self.package_with_longest_window()
        booking = self.book_package(package)
        old_end = date.fromisoformat(booking["end_date"])
        package_end = date.fromisoformat(package["end_date"])
        new_end = min(old_end - timedelta(days=1), package_end)
        new_start = date.fromisoformat(booking["start_date"])
        if new_end < new_start:
            new_start = new_end

        response = self.client.post(
            f"/customer/bookings/{booking['id']}/reschedule",
            data={"start_date": new_start.isoformat(), "end_date": new_end.isoformat()},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            saved = get_db().execute(
                "SELECT start_date, end_date FROM bookings WHERE id = ?", (booking["id"],)
            ).fetchone()
        self.assertEqual(saved["start_date"], new_start.isoformat())
        self.assertEqual(saved["end_date"], new_end.isoformat())

    def test_customer_cannot_cancel_another_customers_booking(self):
        self.register_customer()
        package = self.package_with_longest_window()
        booking = self.book_package(package)

        other_client = self.app.test_client()
        self.register_customer(other_client, email="another-customer@example.test")
        other_client.post(f"/customer/bookings/{booking['id']}/cancel", follow_redirects=True)

        with self.app.app_context():
            saved = get_db().execute(
                "SELECT status FROM bookings WHERE id = ?", (booking["id"],)
            ).fetchone()
        self.assertEqual(saved["status"], "booked")


if __name__ == "__main__":
    unittest.main()
