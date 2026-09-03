"""مهاجرت‌های ستون‌محور و جدول‌محور؛ در زمان راه‌اندازی اجرا می‌شود."""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]      # ریشه EnterpriseERP
DB_PATH = BASE_DIR / "enterprise.db"

# (جدول, ستون, تعریف SQL) — نام‌ها ثابت داخلی‌اند، ورودی کاربر نیستند
REQUIRED_COLUMNS: list[tuple[str, str, str]] = [
    ("products", "barcode_type", "TEXT DEFAULT '1D'"),
    ("products", "barcode",      "TEXT DEFAULT ''"),
    ("products", "quantity",     "INTEGER DEFAULT 0"),
    ("products", "unit_price",   "REAL DEFAULT 0.0"),
    ("products", "description",  "TEXT DEFAULT ''"),
    ("products", "retail_price", "REAL DEFAULT 0.0"),
]

REQUIRED_TABLES: dict[str, str] = {
    "invoices": """
        CREATE TABLE invoices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            total       REAL NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """,
    "invoice_items": """
        CREATE TABLE invoice_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity   INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL
        )
    """,
    # جدول حسابداری به صورت مجزا و صحیح اضافه شد
    "accounting_docs": """
        CREATE TABLE IF NOT EXISTS accounting_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_number TEXT,
            date TEXT,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """,
}


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def run_migrations() -> list[str]:
    """ستون‌ها/جدول‌های گم‌شده را می‌سازد و فهرست تغییرات را برمی‌گرداند."""
    applied: list[str] = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        existing = _tables(conn)

        for name, ddl in REQUIRED_TABLES.items():
            if name not in existing:
                conn.executescript(ddl)
                applied.append(f"table:{name}")

        for table, column, ddl in REQUIRED_COLUMNS:
            if table not in existing:
                continue
            if column not in _columns(conn, table):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
                applied.append(f"{table}.{column}")

        # پرکردن ستون‌های موازی برای رکوردهای قدیمی
        if "products" in existing:
            cols = _columns(conn, "products")
            if {"quantity", "stock"} <= cols:
                conn.execute(
                    "UPDATE products SET quantity = stock "
                    "WHERE COALESCE(quantity, 0) = 0 AND COALESCE(stock, 0) <> 0"
                )
            if {"unit_price", "price"} <= cols:
                conn.execute(
                    "UPDATE products SET unit_price = price "
                    "WHERE COALESCE(unit_price, 0) = 0 AND COALESCE(price, 0) <> 0"
                )
            if {"retail_price", "price"} <= cols:
                conn.execute(
                    "UPDATE products SET retail_price = price "
                    "WHERE COALESCE(retail_price, 0) = 0 AND COALESCE(price, 0) <> 0"
                )
        conn.commit()

    return applied