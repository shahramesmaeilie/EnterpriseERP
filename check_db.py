import sqlite3

conn = sqlite3.connect("enterprise.db")
cur = conn.cursor()

cur.execute("PRAGMA journal_mode;")
print("journal_mode:", cur.fetchone())

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("tables:", tables)

for t in tables:
    table_name = t[0]
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cur.fetchone()[0]
    print(f"  {table_name}: {count} rows")

conn.close()
print("DONE")
