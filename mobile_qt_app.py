from __future__ import annotations

import sys
from typing import Any

from mysql.connector import Error
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_NAME
from src.database.connection import Database
from src.repositories.client_portal import ClientPortalRepository
from src.services.workout_service import WorkoutRegistrationError, WorkoutService


MOBILE_STYLESHEET = """
QWidget {
    background: #f6f7fb;
    color: #202433;
    font-family: Segoe UI;
    font-size: 14px;
}
QFrame#Screen {
    background: #f6f7fb;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #e4e7ef;
    border-radius: 10px;
}
QFrame#Card QLabel {
    background: transparent;
}
QLabel#Header {
    font-size: 18px;
    font-weight: 700;
}
QLabel#SectionTitle {
    font-size: 17px;
    font-weight: 700;
}
QPushButton {
    background: #1f7a5c;
    color: #ffffff;
    border: 0;
    border-radius: 8px;
    padding: 9px;
    font-weight: 600;
}
QPushButton:hover {
    background: #16654b;
}
QPushButton#NavButton {
    background: #edf1f7;
    color: #243047;
}
QPushButton#NavButton:checked {
    background: #1f7a5c;
    color: #ffffff;
}
QPushButton#LogoutButton {
    background: #dfe5ef;
    color: #243047;
}
QLineEdit {
    background: #ffffff;
    border: 1px solid #d7dce8;
    border-radius: 8px;
    padding: 10px;
}
QScrollArea {
    background: transparent;
    border: 0;
}
"""


def make_card(title: str, body: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(6)
    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: 700;")
    body_label = QLabel(body)
    body_label.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(body_label)
    return frame


def scroll_page() -> tuple[QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    layout.addStretch()
    scroll.setWidget(container)
    return scroll, layout


class MobileClientWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fitness Club")
        self.setWindowIcon(QIcon("assets/app_icon.svg"))
        self.setFixedSize(430, 760)

        self.db = Database()
        self.portal = ClientPortalRepository(self.db)
        self.workout_service = WorkoutService(self.db)
        self.client: dict[str, Any] | None = None
        self.workouts: list[dict[str, Any]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        self.stack = QStackedWidget()
        root.addWidget(self.stack)
        self.stack.addWidget(self._login_page())
        self.stack.addWidget(self._client_page())

    def _login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        title = QLabel("Fitness Club")
        title.setObjectName("Header")
        subtitle = QLabel("Личный кабинет клиента")
        subtitle.setStyleSheet("color: #667085;")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7 913 100-10-10")
        self.phone_input.returnPressed.connect(self.login)
        button = QPushButton("Войти")
        button.clicked.connect(self.login)
        demo = QLabel("Демо-телефон: +7 913 100-10-10")
        demo.setStyleSheet("color: #667085;")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.phone_input)
        layout.addWidget(button)
        layout.addWidget(demo)
        layout.addStretch()
        return page

    def _client_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.client_name = QLabel("Клиент")
        self.client_name.setObjectName("Header")
        self.client_name.setWordWrap(True)
        self.client_name.setMinimumHeight(46)
        logout = QPushButton("Выйти")
        logout.setObjectName("LogoutButton")
        logout.setFixedWidth(72)
        logout.clicked.connect(self.logout)
        header.addWidget(self.client_name, 1)
        header.addWidget(logout)

        nav = QHBoxLayout()
        self.nav_buttons: list[QPushButton] = []
        for index, title in enumerate(["Главная", "Тренировки", "История"]):
            button = QPushButton(title)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _, i=index: self.switch_tab(i))
            self.nav_buttons.append(button)
            nav.addWidget(button)
        self.nav_buttons[0].setChecked(True)

        self.message = QLabel("")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("color: #1f7a5c;")

        self.tabs = QStackedWidget()
        home, self.home_layout = scroll_page()
        workouts, self.workouts_layout = scroll_page()
        history, self.history_layout = scroll_page()
        self.tabs.addWidget(home)
        self.tabs.addWidget(workouts)
        self.tabs.addWidget(history)

        layout.addLayout(header)
        layout.addLayout(nav)
        layout.addWidget(self.message)
        layout.addWidget(self.tabs, 1)
        return page

    def login(self) -> None:
        try:
            client = self.portal.find_client_by_phone(self.phone_input.text())
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            return
        if not client:
            QMessageBox.warning(self, "Вход не выполнен", "Клиент с таким телефоном не найден.")
            return
        self.client = client
        self.reload_client()
        self.stack.setCurrentIndex(1)

    def reload_client(self) -> None:
        if not self.client:
            return
        self.client_name.setText(self.client["full_name"])
        self.message.setText("")
        self._clear_layout(self.home_layout)
        self._clear_layout(self.workouts_layout)
        self._clear_layout(self.history_layout)

        try:
            membership = self.portal.active_membership(self.client["id"])
            visits = self.portal.visits(self.client["id"])
            registrations = self.portal.client_registrations(self.client["id"])
            self.workouts = self.portal.available_workouts()
        except Error as exc:
            self.home_layout.insertWidget(0, make_card("Ошибка базы данных", str(exc)))
            return

        self._fill_home(membership, registrations)
        self._fill_workouts(self.workouts)
        self._fill_history(visits, registrations)

    def _fill_home(self, membership: dict[str, Any] | None, registrations: list[dict[str, Any]]) -> None:
        body = "Активный абонемент не найден."
        if membership:
            body = (
                f"Тип: {membership['type_name']}\n"
                f"До: {membership['end_date']}\n"
                f"Осталось посещений: {membership['visits_left']}\n"
                f"Стоимость: {membership['price']}"
            )
        self.home_layout.insertWidget(0, make_card("Абонемент", body))
        next_registration = "Записей пока нет."
        if registrations:
            item = registrations[0]
            next_registration = f"{item['starts_at']}\n{item['title']}\nТренер: {item['trainer_name']}"
        self.home_layout.insertWidget(1, make_card("Ближайшая запись", next_registration))

    def _fill_workouts(self, workouts: list[dict[str, Any]]) -> None:
        title = QLabel("Ближайшие тренировки")
        title.setObjectName("SectionTitle")
        search = QLineEdit()
        search.setPlaceholderText("Поиск тренировки или тренера")
        search.textChanged.connect(lambda text: self._render_workouts(text))
        self.workouts_layout.insertWidget(0, title)
        self.workouts_layout.insertWidget(1, search)
        self._render_workouts("")

    def _render_workouts(self, query: str) -> None:
        while self.workouts_layout.count() > 3:
            item = self.workouts_layout.takeAt(2)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        normalized = query.lower().strip()
        rows = [
            workout for workout in self.workouts
            if not normalized
            or normalized in str(workout["title"]).lower()
            or normalized in str(workout["trainer_name"]).lower()
        ]
        if not rows:
            self.workouts_layout.insertWidget(2, make_card("Ничего не найдено", "Попробуйте изменить запрос."))
            return
        for index, workout in enumerate(rows[:20], start=2):
            self.workouts_layout.insertWidget(index, self._workout_card(workout))

    def _fill_history(
        self,
        visits: list[dict[str, Any]],
        registrations: list[dict[str, Any]],
    ) -> None:
        self.history_layout.insertWidget(0, QLabel("Мои записи"))
        if registrations:
            for index, item in enumerate(registrations[:12], start=1):
                self.history_layout.insertWidget(
                    index,
                    make_card(
                        item["title"],
                        f"{item['starts_at']}\nТренер: {item['trainer_name']}\nДата записи: {item['registered_at']}",
                    ),
                )
        else:
            self.history_layout.insertWidget(1, make_card("Мои записи", "Записей пока нет."))

        offset = self.history_layout.count() - 1
        self.history_layout.insertWidget(offset, QLabel("Посещения"))
        if visits:
            for item in visits[:15]:
                self.history_layout.insertWidget(
                    self.history_layout.count() - 1,
                    make_card(str(item["visited_at"]), f"Абонемент: {item['type_name']}\n{item['note'] or ''}"),
                )
        else:
            self.history_layout.insertWidget(self.history_layout.count() - 1, make_card("Посещения", "Посещений пока нет."))

    def _workout_card(self, workout: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        info = QLabel(
            f"{workout['title']}\n"
            f"{workout['starts_at']}\n"
            f"Тренер: {workout['trainer_name']}\n"
            f"Свободных мест: {workout['free_spots']}"
        )
        info.setWordWrap(True)
        button = QPushButton("Записаться")
        button.clicked.connect(lambda _, workout_id=workout["id"]: self.register(workout_id))
        layout.addWidget(info)
        layout.addWidget(button)
        return frame

    def register(self, workout_id: int) -> None:
        if not self.client:
            return
        try:
            result = self.workout_service.register_client(workout_id, self.client["id"])
        except WorkoutRegistrationError as exc:
            self.message.setText(str(exc))
            return
        except Error as exc:
            self.message.setText(f"Ошибка базы данных: {exc}")
            return
        self.message.setText(f"Вы записаны: {result['workout_title']}")
        self.reload_client()

    def switch_tab(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def logout(self) -> None:
        self.client = None
        self.phone_input.clear()
        self.stack.setCurrentIndex(0)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


def run_mobile_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} Client")
    app.setWindowIcon(QIcon("assets/app_icon.svg"))
    app.setStyleSheet(MOBILE_STYLESHEET)
    window = MobileClientWindow()
    window.show()
    return app.exec()
