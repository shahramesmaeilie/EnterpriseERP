import sqlite3
c = sqlite3.connect("enterprise.db")
c.execute("INSERT INTO customers (full_name, phone) VALUES (?, ?)", ("علی رضایی", "09120000000"))
c.commit()
print(c.execute("SELECT id, full_name, phone FROM customers").fetchall())
c.close()
