from pathlib import Path

import mysql.connector

from src.config import DatabaseConfig


def split_sql(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []

    if current:
        statements.append("\n".join(current))

    return statements


def main() -> None:
    config = DatabaseConfig()
    schema_path = Path("database/schema.sql")
    statements = split_sql(schema_path.read_text(encoding="utf-8"))

    connection = mysql.connector.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        connection_timeout=config.connection_timeout,
        autocommit=True,
    )
    try:
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)
        print(f"Database schema applied: {config.database}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
