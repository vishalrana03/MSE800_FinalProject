"""Final checks for the package catalogue and filters."""
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import get_db


class CatalogueFinalTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "catalogue_final.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "catalogue-test-key",
            "DATABASE": db_path,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register_customer(self, client, email):
        return client.post("/signup", data={
            "full_name": "Catalogue Tester",
            "email": email,
            "password": "TestPass123!",
            "confirm_password": "TestPass123!",
        }, follow_redirects=True)

    def get_first_package(self):
        with self.app.app_context():
            return get_db().execute(
                """SELECT id, title, start_date, end_date, image_url
                   FROM tour_packages WHERE is_active = 1 ORDER BY id LIMIT 1"""
            ).fetchone()

    def test_catalogue_shows_city_names_and_not_database_objects(self):
        response = self.client.get("/packages/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("sqlite3.Row object", html)
        self.assertIn('id="city"', html)
        self.assertIn("Auckland", html)

    def test_city_filter_keeps_matching_packages(self):
        with self.app.app_context():
            city_row = get_db().execute(
                """SELECT l.city FROM locations l
                   JOIN package_locations pl ON pl.location_id = l.id
                   JOIN tour_packages p ON p.id = pl.package_id
                   WHERE p.is_active = 1 ORDER BY l.city LIMIT 1"""
            ).fetchone()
            self.assertIsNotNone(city_row)
            city = city_row["city"]
            expected_titles = {
                row["title"] for row in get_db().execute(
                    """SELECT DISTINCT p.title FROM tour_packages p
                       JOIN package_locations pl ON pl.package_id = p.id
                       JOIN locations l ON l.id = pl.location_id
                       WHERE p.is_active = 1 AND LOWER(l.city) = LOWER(?)""",
                    (city,),
                ).fetchall()
            }

        response = self.client.get("/packages/", query_string={"city": city})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn(f'value="{city}" selected', html)
        for title in expected_titles:
            self.assertIn(title, html)

    def test_package_image_is_rendered_as_an_image(self):
        package = self.get_first_package()
        self.assertIsNotNone(package)
        response = self.client.get("/packages/")
        html = response.get_data(as_text=True)
        self.assertIn(f'href="/packages/{package["id"]}"', html)
        if package["image_url"]:
            self.assertIn('class="package-card__image"', html)
            self.assertNotIn("sqlite3.Row object", html)

    def test_booked_package_is_hidden_only_from_that_customer(self):
        package = self.get_first_package()
        self.assertIsNotNone(package)

        customer_one = self.app.test_client()
        self.register_customer(customer_one, "catalogue-one@example.test")
        booked = customer_one.post(
            f"/customer/packages/{package['id']}/book",
            data={"start_date": package["start_date"], "end_date": package["end_date"]},
            follow_redirects=True,
        )
        self.assertEqual(booked.status_code, 200)

        own_catalogue = customer_one.get("/packages/").get_data(as_text=True)
        self.assertNotIn(f'href="/packages/{package["id"]}"', own_catalogue)

        customer_two = self.app.test_client()
        self.register_customer(customer_two, "catalogue-two@example.test")
        other_catalogue = customer_two.get("/packages/").get_data(as_text=True)
        self.assertIn(f'href="/packages/{package["id"]}"', other_catalogue)


if __name__ == "__main__":
    unittest.main()
