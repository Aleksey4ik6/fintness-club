import hashlib
from typing import Any

from src.database.connection import Database


class UsersRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def find_by_credentials(self, username: str, password: str) -> dict[str, Any] | None:
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, username, full_name, role
                FROM users
                WHERE username = %s AND password_hash = %s AND is_active = 1
                """,
                (username, password_hash),
            )
            return cursor.fetchone()
