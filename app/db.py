"""SQLite helpers and initial schema for the Tour Package application."""
import os
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    """Return a request-scoped SQLite connection."""
    if "db" not in g:
        database_path = current_app.config["DATABASE"]
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create the tables required by authentication, packages, and bookings."""
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
            role TEXT NOT NULL DEFAULT 'customer'
                CHECK (role IN ('customer', 'admin')),
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
            status TEXT NOT NULL DEFAULT 'booked'
                CHECK (status IN ('booked', 'cancelled')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES tour_packages(id) ON DELETE RESTRICT,
            CHECK (end_date >= start_date)
        );

        CREATE INDEX IF NOT EXISTS idx_packages_active_dates
            ON tour_packages(is_active, start_date, end_date);
        CREATE INDEX IF NOT EXISTS idx_bookings_user_status
            ON bookings(user_id, status);
        """
    )
    connection.commit()

    # Preserve the local development admin from Task 1 if it already exists.
    from werkzeug.security import generate_password_hash
    existing = connection.execute(
        "SELECT id FROM users WHERE email = ?", ("admin@tour.local",)
    ).fetchone()
    if existing is None:
        connection.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (
                "Tour Administrator",
                "admin@tour.local",
                generate_password_hash("Admin123!"),
                "admin",
            ),
        )
        connection.commit()
    connection.close()
    app.teardown_appcontext(close_db)
