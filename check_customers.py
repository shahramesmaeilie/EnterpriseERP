import sqlite3
c = sqlite3.connect("enterprise.db")
try:
    n = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    rows = c.execute("SELECT id, full_name, phone FROM customers").fetchall()
    print("row count:", n)
    print("rows:", rows)
finally:
    c.close()
