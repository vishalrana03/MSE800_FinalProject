"""Checks for admin package creation and admin-only access."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db


class AdminWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temp_dir.name) / "admin_workflow.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE": database_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def sign_in_as_admin(self):
        return self.client.post("/signin", data={
            "email": "admin@tour.local",
            "password": "Admin123!",
        }, follow_redirects=True)

    def sign_in_as_customer(self):
        return self.client.post("/signup", data={
            "full_name": "Admin Test Customer",
            "email": "admin-test-customer@example.test",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def test_admin_can_create_package_and_destinations(self):
        self.sign_in_as_admin()
        response = self.client.post("/admin/packages/new", data={
            "title": "Day Four Test Trip",
            "description": "A test package with two stops.",
            "start_date": "2027-06-10",
            "end_date": "2027-06-14",
            "price": "275.50",
            "rating": "4.5",
            "image_url": "https://example.test/main.jpg",
            "destinations": (
                "Harbour Lookout | Test City | View over the harbour | https://example.test/harbour.jpg\n"
                "Forest Walk | Test City | Easy woodland walk"
            ),
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tour package created successfully", response.data)

        with self.app.app_context():
            package = get_db().execute(
                "SELECT id FROM tour_packages WHERE title = ?", ("Day Four Test Trip",)
            ).fetchone()
            self.assertIsNotNone(package)
            destinations = get_db().execute(
                """SELECT l.name, l.city FROM locations l
                   JOIN package_locations pl ON pl.location_id = l.id
                   WHERE pl.package_id = ? ORDER BY pl.position""",
                (package["id"],),
            ).fetchall()
        self.assertEqual(len(destinations), 2)
        self.assertEqual(destinations[0]["name"], "Harbour Lookout")
        self.assertEqual(destinations[1]["name"], "Forest Walk")

    def test_customer_cannot_create_package(self):
        self.sign_in_as_customer()
        with self.app.app_context():
            before = get_db().execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]

        response = self.client.post("/admin/packages/new", data={
            "title": "Should Not Be Saved",
            "description": "Customer is not allowed to create this.",
            "start_date": "2027-06-10",
            "end_date": "2027-06-14",
            "price": "100",
            "rating": "4.0",
            "destinations": "One Place | Test City | Description",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

        with self.app.app_context():
            after = get_db().execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]
        self.assertEqual(before, after)

    def test_signed_out_visitor_is_redirected_from_admin_form(self):
        response = self.client.get("/admin/packages/new")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
