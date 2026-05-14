from src.repositories.base_repository import BaseRepository


class ClientsRepository(BaseRepository):
    table_name = "clients"
    fields = ("full_name", "phone", "email", "birth_date", "status")


class MembershipsRepository(BaseRepository):
    table_name = "memberships"
    fields = (
        "client_id",
        "type_name",
        "start_date",
        "end_date",
        "visits_left",
        "price",
        "status",
    )

    def list_all(self) -> list[dict]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    m.id,
                    m.client_id,
                    c.full_name AS client_name,
                    m.type_name,
                    m.start_date,
                    m.end_date,
                    m.visits_left,
                    m.price,
                    m.status
                FROM memberships m
                JOIN clients c ON c.id = m.client_id
                ORDER BY m.id DESC
                """
            )
            return cursor.fetchall()


class TrainersRepository(BaseRepository):
    table_name = "trainers"
    fields = ("full_name", "phone", "specialization", "work_schedule", "status")


class WorkoutsRepository(BaseRepository):
    table_name = "workouts"
    fields = ("title", "trainer_id", "starts_at", "capacity", "description")

    def list_all(self) -> list[dict]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    w.id,
                    w.title,
                    w.trainer_id,
                    t.full_name AS trainer_name,
                    w.starts_at,
                    w.capacity,
                    w.description
                FROM workouts w
                JOIN trainers t ON t.id = w.trainer_id
                ORDER BY w.starts_at DESC, w.id DESC
                """
            )
            return cursor.fetchall()

    def list_options(self, value_field: str = "id", label_field: str = "title") -> list[tuple[int, str]]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    w.id,
                    CONCAT(
                        DATE_FORMAT(w.starts_at, '%d.%m.%Y %H:%i'),
                        ' - ',
                        w.title,
                        ' / ',
                        t.full_name
                    )
                FROM workouts w
                JOIN trainers t ON t.id = w.trainer_id
                ORDER BY w.starts_at
                """
            )
            return [(value, str(label)) for value, label in cursor.fetchall()]


class WorkoutRegistrationsRepository(BaseRepository):
    table_name = "workout_registrations"
    fields = ("workout_id", "client_id")

    def list_schedule(self) -> list[dict]:
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
                GROUP BY w.id, w.title, t.full_name, w.starts_at, w.capacity
                ORDER BY w.starts_at DESC, w.id DESC
                """
            )
            return cursor.fetchall()

    def list_registrations(self) -> list[dict]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    wr.id,
                    c.full_name AS client_name,
                    w.title AS workout_title,
                    t.full_name AS trainer_name,
                    w.starts_at,
                    wr.registered_at
                FROM workout_registrations wr
                JOIN clients c ON c.id = wr.client_id
                JOIN workouts w ON w.id = wr.workout_id
                JOIN trainers t ON t.id = w.trainer_id
                ORDER BY wr.registered_at DESC, wr.id DESC
                """
            )
            return cursor.fetchall()


class VisitsRepository(BaseRepository):
    table_name = "visits"
    fields = ("client_id", "membership_id", "visited_at", "note")

    def list_all(self) -> list[dict]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    v.id,
                    v.client_id,
                    c.full_name AS client_name,
                    v.membership_id,
                    m.type_name AS membership_type,
                    v.visited_at,
                    v.note
                FROM visits v
                JOIN clients c ON c.id = v.client_id
                JOIN memberships m ON m.id = v.membership_id
                ORDER BY v.visited_at DESC, v.id DESC
                """
            )
            return cursor.fetchall()


class PaymentsRepository(BaseRepository):
    table_name = "payments"
    fields = ("client_id", "membership_id", "amount", "payment_date", "payment_method")

    def list_all(self) -> list[dict]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.client_id,
                    c.full_name AS client_name,
                    p.membership_id,
                    m.type_name AS membership_type,
                    p.amount,
                    p.payment_date,
                    p.payment_method
                FROM payments p
                JOIN clients c ON c.id = p.client_id
                LEFT JOIN memberships m ON m.id = p.membership_id
                ORDER BY p.payment_date DESC, p.id DESC
                """
            )
            return cursor.fetchall()

    def list_membership_options(self) -> list[tuple[int, str]]:
        with self.db.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    m.id,
                    CONCAT(c.full_name, ' - ', m.type_name, ' до ', DATE_FORMAT(m.end_date, '%d.%m.%Y'))
                FROM memberships m
                JOIN clients c ON c.id = m.client_id
                ORDER BY c.full_name, m.end_date DESC
                """
            )
            return [(value, str(label)) for value, label in cursor.fetchall()]
