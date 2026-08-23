import sqlite3
from pathlib import Path

# مسیر دیتابیس کنار پوشه database
DB_PATH = Path(__file__).resolve().parents[2] / "enterprise.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'user',
    permissions TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1
);
"""


def get_connection() -> sqlite3.Connection:
    """اتصال به دیتابیس با خروجی سطرهای dict-مانند."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """ساخت جدول‌ها در صورت نبودن؛ برای دیتابیس‌های موجود بی‌خطر است."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)
