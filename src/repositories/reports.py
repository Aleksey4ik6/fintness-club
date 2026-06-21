from typing import Any

from src.database.connection import Database


class ReportsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def summary(self) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM clients WHERE status = 'active') AS active_clients,
                    (SELECT COUNT(*) FROM memberships WHERE status = 'active') AS active_memberships,
                    (SELECT COUNT(*) FROM visits WHERE DATE(visited_at) = CURDATE()) AS visits_today,
                    (SELECT COALESCE(SUM(amount), 0)
                     FROM payments
                     WHERE YEAR(payment_date) = YEAR(CURDATE())
                       AND MONTH(payment_date) = MONTH(CURDATE())) AS month_revenue
                """
            )
            return cursor.fetchone()

    def expiring_memberships(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    m.id,
                    c.full_name AS client_name,
                    m.type_name,
                    m.end_date,
                    m.visits_left
                FROM memberships m
                JOIN clients c ON c.id = m.client_id
                WHERE m.status = 'active'
                  AND (m.end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) OR m.visits_left <= 2)
                ORDER BY m.end_date ASC, m.visits_left ASC
                LIMIT 20
                """
            )
            return cursor.fetchall()

    def visit_activity(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT DATE(visited_at) AS visit_date, COUNT(*) AS visits_count
                FROM visits
                WHERE visited_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                GROUP BY DATE(visited_at)
                ORDER BY visit_date DESC
                """
            )
            return cursor.fetchall()

    def revenue_by_period(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    p.payment_date,
                    c.full_name AS client_name,
                    COALESCE(m.type_name, 'Без абонемента') AS membership_type,
                    p.amount,
                    p.payment_method
                FROM payments p
                JOIN clients c ON c.id = p.client_id
                LEFT JOIN memberships m ON m.id = p.membership_id
                WHERE p.payment_date BETWEEN %s AND %s
                ORDER BY p.payment_date DESC, p.id DESC
                """,
                (start_date, end_date),
            )
            return cursor.fetchall()

    def visits_by_period(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    DATE(v.visited_at) AS visit_date,
                    TIME(v.visited_at) AS visit_time,
                    c.full_name AS client_name,
                    m.type_name AS membership_type,
                    v.note
                FROM visits v
                JOIN clients c ON c.id = v.client_id
                JOIN memberships m ON m.id = v.membership_id
                WHERE DATE(v.visited_at) BETWEEN %s AND %s
                ORDER BY v.visited_at DESC, v.id DESC
                """,
                (start_date, end_date),
            )
            return cursor.fetchall()

    def workout_registrations_by_period(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    DATE(w.starts_at) AS workout_date,
                    TIME(w.starts_at) AS workout_time,
                    w.title AS workout_title,
                    t.full_name AS trainer_name,
                    c.full_name AS client_name,
                    wr.registered_at
                FROM workout_registrations wr
                JOIN workouts w ON w.id = wr.workout_id
                JOIN trainers t ON t.id = w.trainer_id
                JOIN clients c ON c.id = wr.client_id
                WHERE DATE(w.starts_at) BETWEEN %s AND %s
                ORDER BY w.starts_at DESC, wr.registered_at DESC
                """,
                (start_date, end_date),
            )
            return cursor.fetchall()

    def membership_statuses(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    m.status,
                    COUNT(*) AS memberships_count,
                    SUM(m.price) AS total_price
                FROM memberships m
                GROUP BY m.status
                ORDER BY memberships_count DESC
                """
            )
            return cursor.fetchall()

    def period_summary(self, start_date: str, end_date: str) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM visits WHERE DATE(visited_at) BETWEEN %s AND %s) AS visits_count,
                    (SELECT COUNT(*) FROM payments WHERE payment_date BETWEEN %s AND %s) AS payments_count,
                    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_date BETWEEN %s AND %s) AS revenue,
                    (SELECT COUNT(*) FROM workout_registrations wr
                     JOIN workouts w ON w.id = wr.workout_id
                     WHERE DATE(w.starts_at) BETWEEN %s AND %s) AS workout_registrations_count
                """,
                (
                    start_date,
                    end_date,
                    start_date,
                    end_date,
                    start_date,
                    end_date,
                    start_date,
                    end_date,
                ),
            )
            return cursor.fetchone()

    def management_summary(self) -> dict[str, Any]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM clients WHERE status = 'active') AS active_clients,
                    (SELECT COUNT(*) FROM memberships WHERE status = 'active') AS active_memberships,
                    (SELECT COUNT(*) FROM memberships
                     WHERE status = 'active'
                       AND (end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) OR visits_left <= 2)) AS memberships_attention,
                    (SELECT COUNT(*) FROM visits WHERE DATE(visited_at) = CURDATE()) AS visits_today,
                    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE payment_date = CURDATE()) AS revenue_today,
                    (SELECT COALESCE(SUM(amount), 0)
                     FROM payments
                     WHERE YEAR(payment_date) = YEAR(CURDATE())
                       AND MONTH(payment_date) = MONTH(CURDATE())) AS revenue_month,
                    (SELECT COUNT(*) FROM workouts WHERE DATE(starts_at) = CURDATE()) AS workouts_today,
                    (SELECT COUNT(*) FROM workout_registrations wr
                     JOIN workouts w ON w.id = wr.workout_id
                     WHERE DATE(w.starts_at) = CURDATE()) AS registrations_today
                """
            )
            return cursor.fetchone()

    def membership_alerts(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    c.full_name AS client_name,
                    c.phone,
                    m.type_name,
                    m.end_date,
                    m.visits_left,
                    CASE
                        WHEN m.end_date < CURDATE() THEN 'Просрочен'
                        WHEN m.visits_left = 0 THEN 'Нет посещений'
                        WHEN m.end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 'Скоро закончится'
                        WHEN m.visits_left <= 2 THEN 'Мало посещений'
                        ELSE 'Контроль'
                    END AS reason
                FROM memberships m
                JOIN clients c ON c.id = m.client_id
                WHERE m.status = 'active'
                  AND (m.end_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) OR m.visits_left <= 2)
                ORDER BY m.end_date ASC, m.visits_left ASC
                LIMIT 30
                """
            )
            return cursor.fetchall()

    def workout_occupancy(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    w.title,
                    t.full_name AS trainer_name,
                    w.starts_at,
                    w.capacity,
                    COUNT(wr.id) AS registered_count,
                    ROUND(COUNT(wr.id) / w.capacity * 100, 1) AS occupancy_percent
                FROM workouts w
                JOIN trainers t ON t.id = w.trainer_id
                LEFT JOIN workout_registrations wr ON wr.workout_id = w.id
                WHERE w.starts_at >= CURDATE()
                GROUP BY w.id, w.title, t.full_name, w.starts_at, w.capacity
                ORDER BY w.starts_at ASC
                LIMIT 30
                """
            )
            return cursor.fetchall()

    def payment_structure_current_month(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    payment_method,
                    COUNT(*) AS payments_count,
                    COALESCE(SUM(amount), 0) AS total_amount
                FROM payments
                WHERE YEAR(payment_date) = YEAR(CURDATE())
                  AND MONTH(payment_date) = MONTH(CURDATE())
                GROUP BY payment_method
                ORDER BY total_amount DESC
                """
            )
            return cursor.fetchall()
