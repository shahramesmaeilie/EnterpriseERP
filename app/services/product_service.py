# app/services/product_service.py
from __future__ import annotations
from typing import Optional
from app.database.connection import get_connection
from app.models.product import Product


def find_for_scan(barcode: str) -> Optional[Product]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, name, barcode, barcode_type,
                   quantity, stock, unit_price, retail_price,
                   price, description, category_id
            FROM products
            WHERE barcode = ?
            LIMIT 1
            """,
            (barcode,),
        ).fetchone()
    return Product.from_row(row) if row else None


def find_by_name(query: str) -> list[Product]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, barcode, barcode_type,
                   quantity, stock, unit_price, retail_price,
                   price, description, category_id
            FROM products
            WHERE name LIKE ?
            ORDER BY name
            LIMIT 50
            """,
            (f"%{query}%",),
        ).fetchall()
    return [Product.from_row(r) for r in rows]


def list_products(query: str = "") -> list[Product]:
    """لیست همه کالاها؛ اگر query داده شود، بر اساس نام و بارکد فیلتر می‌شود."""
    with get_connection() as conn:
        if query:
            rows = conn.execute(
                """
                SELECT id, name, barcode, barcode_type,
                       quantity, stock, unit_price, retail_price,
                       price, description, category_id
                FROM products
                WHERE name LIKE ? OR barcode LIKE ?
                ORDER BY name
                """,
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, barcode, barcode_type,
                       quantity, stock, unit_price, retail_price,
                       price, description, category_id
                FROM products
                ORDER BY name
                """
            ).fetchall()
    return [Product.from_row(r) for r in rows]


def create_product(product: Product) -> tuple[bool, str]:
    """INSERT و برگرداندن (True, '') یا (False, پیام خطا)."""
    try:
        p = product.to_params()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO products
                    (name, barcode, barcode_type, quantity, stock,
                     unit_price, retail_price, price, description, category_id)
                VALUES
                    (:name, :barcode, :barcode_type, :quantity, :stock,
                     :unit_price, :retail_price, :price, :description, :category_id)
                """,
                p,
            )
            conn.commit()
            product.id = cur.lastrowid
        return True, ""
    except Exception as e:
        return False, str(e)


def update_product(product: Product) -> tuple[bool, str]:
    """UPDATE کامل یک محصول — برگرداندن (True, '') یا (False, پیام خطا)."""
    try:
        p = product.to_params()
        p["id"] = product.id
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE products
                SET name=:name, barcode=:barcode, barcode_type=:barcode_type,
                    quantity=:quantity, stock=:stock,
                    unit_price=:unit_price, retail_price=:retail_price,
                    price=:price, description=:description,
                    category_id=:category_id
                WHERE id=:id
                """,
                p,
            )
            conn.commit()
        return True, ""
    except Exception as e:
        return False, str(e)


def delete_product(product_id: int) -> None:
    """حذف یک کالا بر اساس id."""
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()


def adjust_stock(barcode: str, delta: int) -> tuple[bool, str, Optional[Product]]:
    """
    افزایش/کاهش موجودی بر اساس بارکد.
    delta مثبت = ورود، منفی = خروج.
    برمی‌گردوند: (ok, message, product|None)
    """
    product = find_for_scan(barcode)
    if not product:
        return False, f"کالایی با بارکد «{barcode}» یافت نشد.", None

    new_qty = max(0, product.quantity + delta)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE products
            SET quantity = ?,
                stock    = ?
            WHERE id = ?
            """,
            (new_qty, new_qty, product.id),
        )
        conn.commit()
    product.quantity = new_qty
    return True, "", product
