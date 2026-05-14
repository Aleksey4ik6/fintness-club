from typing import Any

from src.database.connection import Database


class VisitRegistrationError(ValueError):
    pass


class VisitService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def register_visit(self, client_id: int, note: str = "") -> dict[str, Any]:
        if client_id <= 0:
            raise VisitRegistrationError("Укажите корректный ID клиента.")

        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, type_name, visits_left, end_date
                FROM memberships
                WHERE client_id = %s
                  AND status = 'active'
                  AND start_date <= CURDATE()
                  AND end_date >= CURDATE()
                  AND visits_left > 0
                ORDER BY end_date ASC, id ASC
                LIMIT 1
                FOR UPDATE
                """,
                (client_id,),
            )
            membership = cursor.fetchone()

            if not membership:
                raise VisitRegistrationError(
                    "У клиента нет активного абонемента с доступными посещениями."
                )

            next_visits_left = int(membership["visits_left"]) - 1
            next_status = "closed" if next_visits_left == 0 else "active"

            cursor.execute(
                """
                INSERT INTO visits (client_id, membership_id, visited_at, note)
                VALUES (%s, %s, NOW(), %s)
                """,
                (client_id, membership["id"], note.strip() or "Автоматическая регистрация"),
            )
            visit_id = cursor.lastrowid

            cursor.execute(
                """
                UPDATE memberships
                SET visits_left = %s, status = %s
                WHERE id = %s
                """,
                (next_visits_left, next_status, membership["id"]),
            )

            return {
                "visit_id": visit_id,
                "membership_id": membership["id"],
                "membership_type": membership["type_name"],
                "visits_left": next_visits_left,
                "membership_status": next_status,
            }
