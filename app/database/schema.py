from app.database.connection import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL DEFAULT '',
    email TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS permissions (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,   -- مثل 'users.manage' یا 'sales.create'
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, permission_id)
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    price       REAL NOT NULL DEFAULT 0,
    stock       INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name  TEXT NOT NULL,
    phone      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    total       REAL NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL
);

# CREATE TABLE IF NOT EXISTS employees (
#     id          INTEGER PRIMARY KEY AUTOINCREMENT,
#     first_name  TEXT NOT NULL DEFAULT '',
#     last_name   TEXT NOT NULL DEFAULT '',
#     job_title   TEXT NOT NULL DEFAULT '',
#     salary      REAL NOT NULL DEFAULT 0,
#     hire_date   TEXT NOT NULL DEFAULT '',
#     is_active   INTEGER NOT NULL DEFAULT 1,
#     created_at  TEXT NOT NULL DEFAULT (datetime('now'))
# );

"""


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    print("دیتابیس با موفقیت ساخته شد:", "enterprise.db")


if __name__ == "__main__":
    init_db()
