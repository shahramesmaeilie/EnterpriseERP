# app/services/invoice_service.py
from __future__ import annotations
from typing import Optional
from app.core.session import Session
from app.database.connection import get_connection
from app.models.invoice import InvoiceItem


def create_invoice(
    customer_id: Optional[int],
    items: list[InvoiceItem],
) -> tuple[bool, str, Optional[int]]:
    """
    sales-(2).py خط ۲۱۳.
    برمی‌گرداند: (ok, message, invoice_id)
    user_id از Session گرفته می‌شود (invoices.user_id NOT NULL).
    """
    if not items:
        return False, "سبد خرید خالی است.", None

    user = Session.current_user
    if user is None:
        return False, "کاربری در سیستم وارد نشده است.", None

    total = sum(it.quantity * it.unit_price for it in items)

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO invoices (customer_id, user_id, total)
                VALUES (?, ?, ?)
                """,
                (customer_id, user.id, total),
            )
            inv_id = cur.lastrowid

            conn.executemany(
                """
                INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (inv_id, it.product_id, it.quantity, it.unit_price)
                    for it in items
                ],
            )

            # کسر موجودی — در یک تراکنش
            conn.executemany(
                """
                UPDATE products
                SET quantity = MAX(0, quantity - ?),
                    stock    = MAX(0, stock    - ?)
                WHERE id = ?
                """,
                [(it.quantity, it.quantity, it.product_id) for it in items],
            )

            conn.commit()
        return True, "فاکتور با موفقیت ثبت شد.", inv_id

    except Exception as exc:  # noqa: BLE001
        return False, f"خطا در ثبت فاکتور: {exc}", None


def invoice_html(
    inv_id: int,
    customer_name: str,
    items: list[InvoiceItem],
    date_str: str,
) -> str:
    """
    sales-(2).py خطوط ۲۱۹–۲۲۴.
    HTML ساده برای چاپ/پیش‌نمایش فاکتور.
    """
    rows_html = ""
    total = 0.0
    for i, it in enumerate(items, 1):
        line = it.quantity * it.unit_price
        total += line
        rows_html += (
            f"<tr>"
            f"<td>{i}</td>"
            f"<td>{it.product_name}</td>"
            f"<td>{it.quantity:,}</td>"
            f"<td>{it.unit_price:,.0f}</td>"
            f"<td>{line:,.0f}</td>"
            f"</tr>"
        )

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
<meta charset="utf-8">
<title>فاکتور #{inv_id}</title>
<style>
  body {{ font-family: Tahoma, sans-serif; font-size: 13px; margin: 24px; color: #1a1a1a; }}
  h2   {{ font-size: 16px; margin-bottom: 4px; }}
  .meta {{ color: #555; font-size: 12px; margin-bottom: 16px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border: 1px solid #d0d0d0; padding: 6px 10px; text-align: right; }}
  th {{ background: #f2f2f2; font-weight: bold; }}
  .total-row td {{ font-weight: bold; background: #f9f9f9; }}
</style>
</head>
<body>
  <h2>فاکتور فروش</h2>
  <div class="meta">
    شماره: <b>{inv_id}</b> &nbsp;|&nbsp;
    مشتری: <b>{customer_name}</b> &nbsp;|&nbsp;
    تاریخ: <b>{date_str}</b>
  </div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>نام کالا</th><th>تعداد</th>
        <th>قیمت واحد (ریال)</th><th>جمع (ریال)</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
      <tr class="total-row">
        <td colspan="4" style="text-align:left">جمع کل</td>
        <td>{total:,.0f}</td>
      </tr>
    </tbody>
  </table>
</body>
</html>"""
