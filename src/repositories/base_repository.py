from typing import Any

from src.database.connection import Database


class BaseRepository:
    table_name = ""
    fields: tuple[str, ...] = ()

    def __init__(self, db: Database) -> None:
        self.db = db

    def list_all(self) -> list[dict[str, Any]]:
        field_list = ", ".join(("id", *self.fields))
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT {field_list} FROM {self.table_name} ORDER BY id DESC")
            return cursor.fetchall()

    def list_options(self, value_field: str = "id", label_field: str = "full_name") -> list[tuple[Any, str]]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT {value_field}, {label_field} FROM {self.table_name} ORDER BY {label_field}"
            )
            return [(value, str(label)) for value, label in cursor.fetchall()]

    def create(self, payload: dict[str, Any]) -> int:
        allowed = {key: value for key, value in payload.items() if key in self.fields}
        columns = ", ".join(allowed)
        placeholders = ", ".join(["%s"] * len(allowed))
        values = tuple(allowed.values())
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                values,
            )
            return cursor.lastrowid

    def update(self, item_id: int, payload: dict[str, Any]) -> None:
        allowed = {key: value for key, value in payload.items() if key in self.fields}
        assignments = ", ".join([f"{column} = %s" for column in allowed])
        values = tuple(allowed.values()) + (item_id,)
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET {assignments} WHERE id = %s",
                values,
            )

    def delete(self, item_id: int) -> None:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = %s", (item_id,))
