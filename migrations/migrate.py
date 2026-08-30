# migrate.py (کنار main.py بساز)
from app.database.connection import get_connection

conn = get_connection()

migrations = [
    "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
    "ALTER TABLE users ADD COLUMN permissions TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE users ADD COLUMN email TEXT",
]

for sql in migrations:
    try:
        conn.execute(sql)
        print(f"OK: {sql[:60]}")
    except Exception as e:
        print(f"SKIP: {e}")

conn.execute("UPDATE users SET role='admin' WHERE username='admin'")
conn.commit()
conn.close()
print("Migration complete.")
