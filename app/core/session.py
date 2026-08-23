# app/core/session.py


class Session:
    """نگهداری وضعیت کاربر واردشده در طول اجرای برنامه."""

    current_user: dict | None = None

    @classmethod
    def clear(cls):
        cls.current_user = None
