from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

from src.config import DatabaseConfig


class Database:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or DatabaseConfig()

    @contextmanager
    def connect(self):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                connection_timeout=self.config.connection_timeout,
                autocommit=False,
            )
            yield connection
            connection.commit()
        except Error:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def ping(self) -> bool:
        with self.connect() as connection:
            return connection.is_connected()
