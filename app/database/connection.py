"""
مدیریت اتصال به SQLite.
تنها نقطه‌ی مجاز برای ساخت connection در کل پروژه.
لایه‌های UI هرگز مستقیماً این ماژول را ایمپورت نمی‌کنند؛ فقط app/services/*.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# app/database/connection.py -> app/database -> app -> <project root>
DB_PATH: Path = Path(__file__).resolve().parent.parent.parent / "enterprise.db"


def _configure(conn: sqlite3.Connection) -> None:
    """تنظیمات پایه‌ی هر اتصال تازه."""
    conn.row_factory = sqlite3.Row          # دسترسی به ستون‌ها با نام
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # همزمانی بهتر خواندن/نوشتن
    conn.execute("PRAGMA synchronous = NORMAL")


def get_connection() -> sqlite3.Connection:
    """
    یک اتصال تازه و تنظیم‌شده برمی‌گرداند.
    مسئولیت بستن آن با فراخواننده است؛ در حالت عادی از get_cursor استفاده کنید.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"فایل دیتابیس پیدا نشد: {DB_PATH}\n"
            "ابتدا migrations/001_add_missing_columns.py را اجرا کنید."
        )
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    _configure(conn)
    return conn


@contextmanager
def get_cursor(commit: bool = False) -> Iterator[sqlite3.Cursor]:
    """
    context manager استاندارد برای کوئری‌ها.

        with get_cursor() as cur:                # خواندن
            rows = cur.execute("SELECT ...").fetchall()

        with get_cursor(commit=True) as cur:     # نوشتن
            cur.execute("INSERT ...", params)

    در صورت بروز خطا rollback و سپس اتصال بسته می‌شود.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def table_columns(table: str) -> set[str]:
    """نام ستون‌های یک جدول — برای بررسی سازگاری اسکیما در زمان اجرا."""
    with get_cursor() as cur:
        return {r["name"] for r in cur.execute(f'PRAGMA table_info("{table}")')}
