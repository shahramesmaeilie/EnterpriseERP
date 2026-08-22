import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "enterprise.db"

_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """اتصال یکتا (Singleton) به دیتابیس برمی‌گرداند."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(DB_PATH)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON;")
    return _connection


def close_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
