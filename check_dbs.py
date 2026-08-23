import sqlite3
from pathlib import Path

paths = [
    Path("enterprise.db"),
    Path("app/database/enterprise.db"),
    Path("data/enterprise.db"),
]

for p in paths:
    print("=" * 60)
    print(p, "-", p.stat().st_size, "bytes")
    conn = sqlite3.connect(p)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )]
    print("tables:", tables)
    if "users" in tables:
        for row in conn.execute("SELECT id, username, role FROM users"):
            print("  user:", dict(zip(["id", "username", "role"], row)))
    conn.close()
