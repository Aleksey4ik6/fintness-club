from mysql.connector import Error
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.auth_service import AuthService


class LoginWindow(QWidget):
    logged_in = Signal(dict)

    def __init__(self, auth_service: AuthService) -> None:
        super().__init__()
        self.auth_service = auth_service
        self.setWindowTitle("Вход в систему")
        self.setWindowIcon(QIcon("assets/app_icon.svg"))
        self.setFixedSize(380, 310)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(14)

        title = QLabel("Fitness Club IS")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Авторизация сотрудника")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Логин")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Пароль")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.try_login)

        button = QPushButton("Войти")
        button.clicked.connect(self.try_login)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(button)
        layout.addStretch()

    def try_login(self) -> None:
        try:
            user = self.auth_service.login(self.username.text(), self.password.text())
        except Error as exc:
            QMessageBox.warning(self, "Ошибка подключения", str(exc))
            return

        if not user:
            QMessageBox.warning(self, "Вход не выполнен", "Проверьте логин и пароль.")
            return

        self.logged_in.emit(user)
