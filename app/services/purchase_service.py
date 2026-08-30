# -*- coding: utf-8 -*-
"""سرویس فاکتور خرید: ثبت فاکتور، افزایش موجودی، تعریف خودکار کالای جدید"""

import sqlite3
from datetime import datetime

from app.models.purchase import PurchaseInvoice, PurchaseItem
from app.database.connection import get_connection
from app.services import product_service


def _ensure_tables():
    product_service._ensure_table()          # جدول products آماده باشد
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT NOT NULL,
                invoice_no TEXT DEFAULT '',
                date TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL REFERENCES purchase_invoices(id),
                product_id INTEGER,
                product_name TEXT NOT NULL,
                barcode TEXT NOT NULL,
                barcode_type TEXT DEFAULT '1D',
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL
            )
        """)


def register_purchase(inv: PurchaseInvoice) -> tuple[bool, str]:
    """ثبت فاکتور خرید در یک تراکنش:
    - کالای موجود (بارکد تکراری) → موجودی زیاد می‌شود.
    - کالای جدید → در جدول products تعریف می‌شود (قیمت اولیهٔ فروش = قیمت خرید).
    در صورت هر خطا کل تراکنش rollback می‌شود."""
    if not inv.items:
        return False, "فاکتور خرید هیچ قلمی ندارد."
    _ensure_tables()
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN")
        cur = conn.execute(
            "INSERT INTO purchase_invoices (supplier, invoice_no, date, total) "
            "VALUES (?, ?, ?, ?)",
            (inv.supplier, inv.invoice_no, inv.date, inv.total))
        purchase_id = cur.lastrowid

        for item in inv.items:
            row = conn.execute("SELECT id, quantity FROM products WHERE barcode = ?",
                               (item.barcode,)).fetchone()
            if row:                                          # کالای موجود → افزایش موجودی
                product_id = row["id"]
                conn.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?",
                             (item.quantity, product_id))
            else:                                            # کالای جدید → تعریف خودکار
                cur = conn.execute(
                    "INSERT INTO products (name, barcode, barcode_type, "
                    "quantity, unit_price, description) VALUES (?, ?, ?, ?, ?, '')",
                    (item.product_name, item.barcode, item.barcode_type,
                     item.quantity, item.unit_price))
                product_id = cur.lastrowid

            conn.execute(
                "INSERT INTO purchase_items (purchase_id, product_id, product_name, "
                "barcode, barcode_type, quantity, unit_price, total) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (purchase_id, product_id, item.product_name, item.barcode,
                 item.barcode_type, item.quantity, item.unit_price, item.total))

        conn.commit()
        return True, f"فاکتور خرید شمارهٔ {purchase_id} ثبت و کالاها به انبار اضافه شد."
    except Exception as exc:
        conn.rollback()
        return False, f"ثبت فاکتور خرید ناموفق بود: {exc}"
    finally:
        conn.close()


def list_purchases(search: str = "") -> list[dict]:
    """فهرست فاکتورهای خرید برای تب سابقه (جست‌وجو با نام شرکت یا شمارهٔ فاکتور)."""
    _ensure_tables()
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        if search:
            like = f"%{search}%"
            rows = conn.execute(
                "SELECT * FROM purchase_invoices "
                "WHERE supplier LIKE ? OR invoice_no LIKE ? ORDER BY id DESC",
                (like, like)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM purchase_invoices ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def purchase_items(purchase_id: int) -> list[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM purchase_items WHERE purchase_id = ?",
                            (purchase_id,)).fetchall()
    return [dict(r) for r in rows]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
