from src.repositories.users import UsersRepository


class AuthService:
    def __init__(self, users: UsersRepository) -> None:
        self.users = users

    def login(self, username: str, password: str) -> dict | None:
        if not username.strip() or not password:
            return None
        return self.users.find_by_credentials(username.strip(), password)
