# app/services/customer_service.py
from __future__ import annotations
from typing import Optional
from app.database.connection import get_connection
from app.models.customer import Customer


def list_customers(query: str = "") -> list[Customer]:
    """
    sales-(2).py خطوط ۱۳۶ و ۲۸۰ — با و بدون query.
    full_name → name mapping در Customer.from_row انجام می‌شود.
    """
    with get_connection() as conn:
        if query:
            rows = conn.execute(
                """
                SELECT id, full_name, phone, created_at
                FROM customers
                WHERE full_name LIKE ? OR phone LIKE ?
                ORDER BY full_name
                """,
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, full_name, phone, created_at FROM customers ORDER BY full_name"
            ).fetchall()
    return [Customer.from_row(r) for r in rows]


def get_customer(customer_id: int) -> Optional[Customer]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, full_name, phone, created_at FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
    return Customer.from_row(row) if row else None


def create_customer(customer: Customer) -> Customer:
    """
    sales-(2).py خط ۶۱ — پس از موفقیت customer.id پر می‌شود.
    address در دیتابیس نیست، نادیده گرفته می‌شود.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO customers (full_name, phone) VALUES (?, ?)",
            (customer.name, customer.phone),
        )
        conn.commit()
        customer.id = cur.lastrowid
    return customer


def update_customer(customer: Customer) -> None:
    """sales-(2).py خط ۵۸."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET full_name=?, phone=? WHERE id=?",
            (customer.name, customer.phone, customer.id),
        )
        conn.commit()


def delete_customer(customer_id: int) -> None:
    """sales-(2).py خط ۳۳۳."""
    with get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
