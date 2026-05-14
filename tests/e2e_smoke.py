import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.connection import Database
from src.repositories.catalogs import (
    ClientsRepository,
    MembershipsRepository,
    PaymentsRepository,
    TrainersRepository,
    WorkoutsRepository,
)
from src.repositories.reports import ReportsRepository
from src.services.visit_service import VisitService
from src.services.workout_service import WorkoutService


created_client_id: int | None = None
created_workout_id: int | None = None


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def cleanup(db: Database) -> None:
    if created_workout_id is None and created_client_id is None:
        return
    with db.connect() as connection:
        cursor = connection.cursor()
        if created_workout_id is not None:
            cursor.execute("DELETE FROM workouts WHERE id = %s", (created_workout_id,))
        if created_client_id is not None:
            cursor.execute("DELETE FROM clients WHERE id = %s", (created_client_id,))


def main() -> None:
    global created_client_id, created_workout_id

    db = Database()
    suffix = datetime.now().strftime("%Y%m%d%H%M%S")

    clients = ClientsRepository(db)
    memberships = MembershipsRepository(db)
    payments = PaymentsRepository(db)
    trainers = TrainersRepository(db)
    workouts = WorkoutsRepository(db)
    reports = ReportsRepository(db)
    visit_service = VisitService(db)
    workout_service = WorkoutService(db)

    try:
        client_id = clients.create(
            {
                "full_name": f"Тестовый Клиент {suffix}",
                "phone": f"+7 999 {suffix[-3:]}-{suffix[-5:-3]}-{suffix[-7:-5]}",
                "email": f"client{suffix}@example.com",
                "birth_date": "1999-01-01",
                "status": "active",
            }
        )
        created_client_id = client_id
        assert_true(client_id > 0, "Клиент не создан")

        membership_id = memberships.create(
            {
                "client_id": client_id,
                "type_name": "Тестовый месячный",
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
                "visits_left": 5,
                "price": 3900,
                "status": "active",
            }
        )
        assert_true(membership_id > 0, "Абонемент не создан")

        payment_id = payments.create(
            {
                "client_id": client_id,
                "membership_id": membership_id,
                "amount": 3900,
                "payment_date": date.today().isoformat(),
                "payment_method": "card",
            }
        )
        assert_true(payment_id > 0, "Оплата не создана")

        visit_result = visit_service.register_visit(client_id, "E2E проверка посещения")
        assert_true(
            visit_result["membership_id"] == membership_id,
            "Посещение списалось не с созданного абонемента",
        )
        assert_true(visit_result["visits_left"] == 4, "Посещение не списало остаток абонемента")

        trainer_options = TrainersRepository(db).list_options()
        if trainer_options:
            trainer_id = trainer_options[0][0]
        else:
            trainer_id = trainers.create(
                {
                    "full_name": "Тестовый Тренер",
                    "phone": f"+7 999 000-{suffix[-4:]}",
                    "specialization": "Функциональный тренинг",
                    "work_schedule": "Пн-Пт",
                    "status": "active",
                }
            )

        workout_id = workouts.create(
            {
                "title": f"E2E тренировка {suffix}",
                "trainer_id": trainer_id,
                "starts_at": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "capacity": 3,
                "description": "Тренировка для проверки полного сценария",
            }
        )
        created_workout_id = workout_id
        assert_true(workout_id > 0, "Тренировка не создана")

        registration_result = workout_service.register_client(workout_id, client_id)
        assert_true(
            registration_result["workout_title"] == f"E2E тренировка {suffix}",
            "Клиент не записался на созданную тренировку",
        )
        assert_true(registration_result["free_spots"] == 2, "Неверно рассчитаны свободные места")

        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=2)).isoformat()
        summary = reports.period_summary(start_date, end_date)
        revenue_rows = reports.revenue_by_period(start_date, end_date)
        visit_rows = reports.visits_by_period(start_date, end_date)
        workout_rows = reports.workout_registrations_by_period(start_date, end_date)

        assert_true(summary["visits_count"] >= 1, "Отчет не видит посещение")
        assert_true(summary["payments_count"] >= 1, "Отчет не видит оплату")
        assert_true(summary["revenue"] >= 3900, "Отчет не видит выручку")
        assert_true(summary["workout_registrations_count"] >= 1, "Отчет не видит запись на тренировку")
        assert_true(any(row["client_name"].startswith("Тестовый Клиент") for row in revenue_rows), "Выручка не попала в детализацию")
        assert_true(any(row["client_name"].startswith("Тестовый Клиент") for row in visit_rows), "Посещение не попало в детализацию")
        assert_true(any(row["client_name"].startswith("Тестовый Клиент") for row in workout_rows), "Запись не попала в детализацию")

        print("E2E smoke scenario passed")
        print(f"client_id={client_id}")
        print(f"membership_id={membership_id}")
        print(f"payment_id={payment_id}")
        print(f"workout_id={workout_id}")
        print(f"period_summary={summary}")
    finally:
        cleanup(db)
        print("E2E temporary records cleaned")


if __name__ == "__main__":
    main()
