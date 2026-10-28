"""Final smoke tests for the main application workflows."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db


class FinalApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "final_app.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "final-test-key",
            "DATABASE": db_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_customer(self):
        return self.client.post("/signup", data={
            "full_name": "Final Workflow Customer",
            "email": "final-workflow@example.test",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def first_package(self):
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, title, start_date, end_date, image_url
                   FROM tour_packages WHERE is_active = 1 ORDER BY id LIMIT 1"""
            ).fetchone()

    def test_home_catalogue_details_and_css_load(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/packages/").status_code, 200)
        package = self.first_package()
        self.assertIsNotNone(package)
        detail_response = self.client.get(f"/packages/{package['id']}")
        self.assertEqual(detail_response.status_code, 200)
        css_response = self.client.get("/static/css/packages.css")
        self.assertEqual(css_response.status_code, 200)

    def test_customer_can_book_cancel_and_see_package_again(self):
        self.register_customer()
        package = self.first_package()
        booking_response = self.client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["start_date"], "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(booking_response.status_code, 200)
        self.assertIn(b"My bookings", booking_response.data)

        with self.app.app_context():
            booking = get_db().execute(
                """SELECT id FROM bookings WHERE package_id = ? AND status = 'booked'
                   ORDER BY id DESC LIMIT 1""",
                (package["id"],),
            ).fetchone()
        self.assertIsNotNone(booking)

        own_catalogue = self.client.get("/packages/").get_data(as_text=True)
        self.assertNotIn(f'href="/packages/{package["id"]}"', own_catalogue)

        cancelled = self.client.post(
            f"/customer/bookings/{booking['id']}/cancel", follow_redirects=True
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertIn(b"Cancelled bookings", cancelled.data)
        catalogue_again = self.client.get("/packages/").get_data(as_text=True)
        self.assertIn(f'href="/packages/{package["id"]}"', catalogue_again)

    def test_admin_can_open_dashboard_and_customer_cannot(self):
        admin_client = self.app.test_client()
        admin_client.post("/signin", data={
            "email": "admin@tour.local",
            "password": "Admin123!",
        }, follow_redirects=True)
        self.assertEqual(admin_client.get("/admin/").status_code, 200)

        self.register_customer()
        response = self.client.get("/admin/", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
