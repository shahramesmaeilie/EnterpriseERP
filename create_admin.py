from app.database.connection import DATABASE_PATH, get_connection
from app.services.auth_service import hash_password


def ensure_users_table() -> None:
    """
    ایجاد جدول کاربران در صورت نبودن آن.
    """

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                fullname TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()


def create_or_update_admin() -> None:
    """
    ایجاد یا بازنشانی کاربر مدیر اولیه.

    username: admin
    password: admin123
    """

    username = "admin"
    plain_password = "admin123"
    fullname = "مدیر سیستم"
    role = "admin"
    is_active = 1

    # ابتدا ساختار دیتابیس را تضمین می‌کنیم.
    ensure_users_table()

    # هش امن PBKDF2-SHA256؛ رمز ساده در دیتابیس ذخیره نخواهد شد.
    hashed_password = hash_password(plain_password)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            LIMIT 1;
            """,
            (username,),
        )

        existing_user = cursor.fetchone()

        if existing_user is None:
            cursor.execute(
                """
                INSERT INTO users (
                    username,
                    password,
                    fullname,
                    role,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    username,
                    hashed_password,
                    fullname,
                    role,
                    is_active,
                ),
            )

            result_message = "کاربر مدیر با موفقیت ایجاد شد."

        else:
            cursor.execute(
                """
                UPDATE users
                SET
                    password = ?,
                    fullname = ?,
                    role = ?,
                    is_active = ?
                WHERE username = ?;
                """,
                (
                    hashed_password,
                    fullname,
                    role,
                    is_active,
                    username,
                ),
            )

            result_message = (
                "کاربر admin از قبل وجود داشت؛ "
                "رمز عبور و اطلاعات آن به‌روزرسانی شد."
            )

        connection.commit()

    print("=" * 55)
    print(result_message)
    print(f"مسیر دیتابیس فعال: {DATABASE_PATH}")
    print("نام کاربری: admin")
    print("رمز عبور: admin123")
    print("=" * 55)


if __name__ == "__main__":
    try:
        create_or_update_admin()

    except Exception as error:
        print(f"خطا در ایجاد کاربر مدیر: {error}")
