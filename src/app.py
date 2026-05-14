import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.config import APP_NAME
from src.database.connection import Database
from src.repositories.catalogs import (
    ClientsRepository,
    MembershipsRepository,
    PaymentsRepository,
    TrainersRepository,
    VisitsRepository,
    WorkoutRegistrationsRepository,
    WorkoutsRepository,
)
from src.repositories.reports import ReportsRepository
from src.repositories.users import UsersRepository
from src.services.auth_service import AuthService
from src.services.visit_service import VisitService
from src.services.workout_service import WorkoutService
from src.ui.login_window import LoginWindow
from src.ui.main_window import MainWindow
from src.ui.theme import APP_STYLESHEET


def build_repositories(db: Database) -> dict:
    return {
        "clients": ClientsRepository(db),
        "memberships": MembershipsRepository(db),
        "trainers": TrainersRepository(db),
        "workouts": WorkoutsRepository(db),
        "workout_registrations": WorkoutRegistrationsRepository(db),
        "visits": VisitsRepository(db),
        "payments": PaymentsRepository(db),
        "reports": ReportsRepository(db),
        "visit_service": VisitService(db),
        "workout_service": WorkoutService(db),
    }


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(Path("assets/app_icon.svg"))))
    app.setStyleSheet(APP_STYLESHEET)

    db = Database()
    auth_service = AuthService(UsersRepository(db))
    login = LoginWindow(auth_service)

    windows = {"main": None}

    def open_main(user: dict) -> None:
        repositories = build_repositories(db)
        main_window = MainWindow(repositories, user)
        windows["main"] = main_window
        main_window.show()
        login.close()

    login.logged_in.connect(open_main)
    login.show()
    return app.exec()
