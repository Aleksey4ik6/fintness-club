from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

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
from src.services.visit_service import VisitService
from src.services.workout_service import WorkoutService
from src.ui.pages import CrudPage, DashboardPage, ReportsPage, SchedulePage, VisitsPage


class MainWindow(QMainWindow):
    def __init__(self, repositories: dict, user: dict) -> None:
        super().__init__()
        self.repositories = repositories
        self.user = user
        self.setWindowTitle("Fitness Club IS")
        self.setWindowIcon(QIcon("assets/app_icon.svg"))
        self.resize(1280, 760)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(245)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 22, 18, 18)
        sidebar_layout.setSpacing(8)

        brand = QLabel("Fitness Club")
        brand.setObjectName("Brand")
        user_label = QLabel(f"{user['full_name']} | {user['role']}")
        user_label.setStyleSheet("color: #aeb8cc; background: transparent;")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(user_label)
        sidebar_layout.addSpacing(16)

        self.stack = QStackedWidget()
        self.pages = self._build_pages()

        for title, page in self.pages:
            index = self.stack.addWidget(page)
            button = QPushButton(title)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _, i=index, b=button: self.switch_page(i, b))
            sidebar_layout.addWidget(button)
            if index == 0:
                button.setChecked(True)
                self.active_button = button

        sidebar_layout.addStretch()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)
        self.setCentralWidget(root)

    def switch_page(self, index: int, button: QPushButton) -> None:
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()
        self.active_button.setChecked(False)
        button.setChecked(True)
        self.active_button = button

    def _build_pages(self):
        clients: ClientsRepository = self.repositories["clients"]
        memberships: MembershipsRepository = self.repositories["memberships"]
        trainers: TrainersRepository = self.repositories["trainers"]
        workouts: WorkoutsRepository = self.repositories["workouts"]
        workout_registrations: WorkoutRegistrationsRepository = self.repositories[
            "workout_registrations"
        ]
        visits: VisitsRepository = self.repositories["visits"]
        payments: PaymentsRepository = self.repositories["payments"]
        reports: ReportsRepository = self.repositories["reports"]
        visit_service: VisitService = self.repositories["visit_service"]
        workout_service: WorkoutService = self.repositories["workout_service"]

        client_options = lambda: clients.list_options()
        trainer_options = lambda: trainers.list_options()
        membership_options = lambda: payments.list_membership_options()

        return [
            ("Дашборд", DashboardPage(self.repositories)),
            (
                "Клиенты",
                CrudPage(
                    "Клиенты",
                    clients,
                    [
                        ("id", "ID"),
                        ("full_name", "ФИО"),
                        ("phone", "Телефон"),
                        ("email", "Email"),
                        ("birth_date", "Дата рождения"),
                        ("status", "Статус"),
                    ],
                    [
                        {"name": "full_name", "label": "ФИО", "type": "string"},
                        {"name": "phone", "label": "Телефон", "type": "string"},
                        {"name": "email", "label": "Email", "type": "string"},
                        {"name": "birth_date", "label": "Дата рождения", "type": "date"},
                        {
                            "name": "status",
                            "label": "Статус",
                            "type": "choice",
                            "options": [("active", "Активный"), ("inactive", "Неактивный")],
                        },
                    ],
                ),
            ),
            (
                "Абонементы",
                CrudPage(
                    "Абонементы",
                    memberships,
                    [
                        ("id", "ID"),
                        ("client_name", "Клиент"),
                        ("type_name", "Тип"),
                        ("start_date", "Начало"),
                        ("end_date", "Окончание"),
                        ("visits_left", "Посещений"),
                        ("price", "Цена"),
                        ("status", "Статус"),
                    ],
                    [
                        {
                            "name": "client_id",
                            "label": "Клиент",
                            "type": "foreign_choice",
                            "options_provider": client_options,
                        },
                        {"name": "type_name", "label": "Тип", "type": "string"},
                        {"name": "start_date", "label": "Дата начала", "type": "date"},
                        {"name": "end_date", "label": "Дата окончания", "type": "date"},
                        {"name": "visits_left", "label": "Осталось посещений", "type": "int"},
                        {"name": "price", "label": "Цена", "type": "money"},
                        {
                            "name": "status",
                            "label": "Статус",
                            "type": "choice",
                            "options": [
                                ("active", "Активен"),
                                ("expired", "Истек"),
                                ("closed", "Закрыт"),
                            ],
                        },
                    ],
                ),
            ),
            ("Посещения", VisitsPage(visits, visit_service, client_options)),
            (
                "Расписание",
                SchedulePage(
                    workout_registrations,
                    workout_service,
                    client_options,
                    lambda: workouts.list_options(),
                ),
            ),
            (
                "Тренеры",
                CrudPage(
                    "Тренеры",
                    trainers,
                    [
                        ("id", "ID"),
                        ("full_name", "ФИО"),
                        ("phone", "Телефон"),
                        ("specialization", "Специализация"),
                        ("work_schedule", "График"),
                        ("status", "Статус"),
                    ],
                    [
                        {"name": "full_name", "label": "ФИО", "type": "string"},
                        {"name": "phone", "label": "Телефон", "type": "string"},
                        {"name": "specialization", "label": "Специализация", "type": "string"},
                        {"name": "work_schedule", "label": "График", "type": "string"},
                        {
                            "name": "status",
                            "label": "Статус",
                            "type": "choice",
                            "options": [("active", "Активный"), ("inactive", "Неактивный")],
                        },
                    ],
                ),
            ),
            (
                "Тренировки",
                CrudPage(
                    "Групповые тренировки",
                    workouts,
                    [
                        ("id", "ID"),
                        ("title", "Название"),
                        ("trainer_name", "Тренер"),
                        ("starts_at", "Начало"),
                        ("capacity", "Мест"),
                        ("description", "Описание"),
                    ],
                    [
                        {"name": "title", "label": "Название", "type": "string"},
                        {
                            "name": "trainer_id",
                            "label": "Тренер",
                            "type": "foreign_choice",
                            "options_provider": trainer_options,
                        },
                        {"name": "starts_at", "label": "Дата и время", "type": "datetime"},
                        {"name": "capacity", "label": "Мест", "type": "int"},
                        {"name": "description", "label": "Описание", "type": "text"},
                    ],
                ),
            ),
            (
                "Оплаты",
                CrudPage(
                    "Оплаты",
                    payments,
                    [
                        ("id", "ID"),
                        ("client_name", "Клиент"),
                        ("membership_type", "Абонемент"),
                        ("amount", "Сумма"),
                        ("payment_date", "Дата"),
                        ("payment_method", "Метод"),
                    ],
                    [
                        {
                            "name": "client_id",
                            "label": "Клиент",
                            "type": "foreign_choice",
                            "options_provider": client_options,
                        },
                        {
                            "name": "membership_id",
                            "label": "Абонемент",
                            "type": "foreign_choice",
                            "options_provider": membership_options,
                        },
                        {"name": "amount", "label": "Сумма", "type": "money"},
                        {"name": "payment_date", "label": "Дата оплаты", "type": "date"},
                        {
                            "name": "payment_method",
                            "label": "Метод оплаты",
                            "type": "choice",
                            "options": [
                                ("cash", "Наличные"),
                                ("card", "Карта"),
                                ("transfer", "Перевод"),
                            ],
                        },
                    ],
                ),
            ),
            ("Отчеты", ReportsPage(reports)),
        ]
