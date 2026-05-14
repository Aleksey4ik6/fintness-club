from typing import Any

from mysql.connector import IntegrityError

from src.database.connection import Database


class WorkoutRegistrationError(ValueError):
    pass


class WorkoutService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def register_client(self, workout_id: int, client_id: int) -> dict[str, Any]:
        if workout_id <= 0 or client_id <= 0:
            raise WorkoutRegistrationError("Выберите клиента и тренировку.")

        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    w.id,
                    w.title,
                    w.capacity,
                    COUNT(wr.id) AS registered_count
                FROM workouts w
                LEFT JOIN workout_registrations wr ON wr.workout_id = w.id
                WHERE w.id = %s
                GROUP BY w.id, w.title, w.capacity
                FOR UPDATE
                """,
                (workout_id,),
            )
            workout = cursor.fetchone()
            if not workout:
                raise WorkoutRegistrationError("Тренировка не найдена.")

            if int(workout["registered_count"]) >= int(workout["capacity"]):
                raise WorkoutRegistrationError("В группе нет свободных мест.")

            cursor.execute(
                """
                SELECT id
                FROM memberships
                WHERE client_id = %s
                  AND status = 'active'
                  AND start_date <= CURDATE()
                  AND end_date >= CURDATE()
                  AND visits_left > 0
                LIMIT 1
                """,
                (client_id,),
            )
            if not cursor.fetchone():
                raise WorkoutRegistrationError(
                    "У клиента нет активного абонемента для записи на тренировку."
                )

            try:
                cursor.execute(
                    """
                    INSERT INTO workout_registrations (workout_id, client_id)
                    VALUES (%s, %s)
                    """,
                    (workout_id, client_id),
                )
            except IntegrityError as exc:
                raise WorkoutRegistrationError("Клиент уже записан на эту тренировку.") from exc

            return {
                "workout_title": workout["title"],
                "free_spots": int(workout["capacity"]) - int(workout["registered_count"]) - 1,
            }
