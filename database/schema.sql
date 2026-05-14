CREATE DATABASE IF NOT EXISTS fitness_club
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fitness_club;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash CHAR(64) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    role ENUM('admin', 'manager', 'trainer') NOT NULL DEFAULT 'manager',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(120),
    birth_date DATE,
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trainers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    specialization VARCHAR(120) NOT NULL,
    work_schedule VARCHAR(120),
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS memberships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    type_name VARCHAR(80) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    visits_left INT NOT NULL DEFAULT 0,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    status ENUM('active', 'expired', 'closed') NOT NULL DEFAULT 'active',
    CONSTRAINT fk_memberships_client
        FOREIGN KEY (client_id) REFERENCES clients(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    membership_id INT NOT NULL,
    visited_at DATETIME NOT NULL,
    note VARCHAR(255),
    CONSTRAINT fk_visits_client
        FOREIGN KEY (client_id) REFERENCES clients(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_visits_membership
        FOREIGN KEY (membership_id) REFERENCES memberships(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(120) NOT NULL,
    trainer_id INT NOT NULL,
    starts_at DATETIME NOT NULL,
    capacity INT NOT NULL DEFAULT 10,
    description VARCHAR(255),
    CONSTRAINT fk_workouts_trainer
        FOREIGN KEY (trainer_id) REFERENCES trainers(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workout_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workout_id INT NOT NULL,
    client_id INT NOT NULL,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_workout_client (workout_id, client_id),
    CONSTRAINT fk_registrations_workout
        FOREIGN KEY (workout_id) REFERENCES workouts(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_registrations_client
        FOREIGN KEY (client_id) REFERENCES clients(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    membership_id INT,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method ENUM('cash', 'card', 'transfer') NOT NULL DEFAULT 'card',
    CONSTRAINT fk_payments_client
        FOREIGN KEY (client_id) REFERENCES clients(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_payments_membership
        FOREIGN KEY (membership_id) REFERENCES memberships(id)
        ON DELETE SET NULL
);

INSERT INTO users (username, password_hash, full_name, role)
VALUES (
    'admin',
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    'Администратор',
    'admin'
)
ON DUPLICATE KEY UPDATE username = username;

INSERT INTO clients (full_name, phone, email, birth_date, status)
SELECT 'Иванов Артем Сергеевич', '+7 913 100-10-10', 'ivanov@example.com', '1998-04-12', 'active'
WHERE NOT EXISTS (SELECT 1 FROM clients WHERE phone = '+7 913 100-10-10');

INSERT INTO clients (full_name, phone, email, birth_date, status)
SELECT 'Петрова Мария Андреевна', '+7 913 200-20-20', 'petrova@example.com', '2001-08-25', 'active'
WHERE NOT EXISTS (SELECT 1 FROM clients WHERE phone = '+7 913 200-20-20');

INSERT INTO trainers (full_name, phone, specialization, work_schedule, status)
SELECT 'Смирнов Денис Павлович', '+7 913 300-30-30', 'Силовые тренировки', 'Пн-Пт 09:00-18:00', 'active'
WHERE NOT EXISTS (SELECT 1 FROM trainers WHERE phone = '+7 913 300-30-30');

INSERT INTO trainers (full_name, phone, specialization, work_schedule, status)
SELECT 'Кузнецова Анна Игоревна', '+7 913 400-40-40', 'Йога и растяжка', 'Вт-Сб 12:00-20:00', 'active'
WHERE NOT EXISTS (SELECT 1 FROM trainers WHERE phone = '+7 913 400-40-40');

INSERT INTO memberships (client_id, type_name, start_date, end_date, visits_left, price, status)
SELECT c.id, 'Месячный', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 12, 3500.00, 'active'
FROM clients c
WHERE c.phone = '+7 913 100-10-10'
  AND NOT EXISTS (SELECT 1 FROM memberships m WHERE m.client_id = c.id AND m.type_name = 'Месячный');

INSERT INTO memberships (client_id, type_name, start_date, end_date, visits_left, price, status)
SELECT c.id, 'Безлимит', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 30, 5200.00, 'active'
FROM clients c
WHERE c.phone = '+7 913 200-20-20'
  AND NOT EXISTS (SELECT 1 FROM memberships m WHERE m.client_id = c.id AND m.type_name = 'Безлимит');

INSERT INTO workouts (title, trainer_id, starts_at, capacity, description)
SELECT 'Функциональная тренировка', t.id, DATE_ADD(NOW(), INTERVAL 1 DAY), 12, 'Групповая силовая тренировка'
FROM trainers t
WHERE t.phone = '+7 913 300-30-30'
  AND NOT EXISTS (SELECT 1 FROM workouts w WHERE w.title = 'Функциональная тренировка');

INSERT INTO workouts (title, trainer_id, starts_at, capacity, description)
SELECT 'Йога Stretch', t.id, DATE_ADD(NOW(), INTERVAL 2 DAY), 15, 'Растяжка и восстановление'
FROM trainers t
WHERE t.phone = '+7 913 400-40-40'
  AND NOT EXISTS (SELECT 1 FROM workouts w WHERE w.title = 'Йога Stretch');

INSERT INTO payments (client_id, membership_id, amount, payment_date, payment_method)
SELECT c.id, m.id, m.price, CURDATE(), 'card'
FROM clients c
JOIN memberships m ON m.client_id = c.id
WHERE c.phone = '+7 913 100-10-10'
  AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.membership_id = m.id);

INSERT INTO payments (client_id, membership_id, amount, payment_date, payment_method)
SELECT c.id, m.id, m.price, CURDATE(), 'cash'
FROM clients c
JOIN memberships m ON m.client_id = c.id
WHERE c.phone = '+7 913 200-20-20'
  AND NOT EXISTS (SELECT 1 FROM payments p WHERE p.membership_id = m.id);

CREATE OR REPLACE VIEW report_active_memberships AS
SELECT
    m.id,
    c.full_name AS client_name,
    m.type_name,
    m.end_date,
    m.visits_left,
    m.status
FROM memberships m
JOIN clients c ON c.id = m.client_id
WHERE m.status = 'active';

CREATE OR REPLACE VIEW report_month_revenue AS
SELECT
    DATE_FORMAT(payment_date, '%Y-%m') AS month_key,
    COUNT(*) AS payments_count,
    SUM(amount) AS total_amount
FROM payments
GROUP BY DATE_FORMAT(payment_date, '%Y-%m');
