"""SQLite connection helpers, tables, and starter tour data."""
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    """Return one database connection for the current request."""
    if "db" not in g:
        database_path = current_app.config["DATABASE"]
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    """Close the request's database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _add_sample_packages(connection, admin_id):
    """Add a few example trips once, so a new install is not empty."""
    count = connection.execute("SELECT COUNT(*) FROM tour_packages").fetchone()[0]
    if count:
        return

    samples = [
        {
            "title": "Auckland City Highlights",
            "description": "Discover the waterfront, city views, and well-known Auckland sights.",
            "start": "2026-12-01", "end": "2026-12-05", "price": 249.00, "rating": 4.6,
            "image": "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?w=1000&q=80",
            "locations": [
                ("Sky Tower", "Auckland", "Enjoy views across the city.", "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?w=800&q=80"),
                ("Viaduct Harbour", "Auckland", "Walk by the waterfront and restaurants.", "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=800&q=80"),
            ],
        },
        {
            "title": "Rotorua Geothermal Escape",
            "description": "A relaxing trip with geothermal landscapes and local culture.",
            "start": "2027-01-10", "end": "2027-01-14", "price": 319.00, "rating": 4.8,
            "image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1000&q=80",
            "locations": [
                ("Te Puia", "Rotorua", "See geothermal activity and Māori arts and crafts.", "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80"),
                ("Redwoods Forest", "Rotorua", "Walk among tall trees and forest tracks.", "https://images.unsplash.com/photo-1448375240586-882707db888b?w=800&q=80"),
            ],
        },
        {
            "title": "Queenstown Lake Adventure",
            "description": "Take in alpine scenery, lakeside views, and outdoor activities.",
            "start": "2027-02-01", "end": "2027-02-07", "price": 479.00, "rating": 4.9,
            "image": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1000&q=80",
            "locations": [
                ("Lake Wakatipu", "Queenstown", "Enjoy the lake and surrounding mountains.", "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&q=80"),
                ("Queenstown Gardens", "Queenstown", "Explore gardens close to the lake.", "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80"),
            ],
        },
        {
            "title": "Christchurch and Lake Tekapo",
            "description": "Combine garden-city sights with the clear blue waters of Lake Tekapo.",
            "start": "2027-03-02", "end": "2027-03-08", "price": 399.00, "rating": 4.7,
            "image": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1000&q=80",
            "locations": [
                ("Christchurch Botanic Gardens", "Christchurch", "Visit gardens in the centre of Christchurch.", "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80"),
                ("Lake Tekapo", "Lake Tekapo", "See the lake and alpine landscape.", "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=800&q=80"),
            ],
        },
    ]

    for item in samples:
        package_cursor = connection.execute(
            """INSERT INTO tour_packages
               (title, description, start_date, end_date, price, rating, image_url, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item["title"], item["description"], item["start"], item["end"],
             item["price"], item["rating"], item["image"], admin_id),
        )
        package_id = package_cursor.lastrowid
        for position, (name, city, description, image_url) in enumerate(item["locations"], start=1):
            location_cursor = connection.execute(
                "INSERT INTO locations (name, city, description, image_url) VALUES (?, ?, ?, ?)",
                (name, city, description, image_url),
            )
            connection.execute(
                "INSERT INTO package_locations (package_id, location_id, position) VALUES (?, ?, ?)",
                (package_id, location_cursor.lastrowid, position),
            )


def init_db(app):
    """Create tables and add the local admin plus demo packages if needed."""
    database_path = app.config["DATABASE"]
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tour_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            price REAL NOT NULL CHECK (price >= 0),
            rating REAL NOT NULL DEFAULT 0 CHECK (rating >= 0 AND rating <= 5),
            image_url TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            CHECK (end_date >= start_date)
        );
        CREATE TABLE IF NOT EXISTS package_locations (
            package_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            position INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (package_id, location_id),
            FOREIGN KEY (package_id) REFERENCES tour_packages(id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            package_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES tour_packages(id) ON DELETE RESTRICT,
            CHECK (end_date >= start_date)
        );
        CREATE INDEX IF NOT EXISTS idx_packages_active_dates ON tour_packages(is_active, start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id, status);
        """
    )

    from werkzeug.security import generate_password_hash
    admin = connection.execute("SELECT id FROM users WHERE email = ?", ("admin@tour.local",)).fetchone()
    if admin is None:
        cursor = connection.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
            ("Tour Administrator", "admin@tour.local", generate_password_hash("Admin123!")),
        )
        admin_id = cursor.lastrowid
    else:
        admin_id = admin[0]

    _add_sample_packages(connection, admin_id)
    connection.commit()
    connection.close()
    app.teardown_appcontext(close_db)
