"""Object-oriented user model."""
from dataclasses import dataclass
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db


@dataclass
class User:
    id: int
    full_name: str
    email: str
    role: str

    @classmethod
    def from_row(cls, row) -> Optional["User"]:
        if row is None:
            return None
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            role=row["role"],
        )

    @classmethod
    def find_by_id(cls, user_id: int) -> Optional["User"]:
        row = get_db().execute(
            "SELECT id, full_name, email, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return cls.from_row(row)

    @classmethod
    def find_by_email(cls, email: str):
        return get_db().execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
        ).fetchone()

    @classmethod
    def create_customer(cls, full_name: str, email: str, password: str) -> "User":
        db = get_db()
        cursor = db.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, 'customer')",
            (full_name.strip(), email.strip().lower(), generate_password_hash(password)),
        )
        db.commit()
        return cls.find_by_id(cursor.lastrowid)

    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional["User"]:
        row = cls.find_by_email(email)
        if row is None or not check_password_hash(row["password_hash"], password):
            return None
        return cls.from_row(row)
