import sqlite3
from app.models.customer import Customer

conn = sqlite3.connect("enterprise.db")
conn.row_factory = sqlite3.Row
cur = conn.execute("SELECT * FROM customers LIMIT 1")
row = cur.fetchone()

assert row is not None, "جدول customers خالی است، یک مشتری نمونه اضافه کن"

customer = Customer.from_row(row)

print("row['full_name'] =", row["full_name"])
print("customer.name    =", customer.name)

assert customer.name == row["full_name"], (
    f"نگاشت اشتباه است: full_name={row['full_name']!r} ولی name={customer.name!r}"
)
print("✅ نگاشت درست است")
