from collections.abc import Callable
from decimal import Decimal
from typing import Any

from mysql.connector import Error
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCompleter,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.repositories.base_repository import BaseRepository
from src.repositories.catalogs import WorkoutRegistrationsRepository
from src.repositories.reports import ReportsRepository
from src.services.visit_service import VisitRegistrationError, VisitService
from src.services.export_service import ExportService
from src.services.workout_service import WorkoutRegistrationError, WorkoutService
from src.ui.forms import open_entity_dialog


DISPLAY_VALUES = {
    "active": "Активен",
    "inactive": "Неактивен",
    "expired": "Истек",
    "closed": "Закрыт",
    "cash": "Наличные",
    "card": "Карта",
    "transfer": "Перевод",
}


def display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return DISPLAY_VALUES.get(str(value), str(value))


def row_matches(row: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    normalized = query.lower()
    return any(normalized in display_value(value).lower() for value in row.values())


def make_searchable_combo(combo: QComboBox) -> None:
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    combo.completer().setCompletionMode(QCompleter.PopupCompletion)
    combo.completer().setFilterMode(Qt.MatchContains)
    combo.completer().setCaseSensitivity(Qt.CaseInsensitive)


class DashboardPage(QWidget):
    def __init__(self, repositories: dict[str, BaseRepository]) -> None:
        super().__init__()
        self.repositories = repositories
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        title = QLabel("Панель управления")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        layout.addLayout(cards)

        for caption, key in [
            ("Клиенты", "clients"),
            ("Абонементы", "memberships"),
            ("Тренеры", "trainers"),
            ("Посещения", "visits"),
        ]:
            cards.addWidget(self._metric_card(caption, key))

        note = QLabel(
            "Система ведет клиентов, абонементы, посещения, тренеров, расписание, оплаты и отчеты."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def _metric_card(self, caption: str, key: str) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)

        value = QLabel("0")
        value.setObjectName("MetricValue")
        label = QLabel(caption)

        try:
            value.setText(str(len(self.repositories[key].list_all())))
        except Error:
            value.setText("БД")

        layout.addWidget(value)
        layout.addWidget(label)
        return card


class CrudPage(QWidget):
    def __init__(
        self,
        title: str,
        repository: BaseRepository,
        columns: list[tuple[str, str]],
        form_fields: list[dict[str, Any]],
    ) -> None:
        super().__init__()
        self.title = title
        self.repository = repository
        self.columns = columns
        self.form_fields = form_fields
        self.rows: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        page_title = QLabel(title)
        page_title.setObjectName("PageTitle")
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_record)
        header.addWidget(page_title)
        header.addStretch()
        header.addWidget(add_button)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")
        self.search.textChanged.connect(self.apply_filter)

        self.table = QTableWidget()
        self.table.setColumnCount(len(columns) + 1)
        self.table.setHorizontalHeaderLabels([label for _, label in columns] + ["Действия"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addLayout(header)
        layout.addWidget(self.search)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.rows = self.repository.list_all()
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            self.rows = []
        self.apply_filter()

    def apply_filter(self) -> None:
        filtered_rows = [row for row in self.rows if row_matches(row, self.search.text().strip())]
        self.table.setRowCount(len(filtered_rows))
        for row_index, row in enumerate(filtered_rows):
            for col_index, (key, _) in enumerate(self.columns):
                item = QTableWidgetItem(display_value(row.get(key)))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row_index, col_index, item)

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            edit_button = QPushButton("Изм.")
            delete_button = QPushButton("Удалить")
            delete_button.setObjectName("DangerButton")
            edit_button.clicked.connect(lambda _, record=row: self.edit_record(record))
            delete_button.clicked.connect(lambda _, record=row: self.delete_record(record))
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.table.setCellWidget(row_index, len(self.columns), actions)

    def add_record(self) -> None:
        open_entity_dialog(
            f"{self.title}: добавление",
            self.form_fields,
            self._create_record,
            parent=self,
        )

    def edit_record(self, row: dict[str, Any]) -> None:
        open_entity_dialog(
            f"{self.title}: редактирование",
            self.form_fields,
            lambda payload: self._update_record(int(row["id"]), payload),
            data=row,
            parent=self,
        )

    def delete_record(self, row: dict[str, Any]) -> None:
        answer = QMessageBox.question(
            self,
            "Удаление",
            "Удалить выбранную запись?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            try:
                self.repository.delete(int(row["id"]))
                self.refresh()
            except Error as exc:
                QMessageBox.warning(self, "Ошибка базы данных", str(exc))

    def _create_record(self, payload: dict[str, Any]) -> None:
        try:
            self.repository.create(payload)
            self.refresh()
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))

    def _update_record(self, item_id: int, payload: dict[str, Any]) -> None:
        try:
            self.repository.update(item_id, payload)
            self.refresh()
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))


class VisitsPage(QWidget):
    def __init__(
        self,
        visits_repository: BaseRepository,
        visit_service: VisitService,
        client_options_provider: Callable[[], list[tuple[int, str]]],
    ) -> None:
        super().__init__()
        self.visits_repository = visits_repository
        self.visit_service = visit_service
        self.client_options_provider = client_options_provider
        self.rows: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        title = QLabel("Регистрация посещений")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        registration = QFrame()
        registration.setObjectName("MetricCard")
        registration_layout = QHBoxLayout(registration)
        registration_layout.setContentsMargins(16, 14, 16, 14)
        registration_layout.setSpacing(12)

        self.client_select = QComboBox()
        self.client_select.setMinimumWidth(280)
        make_searchable_combo(self.client_select)

        self.note = QTextEdit()
        self.note.setPlaceholderText("Примечание")
        self.note.setFixedHeight(48)

        register_button = QPushButton("Зарегистрировать вход")
        register_button.clicked.connect(self.register_visit)

        registration_layout.addWidget(self.client_select)
        registration_layout.addWidget(self.note, 1)
        registration_layout.addWidget(register_button)
        layout.addWidget(registration)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по истории посещений")
        self.search.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search)

        self.table = QTableWidget()
        self.columns = [
            ("id", "ID"),
            ("client_name", "Клиент"),
            ("membership_type", "Абонемент"),
            ("visited_at", "Дата и время"),
            ("note", "Примечание"),
        ]
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([label for _, label in self.columns])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.refresh()

    def register_visit(self) -> None:
        try:
            result = self.visit_service.register_visit(
                int(self.client_select.currentData()),
                self.note.toPlainText(),
            )
        except VisitRegistrationError as exc:
            QMessageBox.warning(self, "Посещение не зарегистрировано", str(exc))
            return
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            return

        QMessageBox.information(
            self,
            "Посещение зарегистрировано",
            (
                f"Абонемент: {result['membership_type']}\n"
                f"Осталось посещений: {result['visits_left']}"
            ),
        )
        self.note.clear()
        self.refresh()

    def refresh(self) -> None:
        self._reload_clients()
        try:
            self.rows = self.visits_repository.list_all()
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            self.rows = []
        self.apply_filter()

    def apply_filter(self) -> None:
        filtered_rows = [row for row in self.rows if row_matches(row, self.search.text().strip())]
        self.table.setRowCount(len(filtered_rows))
        for row_index, row in enumerate(filtered_rows):
            for col_index, (key, _) in enumerate(self.columns):
                item = QTableWidgetItem(display_value(row.get(key)))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row_index, col_index, item)

    def _reload_clients(self) -> None:
        selected = self.client_select.currentData()
        self.client_select.blockSignals(True)
        self.client_select.clear()
        for value, label in self.client_options_provider():
            self.client_select.addItem(label, value)
        if selected is not None:
            index = self.client_select.findData(selected)
            if index >= 0:
                self.client_select.setCurrentIndex(index)
        self.client_select.blockSignals(False)


class SchedulePage(QWidget):
    def __init__(
        self,
        registrations_repository: WorkoutRegistrationsRepository,
        workout_service: WorkoutService,
        client_options_provider: Callable[[], list[tuple[int, str]]],
        workout_options_provider: Callable[[], list[tuple[int, str]]],
    ) -> None:
        super().__init__()
        self.registrations_repository = registrations_repository
        self.workout_service = workout_service
        self.client_options_provider = client_options_provider
        self.workout_options_provider = workout_options_provider
        self.schedule_rows: list[dict[str, Any]] = []
        self.registration_rows: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        title = QLabel("Расписание и запись")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        registration = QFrame()
        registration.setObjectName("MetricCard")
        registration_layout = QHBoxLayout(registration)
        registration_layout.setContentsMargins(16, 14, 16, 14)
        registration_layout.setSpacing(12)

        self.workout_select = QComboBox()
        self.workout_select.setMinimumWidth(360)
        self.client_select = QComboBox()
        self.client_select.setMinimumWidth(280)
        make_searchable_combo(self.workout_select)
        make_searchable_combo(self.client_select)

        register_button = QPushButton("Записать клиента")
        register_button.clicked.connect(self.register_client)

        registration_layout.addWidget(self.workout_select, 2)
        registration_layout.addWidget(self.client_select, 1)
        registration_layout.addWidget(register_button)
        layout.addWidget(registration)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск по расписанию и записям")
        self.search.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search)

        self.schedule_table = QTableWidget()
        self.schedule_columns = [
            ("title", "Тренировка"),
            ("trainer_name", "Тренер"),
            ("starts_at", "Дата и время"),
            ("capacity", "Мест"),
            ("registered_count", "Записано"),
            ("free_spots", "Свободно"),
        ]
        self.schedule_table.setColumnCount(len(self.schedule_columns))
        self.schedule_table.setHorizontalHeaderLabels([label for _, label in self.schedule_columns])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.schedule_table)

        registrations_title = QLabel("Записи клиентов")
        registrations_title.setObjectName("PageTitle")
        layout.addWidget(registrations_title)

        self.registrations_table = QTableWidget()
        self.registration_columns = [
            ("client_name", "Клиент"),
            ("workout_title", "Тренировка"),
            ("trainer_name", "Тренер"),
            ("starts_at", "Дата тренировки"),
            ("registered_at", "Дата записи"),
        ]
        self.registrations_table.setColumnCount(len(self.registration_columns))
        self.registrations_table.setHorizontalHeaderLabels(
            [label for _, label in self.registration_columns]
        )
        self.registrations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.registrations_table.verticalHeader().setVisible(False)
        self.registrations_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.registrations_table)

        self.refresh()

    def register_client(self) -> None:
        try:
            result = self.workout_service.register_client(
                int(self.workout_select.currentData()),
                int(self.client_select.currentData()),
            )
        except WorkoutRegistrationError as exc:
            QMessageBox.warning(self, "Запись не выполнена", str(exc))
            return
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            return

        QMessageBox.information(
            self,
            "Клиент записан",
            f"Тренировка: {result['workout_title']}\nСвободных мест: {result['free_spots']}",
        )
        self.refresh()

    def refresh(self) -> None:
        self._reload_selects()
        try:
            self.schedule_rows = self.registrations_repository.list_schedule()
            self.registration_rows = self.registrations_repository.list_registrations()
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            self.schedule_rows = []
            self.registration_rows = []
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search.text().strip()
        schedule_rows = [row for row in self.schedule_rows if row_matches(row, query)]
        registration_rows = [row for row in self.registration_rows if row_matches(row, query)]

        self.schedule_table.setRowCount(len(schedule_rows))
        for row_index, row in enumerate(schedule_rows):
            for col_index, (key, _) in enumerate(self.schedule_columns):
                item = QTableWidgetItem(display_value(row.get(key)))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.schedule_table.setItem(row_index, col_index, item)

        self.registrations_table.setRowCount(len(registration_rows))
        for row_index, row in enumerate(registration_rows):
            for col_index, (key, _) in enumerate(self.registration_columns):
                item = QTableWidgetItem(display_value(row.get(key)))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.registrations_table.setItem(row_index, col_index, item)

    def _reload_selects(self) -> None:
        self._reload_combo(self.client_select, self.client_options_provider())
        self._reload_combo(self.workout_select, self.workout_options_provider())

    def _reload_combo(self, combo: QComboBox, options: list[tuple[int, str]]) -> None:
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for value, label in options:
            combo.addItem(label, value)
        if selected is not None:
            index = combo.findData(selected)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)


class ReportsPage(QWidget):
    def __init__(self, reports: ReportsRepository) -> None:
        super().__init__()
        self.reports = reports
        self.export_service = ExportService()
        self.report_data: dict[str, list[dict[str, Any]]] = {}
        self.report_tables: dict[str, QTableWidget] = {}
        self.report_columns = {
            "revenue": (
                "Выручка",
                [
                    ("payment_date", "Дата"),
                    ("client_name", "Клиент"),
                    ("membership_type", "Абонемент"),
                    ("amount", "Сумма"),
                    ("payment_method", "Метод оплаты"),
                ],
            ),
            "visits": (
                "Посещения",
                [
                    ("visit_date", "Дата"),
                    ("visit_time", "Время"),
                    ("client_name", "Клиент"),
                    ("membership_type", "Абонемент"),
                    ("note", "Примечание"),
                ],
            ),
            "workouts": (
                "Записи на тренировки",
                [
                    ("workout_date", "Дата"),
                    ("workout_time", "Время"),
                    ("workout_title", "Тренировка"),
                    ("trainer_name", "Тренер"),
                    ("client_name", "Клиент"),
                    ("registered_at", "Дата записи"),
                ],
            ),
            "memberships": (
                "Статусы абонементов",
                [
                    ("status", "Статус"),
                    ("memberships_count", "Количество"),
                    ("total_price", "Сумма"),
                ],
            ),
            "expiring": (
                "Требуют внимания",
                [
                    ("id", "ID"),
                    ("client_name", "Клиент"),
                    ("type_name", "Абонемент"),
                    ("end_date", "Окончание"),
                    ("visits_left", "Осталось"),
                ],
            ),
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        title = QLabel("Отчеты")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        filters = QHBoxLayout()
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate().addDays(14))

        refresh_button = QPushButton("Сформировать")
        refresh_button.clicked.connect(self.refresh)
        export_csv_button = QPushButton("Экспорт CSV")
        export_csv_button.clicked.connect(self.export_csv)
        export_xlsx_button = QPushButton("Экспорт Excel")
        export_xlsx_button.clicked.connect(self.export_xlsx)

        filters.addWidget(QLabel("Период с"))
        filters.addWidget(self.start_date)
        filters.addWidget(QLabel("по"))
        filters.addWidget(self.end_date)
        filters.addStretch()
        filters.addWidget(refresh_button)
        filters.addWidget(export_csv_button)
        filters.addWidget(export_xlsx_button)
        layout.addLayout(filters)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        layout.addLayout(cards)

        self.metric_labels: dict[str, QLabel] = {}
        for key, caption in [
            ("visits_count", "Посещений за период"),
            ("payments_count", "Оплат за период"),
            ("revenue", "Выручка за период"),
            ("workout_registrations_count", "Записей на тренировки"),
        ]:
            card = QFrame()
            card.setObjectName("MetricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 16, 18, 16)
            value = QLabel("0")
            value.setObjectName("MetricValue")
            label = QLabel(caption)
            self.metric_labels[key] = value
            card_layout.addWidget(value)
            card_layout.addWidget(label)
            cards.addWidget(card)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск в текущих отчетах")
        self.search.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search)

        self.tabs = QTabWidget()
        for report_key, (title_text, columns) in self.report_columns.items():
            table = QTableWidget()
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels([label for _, label in columns])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.report_tables[report_key] = table
            self.tabs.addTab(table, title_text)
        layout.addWidget(self.tabs)

        self.refresh()

    def refresh(self) -> None:
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        if start_date > end_date:
            QMessageBox.warning(self, "Период отчета", "Дата начала не может быть позже даты окончания.")
            return

        try:
            summary = self.reports.period_summary(start_date, end_date)
            self.report_data = {
                "revenue": self.reports.revenue_by_period(start_date, end_date),
                "visits": self.reports.visits_by_period(start_date, end_date),
                "workouts": self.reports.workout_registrations_by_period(start_date, end_date),
                "memberships": self.reports.membership_statuses(),
                "expiring": self.reports.expiring_memberships(),
            }
        except Error as exc:
            QMessageBox.warning(self, "Ошибка базы данных", str(exc))
            summary = {}
            self.report_data = {key: [] for key in self.report_columns}

        for key, label in self.metric_labels.items():
            label.setText(display_value(summary.get(key, 0)))
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search.text().strip()
        for report_key, rows in self.report_data.items():
            _, columns = self.report_columns[report_key]
            filtered_rows = [row for row in rows if row_matches(row, query)]
            self._fill_table(self.report_tables[report_key], columns, filtered_rows)

    def export_csv(self) -> None:
        report_key = self._current_report_key()
        title, columns = self.report_columns[report_key]
        rows = self._current_filtered_rows(report_key)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV",
            f"{title}.csv",
            "CSV (*.csv)",
        )
        if path:
            self.export_service.export_csv(
                path,
                [label for _, label in columns],
                rows,
                [key for key, _ in columns],
            )
            QMessageBox.information(self, "Экспорт", "CSV-файл сохранен.")

    def export_xlsx(self) -> None:
        report_key = self._current_report_key()
        title, columns = self.report_columns[report_key]
        rows = self._current_filtered_rows(report_key)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить Excel",
            f"{title}.xlsx",
            "Excel (*.xlsx)",
        )
        if path:
            self.export_service.export_xlsx(
                path,
                title,
                [label for _, label in columns],
                rows,
                [key for key, _ in columns],
            )
            QMessageBox.information(self, "Экспорт", "Excel-файл сохранен.")

    def _fill_table(
        self,
        table: QTableWidget,
        columns: list[tuple[str, str]],
        rows: list[dict[str, Any]],
    ) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, (key, _) in enumerate(columns):
                item = QTableWidgetItem(display_value(row.get(key)))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                table.setItem(row_index, col_index, item)

    def _current_report_key(self) -> str:
        return list(self.report_columns.keys())[self.tabs.currentIndex()]

    def _current_filtered_rows(self, report_key: str) -> list[dict[str, Any]]:
        query = self.search.text().strip()
        return [row for row in self.report_data.get(report_key, []) if row_matches(row, query)]
