# app/services/auth_service.py

import bcrypt

from app.database.connection import get_connection
from app.core.session import Session


def login(username: str, password: str) -> tuple[bool, str]:
    """احراز هویت کاربر؛ خروجی: (موفقیت، پیام)."""
    username = (username or "").strip()
    if not username or not password:
        return False, "نام کاربری و رمز عبور را وارد کنید."

    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()

    if row is None:
        return False, "نام کاربری یا رمز عبور اشتباه است."

    user = dict(row)

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return False, "نام کاربری یا رمز عبور اشتباه است."

    if not user.get("is_active", 1):
        return False, "این حساب کاربری غیرفعال شده است."

    user.pop("password_hash", None)
    Session.current_user = user

    return True, f"خوش آمدید، {user.get('full_name') or username}!"
