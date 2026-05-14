from dataclasses import dataclass
from os import getenv

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = getenv("DB_HOST", "localhost")
    port: int = int(getenv("DB_PORT", "3306"))
    user: str = getenv("DB_USER", "root")
    password: str = getenv("DB_PASSWORD", "")
    database: str = getenv("DB_NAME", "fitness_club")
    connection_timeout: int = int(getenv("DB_CONNECTION_TIMEOUT", "5"))


APP_NAME = "Fitness Club IS"
