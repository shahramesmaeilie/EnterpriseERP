"""
Migration 001 — افزودن ستون‌های گم‌شده.
  customers.address  TEXT NOT NULL DEFAULT ''
  invoices.discount  REAL NOT NULL DEFAULT 0

idempotent است: اجرای چندباره بی‌خطر است.
اجرا:  python migrations/001_add_missing_columns.py
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "enterprise.db"

MIGRATIONS: list[tuple[str, str, str]] = [
    # (جدول, ستون, تعریف)
    ("customers", "address",  "TEXT NOT NULL DEFAULT ''"),
    ("invoices",  "discount", "REAL NOT NULL DEFAULT 0"),
]


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def main() -> int:
    if not DB_PATH.exists():
        print(f"[!] دیتابیس پیدا نشد: {DB_PATH}")
        return 1

    backup = DB_PATH.with_name(
        f"enterprise.backup-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    shutil.copy2(DB_PATH, backup)
    print(f"[i] بکاپ: {backup.name}")

    changed = 0
    with sqlite3.connect(DB_PATH) as conn:
        for table, column, decl in MIGRATIONS:
            if not table_exists(conn, table):
                print(f"[!] جدول {table} وجود ندارد — رد شد")
                continue
            if column in columns(conn, table):
                print(f"[=] {table}.{column} از قبل هست")
                continue
            conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {decl}')
            print(f"[+] {table}.{column} اضافه شد")
            changed += 1
        conn.commit()

    print(f"\n[✓] پایان — {changed} تغییر اعمال شد")
    for table, column, _ in MIGRATIONS:
        with sqlite3.connect(DB_PATH) as conn:
            if table_exists(conn, table):
                print(f"    {table}: {sorted(columns(conn, table))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
