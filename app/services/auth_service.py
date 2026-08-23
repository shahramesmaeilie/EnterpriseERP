import bcrypt

from app.core.session import Session
from app.database.connection import get_connection


def login(username: str, password: str) -> tuple[bool, str]:
    """بررسی نام کاربری و رمز عبور؛ در صورت موفقیت کاربر در Session قرار می‌گیرد."""
    username = (username or "").strip()
    if not username or not password:
        return False, "نام کاربری و رمز عبور را وارد کنید."

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False, "نام کاربری یا رمز عبور اشتباه است."

    user = dict(row)

    if not user.get("is_active", 1):
        return False, "این حساب کاربری غیرفعال است."

    password_hash = user.get("password_hash") or ""
    try:
        ok = bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        # هش نامعتبر یا قدیمی در دیتابیس
        return False, "خطا در بررسی رمز عبور. با مدیر سیستم تماس بگیرید."

    if not ok:
        return False, "نام کاربری یا رمز عبور اشتباه است."

    # رمز هش‌شده نباید در Session نگه داشته شود
    user.pop("password_hash", None)
    Session.current_user = user

    return True, "ورود موفقیت‌آمیز بود."


def logout() -> None:
    """خروج کاربر جاری و پاک‌سازی Session."""
    Session.clear()
