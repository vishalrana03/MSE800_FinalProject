"""SQLite database helpers for the Tour Package application."""
import os
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    """Return a request-scoped database connection."""
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
    """Create the initial schema and insert a local development admin."""
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    connection = sqlite3.connect(app.config["DATABASE"])
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
        """
    )
    connection.commit()
    connection.close()
    app.teardown_appcontext(close_db)

    # A local-only starter account so the admin area can be tested.
    # Change this password before using the project beyond local development.
    from werkzeug.security import generate_password_hash

    connection = sqlite3.connect(app.config["DATABASE"])
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
