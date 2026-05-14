from __future__ import annotations

from decimal import Decimal
from typing import Any

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from mysql.connector import Error

from src.database.connection import Database
from src.repositories.client_portal import ClientPortalRepository
from src.services.workout_service import WorkoutRegistrationError, WorkoutService


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


class Card(BoxLayout):
    def __init__(self, title: str, body: str, **kwargs) -> None:
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(6), size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        self.add_widget(Label(text=title, bold=True, size_hint_y=None, height=dp(24), halign="left"))
        body_label = Label(text=body, size_hint_y=None, halign="left", valign="top")
        body_label.bind(texture_size=lambda label, size: setattr(label, "height", size[1] + dp(8)))
        body_label.bind(width=lambda label, width: setattr(label, "text_size", (width, None)))
        self.add_widget(body_label)


class LoginScreen(Screen):
    def __init__(self, portal: ClientPortalRepository, **kwargs) -> None:
        super().__init__(**kwargs)
        self.portal = portal
        layout = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(14))
        layout.add_widget(Label(text="Fitness Club", font_size=dp(28), bold=True, size_hint_y=None, height=dp(52)))
        layout.add_widget(Label(text="Вход клиента по номеру телефона", size_hint_y=None, height=dp(34)))
        self.phone = TextInput(hint_text="+7 913 100-10-10", multiline=False, size_hint_y=None, height=dp(48))
        self.message = Label(text="", color=(0.8, 0.15, 0.15, 1), size_hint_y=None, height=dp(42))
        button = Button(text="Войти", size_hint_y=None, height=dp(48))
        button.bind(on_press=self.login)
        layout.add_widget(self.phone)
        layout.add_widget(button)
        layout.add_widget(self.message)
        layout.add_widget(Label(text="Демо-телефон: +7 913 100-10-10", size_hint_y=None, height=dp(32)))
        layout.add_widget(Label())
        self.add_widget(layout)

    def login(self, _button) -> None:
        try:
            client = self.portal.find_client_by_phone(self.phone.text)
        except Error as exc:
            self.message.text = f"Ошибка базы данных: {exc}"
            return
        if not client:
            self.message.text = "Клиент с таким телефоном не найден."
            return
        app = App.get_running_app()
        app.client = client
        self.manager.get_screen("home").reload()
        self.manager.current = "home"


class HomeScreen(Screen):
    def __init__(self, portal: ClientPortalRepository, workout_service: WorkoutService, **kwargs) -> None:
        super().__init__(**kwargs)
        self.portal = portal
        self.workout_service = workout_service
        root = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        self.title = Label(text="Личный кабинет", bold=True, halign="left")
        logout = Button(text="Выйти", size_hint_x=None, width=dp(92))
        logout.bind(on_press=self.logout)
        header.add_widget(self.title)
        header.add_widget(logout)
        self.message = Label(text="", size_hint_y=None, height=dp(34), color=(0.1, 0.45, 0.32, 1))
        self.content = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.content)
        root.add_widget(header)
        root.add_widget(self.message)
        root.add_widget(scroll)
        self.add_widget(root)

    def reload(self) -> None:
        self.content.clear_widgets()
        self.message.text = ""
        client = App.get_running_app().client
        self.title.text = client["full_name"]
        try:
            membership = self.portal.active_membership(client["id"])
            visits = self.portal.visits(client["id"])
            registrations = self.portal.client_registrations(client["id"])
            workouts = self.portal.available_workouts()
        except Error as exc:
            self.content.add_widget(Card("Ошибка базы данных", str(exc)))
            return
        body = "Активный абонемент не найден."
        if membership:
            body = (
                f"Тип: {membership['type_name']}\n"
                f"Действует до: {membership['end_date']}\n"
                f"Осталось посещений: {membership['visits_left']}\n"
                f"Стоимость: {fmt(membership['price'])}"
            )
        self.content.add_widget(Card("Абонемент", body))
        self.content.add_widget(Card("Мои записи", self._format_registrations(registrations)))
        self.content.add_widget(Card("История посещений", self._format_visits(visits)))
        self.content.add_widget(Label(text="Ближайшие тренировки", bold=True, size_hint_y=None, height=dp(34)))
        for workout in workouts:
            self.content.add_widget(self._workout_card(workout))

    def _format_visits(self, visits: list[dict[str, Any]]) -> str:
        if not visits:
            return "Посещений пока нет."
        return "\n".join(f"{visit['visited_at']} | {visit['type_name']} | {visit['note'] or ''}" for visit in visits[:8])

    def _format_registrations(self, registrations: list[dict[str, Any]]) -> str:
        if not registrations:
            return "Записей на тренировки пока нет."
        return "\n".join(f"{item['starts_at']} | {item['title']} | {item['trainer_name']}" for item in registrations[:8])

    def _workout_card(self, workout: dict[str, Any]) -> BoxLayout:
        card = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8), size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(Label(text=f"{workout['title']}\n{workout['starts_at']} | {workout['trainer_name']}\nСвободных мест: {workout['free_spots']}", halign="left", size_hint_y=None, height=dp(76)))
        button = Button(text="Записаться", size_hint_y=None, height=dp(42))
        button.bind(on_press=lambda _button, workout_id=workout["id"]: self.register(workout_id))
        card.add_widget(button)
        return card

    def register(self, workout_id: int) -> None:
        client = App.get_running_app().client
        try:
            result = self.workout_service.register_client(workout_id, client["id"])
        except WorkoutRegistrationError as exc:
            self.message.text = str(exc)
            return
        except Error as exc:
            self.message.text = f"Ошибка базы данных: {exc}"
            return
        self.message.text = f"Вы записаны: {result['workout_title']}"
        self.reload()

    def logout(self, _button) -> None:
        App.get_running_app().client = None
        self.manager.current = "login"


class FitnessClientApp(App):
    client: dict[str, Any] | None = None

    def build(self):
        self.title = "Fitness Club"
        db = Database()
        portal = ClientPortalRepository(db)
        workout_service = WorkoutService(db)
        manager = ScreenManager()
        manager.add_widget(LoginScreen(portal, name="login"))
        manager.add_widget(HomeScreen(portal, workout_service, name="home"))
        return manager


def run_mobile_app() -> None:
    FitnessClientApp().run()


if __name__ == "__main__":
    run_mobile_app()
