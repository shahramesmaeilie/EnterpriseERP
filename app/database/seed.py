import bcrypt

from app.database.connection import get_connection
from app.database.schema import init_db

DEFAULT_PERMISSIONS = [
    ("users.manage", "مدیریت کاربران"),
    ("products.manage", "مدیریت کالاها"),
    ("customers.manage", "مدیریت مشتریان"),
    ("invoices.create", "صدور فاکتور"),
    ("invoices.view", "مشاهده فاکتورها"),
    ("reports.view", "مشاهده گزارش‌ها"),
]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # بعد از اولین ورود حتماً عوض شود
ADMIN_FULL_NAME = "مدیر سیستم"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def seed() -> None:
    init_db()
    conn = get_connection()

    # مجوزهای پایه (تکراری‌ها نادیده گرفته می‌شوند)
    conn.executemany(
        "INSERT OR IGNORE INTO permissions (code, title) VALUES (?, ?)",
        DEFAULT_PERMISSIONS,
    )

    # کاربر admin فقط اگر وجود نداشته باشد ساخته می‌شود
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)
    ).fetchone()

    if row is None:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)",
            (ADMIN_USERNAME, hash_password(ADMIN_PASSWORD), ADMIN_FULL_NAME),
        )
        admin_id = cursor.lastrowid
        print(f"کاربر admin ساخته شد (id={admin_id}).")
    else:
        admin_id = row["id"]
        print("کاربر admin از قبل وجود دارد.")

    # اختصاص همه‌ی مجوزها به admin
    conn.execute(
        """
        INSERT OR IGNORE INTO user_permissions (user_id, permission_id)
        SELECT ?, id FROM permissions
        """,
        (admin_id,),
    )

    conn.commit()
    print("Seed با موفقیت انجام شد.")


if __name__ == "__main__":
    seed()
