"""Basic integration tests for catalogue, bookings, and admin access."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db


class TourPackageIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temp_dir.name) / "test_tour_package.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DATABASE": database_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def sign_in_as_customer(self):
        return self.client.post("/signup", data={
            "full_name": "Test Customer",
            "email": "customer@example.test",
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def first_package(self):
        with self.app.app_context():
            return get_db().execute(
                "SELECT id, start_date, end_date FROM tour_packages ORDER BY id LIMIT 1"
            ).fetchone()

    def test_city_filter_shows_city_names_not_sqlite_objects(self):
        response = self.client.get("/packages/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('value="Auckland"', html)
        self.assertNotIn("sqlite3.Row object", html)

    def test_details_page_uses_post_booking_form_for_customer(self):
        self.sign_in_as_customer()
        package = self.first_package()
        response = self.client.get(f"/packages/{package['id']}")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('method="post"', html)
        self.assertIn(f'/customer/packages/{package["id"]}/book', html)
        self.assertIn('name="start_date"', html)
        self.assertIn('name="end_date"', html)

    def test_customer_can_book_package(self):
        self.sign_in_as_customer()
        package = self.first_package()
        response = self.client.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["start_date"], "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My bookings", response.data)
        with self.app.app_context():
            count = get_db().execute(
                "SELECT COUNT(*) FROM bookings WHERE package_id = ? AND status = 'booked'",
                (package["id"],),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_customer_cannot_open_admin_package_form(self):
        self.sign_in_as_customer()
        response = self.client.get("/admin/packages/new")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

    def test_admin_cannot_create_package_with_reversed_dates(self):
        self.client.post("/signin", data={
            "email": "admin@tour.local",
            "password": "Admin123!",
        }, follow_redirects=True)
        with self.app.app_context():
            before = get_db().execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]

        response = self.client.post("/admin/packages/new", data={
            "title": "Invalid date package",
            "description": "Dates in the wrong order.",
            "start_date": "2027-05-10",
            "end_date": "2027-05-01",
            "price": "100",
            "rating": "4.0",
            "image_url": "",
            "destinations": "Test Place | Test City | A description",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"End date must be on or after the start date", response.data)
        with self.app.app_context():
            after = get_db().execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
