from typing import Any

from src.database.connection import Database


class ClientPortalRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def find_client_by_phone(self, phone: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, full_name, phone, email, birth_date, status
                FROM clients
                WHERE REPLACE(phone, ' ', '') = REPLACE(%s, ' ', '')
                LIMIT 1
                """,
                (phone.strip(),),
            )
            return cursor.fetchone()

    def active_membership(self, client_id: int) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, type_name, start_date, end_date, visits_left, price, status
                FROM memberships
                WHERE client_id = %s
                  AND status = 'active'
                ORDER BY end_date DESC
                LIMIT 1
                """,
                (client_id,),
            )
            return cursor.fetchone()

    def visits(self, client_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT v.visited_at, m.type_name, v.note
                FROM visits v
                JOIN memberships m ON m.id = v.membership_id
                WHERE v.client_id = %s
                ORDER BY v.visited_at DESC
                LIMIT %s
                """,
                (client_id, limit),
            )
            return cursor.fetchall()

    def available_workouts(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    w.id,
                    w.title,
                    t.full_name AS trainer_name,
                    w.starts_at,
                    w.capacity,
                    COUNT(wr.id) AS registered_count,
                    w.capacity - COUNT(wr.id) AS free_spots
                FROM workouts w
                JOIN trainers t ON t.id = w.trainer_id
                LEFT JOIN workout_registrations wr ON wr.workout_id = w.id
                WHERE w.starts_at >= NOW()
                GROUP BY w.id, w.title, t.full_name, w.starts_at, w.capacity
                ORDER BY w.starts_at ASC
                LIMIT 30
                """
            )
            return cursor.fetchall()

    def client_registrations(self, client_id: int) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    w.title,
                    t.full_name AS trainer_name,
                    w.starts_at,
                    wr.registered_at
                FROM workout_registrations wr
                JOIN workouts w ON w.id = wr.workout_id
                JOIN trainers t ON t.id = w.trainer_id
                WHERE wr.client_id = %s
                ORDER BY w.starts_at DESC
                LIMIT 20
                """
                ,
                (client_id,),
            )
            return cursor.fetchall()
