"""Final checks for admin access and package form validation."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db


class AdminFinalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "admin_final.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "admin-test-key",
            "DATABASE": db_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def sign_in_admin(self):
        return self.client.post("/signin", data={
            "email": "admin@tour.local",
            "password": "Admin123!",
        }, follow_redirects=True)

    def sign_in_customer(self):
        return self.client.post("/signup", data={
            "full_name": "Regular Customer",
            "email": "admin-final-customer@example.test",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def package_count(self):
        with self.app.app_context():
            return get_db().execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]

    def package_form(self, **overrides):
        data = {
            "title": "Final Admin Test Package",
            "description": "A package used for the final test.",
            "start_date": "2027-08-10",
            "end_date": "2027-08-14",
            "price": "250.00",
            "rating": "4.5",
            "image_url": "https://example.test/final.jpg",
            "destinations": "Harbour Point | Test City | A view of the harbour",
        }
        data.update(overrides)
        return data

    def test_guest_cannot_open_admin_dashboard_or_package_form(self):
        dashboard = self.client.get("/admin/")
        form = self.client.get("/admin/packages/new")
        self.assertEqual(dashboard.status_code, 302)
        self.assertEqual(form.status_code, 302)
        self.assertIn("/signin", dashboard.headers["Location"])
        self.assertIn("/signin", form.headers["Location"])

    def test_customer_cannot_create_a_package(self):
        self.sign_in_customer()
        before = self.package_count()
        response = self.client.post("/admin/packages/new", data=self.package_form())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.package_count(), before)

    def test_admin_invalid_rating_is_rejected(self):
        self.sign_in_admin()
        before = self.package_count()
        response = self.client.post(
            "/admin/packages/new", data=self.package_form(rating="6.0")
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.package_count(), before)

    def test_admin_must_provide_at_least_one_destination(self):
        self.sign_in_admin()
        before = self.package_count()
        response = self.client.post(
            "/admin/packages/new", data=self.package_form(destinations="   ")
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.package_count(), before)

    def test_admin_can_create_package_and_destination(self):
        self.sign_in_admin()
        response = self.client.post(
            "/admin/packages/new", data=self.package_form(), follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tour package created successfully", response.data)
        with self.app.app_context():
            saved = get_db().execute(
                "SELECT id FROM tour_packages WHERE title = ?",
                ("Final Admin Test Package",),
            ).fetchone()
            self.assertIsNotNone(saved)
            destination = get_db().execute(
                """SELECT l.name, l.city FROM locations l
                   JOIN package_locations pl ON pl.location_id = l.id
                   WHERE pl.package_id = ?""",
                (saved["id"],),
            ).fetchone()
        self.assertEqual(destination["name"], "Harbour Point")
        self.assertEqual(destination["city"], "Test City")


if __name__ == "__main__":
    unittest.main()
