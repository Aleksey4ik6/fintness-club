from datetime import date, datetime, timedelta
from decimal import Decimal

import mysql.connector

from src.config import DatabaseConfig


CLIENTS = [
    ("Иванов Артем Сергеевич", "+7 913 100-10-10", "ivanov@example.com", "1998-04-12"),
    ("Петрова Мария Андреевна", "+7 913 200-20-20", "petrova@example.com", "2001-08-25"),
    ("Соколов Дмитрий Олегович", "+7 913 101-11-11", "sokolov@example.com", "1995-02-19"),
    ("Васильева Алина Максимовна", "+7 913 102-12-12", "vasileva@example.com", "1999-11-03"),
    ("Морозов Кирилл Игоревич", "+7 913 103-13-13", "morozov@example.com", "1992-07-14"),
    ("Новикова Екатерина Павловна", "+7 913 104-14-14", "novikova@example.com", "2000-05-30"),
    ("Федоров Никита Романович", "+7 913 105-15-15", "fedorov@example.com", "1997-12-09"),
    ("Козлова Дарья Денисовна", "+7 913 106-16-16", "kozlova@example.com", "1996-09-21"),
    ("Лебедев Михаил Артемович", "+7 913 107-17-17", "lebedev@example.com", "1994-03-08"),
    ("Семенова Полина Ильинична", "+7 913 108-18-18", "semenova@example.com", "2002-01-17"),
    ("Егоров Владислав Антонович", "+7 913 109-19-19", "egorov@example.com", "1991-06-27"),
    ("Павлова Софья Матвеевна", "+7 913 110-20-20", "pavlova@example.com", "1998-10-06"),
    ("Александров Глеб Тимурович", "+7 913 111-21-21", "alexandrov@example.com", "1993-04-01"),
    ("Макарова Вероника Сергеевна", "+7 913 112-22-22", "makarova@example.com", "2001-02-22"),
    ("Орлов Илья Константинович", "+7 913 113-23-23", "orlov@example.com", "1990-08-13"),
    ("Зайцева Ксения Андреевна", "+7 913 114-24-24", "zaytseva@example.com", "1999-07-07"),
    ("Степанов Руслан Викторович", "+7 913 115-25-25", "stepanov@example.com", "1989-12-18"),
    ("Григорьева Милана Олеговна", "+7 913 116-26-26", "grigorieva@example.com", "2003-05-11"),
    ("Николаев Егор Александрович", "+7 913 117-27-27", "nikolaev@example.com", "1996-01-29"),
    ("Волкова Анна Дмитриевна", "+7 913 118-28-28", "volkova@example.com", "1997-09-05"),
    ("Киселев Павел Евгеньевич", "+7 913 119-29-29", "kiselev@example.com", "1992-10-16"),
    ("Тихонова Елена Игоревна", "+7 913 120-30-30", "tihonova@example.com", "1995-06-04"),
    ("Белов Данил Андреевич", "+7 913 121-31-31", "belov@example.com", "2000-03-24"),
    ("Комарова Юлия Романовна", "+7 913 122-32-32", "komarova@example.com", "1994-11-28"),
    ("Михайлов Станислав Денисович", "+7 913 123-33-33", "mihaylov@example.com", "1988-04-20"),
    ("Романова Виктория Павловна", "+7 913 124-34-34", "romanova@example.com", "2002-08-31"),
]

TRAINERS = [
    ("Смирнов Денис Павлович", "+7 913 300-30-30", "Силовые тренировки", "Пн-Пт 09:00-18:00"),
    ("Кузнецова Анна Игоревна", "+7 913 400-40-40", "Йога и растяжка", "Вт-Сб 12:00-20:00"),
    ("Андреев Максим Юрьевич", "+7 913 301-31-31", "Функциональный тренинг", "Пн-Ср-Пт 08:00-16:00"),
    ("Сергеева Ольга Валерьевна", "+7 913 302-32-32", "Пилатес", "Пн-Пт 11:00-19:00"),
    ("Крылов Роман Ильич", "+7 913 303-33-33", "Бокс", "Вт-Чт-Сб 15:00-21:00"),
    ("Данилова Ирина Олеговна", "+7 913 304-34-34", "Кардио", "Пн-Пт 07:00-15:00"),
    ("Борисов Андрей Петрович", "+7 913 305-35-35", "Тренажерный зал", "Пн-Сб 10:00-18:00"),
    ("Лазарева Нина Сергеевна", "+7 913 306-36-36", "Здоровая спина", "Ср-Вс 12:00-20:00"),
]

MEMBERSHIP_TYPES = [
    ("Разовый", 1, Decimal("600.00"), 7),
    ("Месячный", 12, Decimal("3500.00"), 30),
    ("Безлимит", 30, Decimal("5200.00"), 30),
    ("Квартальный", 48, Decimal("12500.00"), 90),
]

WORKOUT_TITLES = [
    "Функциональная тренировка",
    "Йога Stretch",
    "Силовой круг",
    "Пилатес Start",
    "Кардио-интенсив",
    "Бокс Fitness",
    "Здоровая спина",
    "TRX Total Body",
    "Утренняя зарядка",
    "Core Training",
]


def connect():
    config = DatabaseConfig()
    return mysql.connector.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        connection_timeout=config.connection_timeout,
        autocommit=False,
    )


def fetch_one(cursor, query, params):
    cursor.execute(query, params)
    return cursor.fetchone()


def ensure_client(cursor, client):
    full_name, phone, email, birth_date = client
    row = fetch_one(cursor, "SELECT id FROM clients WHERE phone = %s", (phone,))
    if row:
        return row[0]
    cursor.execute(
        """
        INSERT INTO clients (full_name, phone, email, birth_date, status)
        VALUES (%s, %s, %s, %s, 'active')
        """,
        (full_name, phone, email, birth_date),
    )
    return cursor.lastrowid


def ensure_trainer(cursor, trainer):
    full_name, phone, specialization, work_schedule = trainer
    row = fetch_one(cursor, "SELECT id FROM trainers WHERE phone = %s", (phone,))
    if row:
        return row[0]
    cursor.execute(
        """
        INSERT INTO trainers (full_name, phone, specialization, work_schedule, status)
        VALUES (%s, %s, %s, %s, 'active')
        """,
        (full_name, phone, specialization, work_schedule),
    )
    return cursor.lastrowid


def ensure_membership(cursor, client_id, index):
    cursor.execute(
        "SELECT id FROM memberships WHERE client_id = %s AND status = 'active' LIMIT 1",
        (client_id,),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    type_name, visits, price, days = MEMBERSHIP_TYPES[index % len(MEMBERSHIP_TYPES)]
    start_date = date.today() - timedelta(days=index % 10)
    end_date = start_date + timedelta(days=days)
    visits_left = max(1, visits - (index % 5))
    cursor.execute(
        """
        INSERT INTO memberships (client_id, type_name, start_date, end_date, visits_left, price, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'active')
        """,
        (client_id, type_name, start_date, end_date, visits_left, price),
    )
    return cursor.lastrowid


def ensure_payment(cursor, client_id, membership_id, amount, index):
    cursor.execute("SELECT id FROM payments WHERE membership_id = %s LIMIT 1", (membership_id,))
    if cursor.fetchone():
        return
    method = ["card", "cash", "transfer"][index % 3]
    payment_date = date.today() - timedelta(days=index % 18)
    cursor.execute(
        """
        INSERT INTO payments (client_id, membership_id, amount, payment_date, payment_method)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (client_id, membership_id, amount, payment_date, method),
    )


def seed_workouts(cursor, trainer_ids):
    cursor.execute("SELECT COUNT(*) FROM workouts WHERE description LIKE 'Демо:%'")
    if cursor.fetchone()[0] >= 20:
        return

    for index in range(24):
        title = WORKOUT_TITLES[index % len(WORKOUT_TITLES)]
        trainer_id = trainer_ids[index % len(trainer_ids)]
        starts_at = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(
            days=index // 3,
            hours=9 + (index % 3) * 3,
        )
        capacity = 8 + (index % 5) * 2
        description = f"Демо: {title}, плановое групповое занятие"
        cursor.execute(
            """
            INSERT INTO workouts (title, trainer_id, starts_at, capacity, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title, trainer_id, starts_at, capacity, description),
        )


def seed_workout_registrations(cursor, client_ids):
    cursor.execute("SELECT COUNT(*) FROM workout_registrations")
    if cursor.fetchone()[0] >= 40:
        return

    cursor.execute("SELECT id, capacity FROM workouts ORDER BY starts_at LIMIT 18")
    workouts = cursor.fetchall()
    created = 0
    for workout_index, (workout_id, capacity) in enumerate(workouts):
        places_to_fill = min(int(capacity) - 1, 2 + workout_index % 4)
        for offset in range(places_to_fill):
            client_id = client_ids[(workout_index + offset) % len(client_ids)]
            cursor.execute(
                """
                SELECT 1
                FROM workout_registrations
                WHERE workout_id = %s AND client_id = %s
                """,
                (workout_id, client_id),
            )
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO workout_registrations (workout_id, client_id)
                VALUES (%s, %s)
                """,
                (workout_id, client_id),
            )
            created += 1
    print(f"Workout registrations inserted: {created}")


def seed_visits(cursor, client_memberships):
    cursor.execute("SELECT COUNT(*) FROM visits WHERE note LIKE 'Демо-посещение%'")
    if cursor.fetchone()[0] >= 60:
        return 0

    created = 0
    for index, (client_id, membership_id) in enumerate(client_memberships):
        visits_for_client = 2 + (index % 3)
        for visit_number in range(visits_for_client):
            visited_at = datetime.now().replace(second=0, microsecond=0) - timedelta(
                days=(index + visit_number) % 21,
                hours=visit_number + 1,
            )
            note = f"Демо-посещение {index + 1}-{visit_number + 1}"
            cursor.execute(
                """
                INSERT INTO visits (client_id, membership_id, visited_at, note)
                VALUES (%s, %s, %s, %s)
                """,
                (client_id, membership_id, visited_at, note),
            )
            created += 1
    print(f"Demo visits inserted: {created}")
    return created


def sync_membership_balances(cursor):
    cursor.execute(
        """
        SELECT membership_id, COUNT(*)
        FROM visits
        WHERE note LIKE 'Демо-посещение%'
        GROUP BY membership_id
        """
    )
    visit_counts = cursor.fetchall()
    for membership_id, visits_count in visit_counts:
        cursor.execute(
            """
            UPDATE memberships
            SET
                visits_left = GREATEST(0, visits_left - %s),
                status = IF(GREATEST(0, visits_left - %s) = 0, 'closed', status)
            WHERE id = %s
              AND status = 'active'
            """,
            (visits_count, visits_count, membership_id),
        )


def main() -> None:
    connection = connect()
    try:
        cursor = connection.cursor()

        client_ids = [ensure_client(cursor, client) for client in CLIENTS]
        trainer_ids = [ensure_trainer(cursor, trainer) for trainer in TRAINERS]

        client_memberships = []
        for index, client_id in enumerate(client_ids):
            membership_id = ensure_membership(cursor, client_id, index)
            cursor.execute("SELECT price FROM memberships WHERE id = %s", (membership_id,))
            amount = cursor.fetchone()[0]
            ensure_payment(cursor, client_id, membership_id, amount, index)
            client_memberships.append((client_id, membership_id))

        seed_workouts(cursor, trainer_ids)
        seed_workout_registrations(cursor, client_ids)
        created_visits = seed_visits(cursor, client_memberships)
        if created_visits:
            sync_membership_balances(cursor)

        connection.commit()
        print("Demo data seeded")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
