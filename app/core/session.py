"""
وضعیت نشست جاری برنامه (کاربر لاگین‌شده).

سازگار با dashboard.py:
  - خط ۱۴  : from app.core.session import Session
  - خط ۱۳۶ : Session.current_user or {}      (خواندن)
  - خط ۳۱۰ : Session.current_user = None     (انتساب مستقیم در _logout)

کلیدهایی که dashboard.py می‌خواند: full_name، role، permissions
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable


class _SessionMeta(type):
    """
    انتساب مستقیم (Session.current_user = ...) را هم به listenerها اطلاع می‌دهد،
    چون dashboard.py در خط ۳۱۰ بدون فراخوانی logout() مقدار را None می‌کند.
    """

    def __setattr__(cls, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name == "current_user":
            if value is None:
                super().__setattr__("login_time", None)
            cls._notify()


class Session(metaclass=_SessionMeta):
    """
    نگهدارنده‌ی حالت در سطح کلاس (اپلیکیشن دسکتاپ تک‌پروسه‌ای).
    current_user یک dict است یا None.
    """

    current_user: dict[str, Any] | None = None
    login_time: datetime | None = None

    _listeners: list[Callable[[dict[str, Any] | None], None]] = []

    # ---------- چرخه‌ی حیات ----------

    @classmethod
    def login(cls, user: dict[str, Any]) -> None:
        # login_time اول ست می‌شود تا listenerها آن را کامل ببینند
        type(cls).__setattr__(cls, "login_time", datetime.now())
        cls.current_user = dict(user)   # _notify از طریق metaclass

    @classmethod
    def logout(cls) -> None:
        cls.current_user = None         # login_time و _notify خودکار

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls.current_user is not None

    # ---------- دسترسی راحت ----------

    @classmethod
    def user_id(cls) -> int | None:
        return (cls.current_user or {}).get("id")

    @classmethod
    def username(cls) -> str:
        u = cls.current_user or {}
        return (u.get("username") or u.get("full_name") or "").strip()

    @classmethod
    def display_name(cls) -> str:
        u = cls.current_user or {}
        return (u.get("full_name") or u.get("username") or "کاربر").strip()

    @classmethod
    def role(cls) -> str:
        return ((cls.current_user or {}).get("role") or "user").lower()

    @classmethod
    def has_role(cls, *roles: str) -> bool:
        """بررسی نقش؛ admin همیشه مجاز است."""
        r = cls.role()
        return r == "admin" or r in roles

    @classmethod
    def permissions(cls) -> set[str]:
        """permissions به‌صورت CSV ذخیره شده — همان تجزیه‌ای که dashboard.py خط ۱۵۵ می‌کند."""
        raw = (cls.current_user or {}).get("permissions") or ""
        return {p.strip() for p in raw.split(",") if p.strip()}

    @classmethod
    def has_permission(cls, perm: str) -> bool:
        return cls.role() == "admin" or perm in cls.permissions()

    # ---------- اطلاع‌رسانی به UI ----------

    @classmethod
    def subscribe(cls, cb: Callable[[dict[str, Any] | None], None]) -> None:
        """اتصال callback برای بروزرسانی هدر/منو هنگام تغییر کاربر."""
        if cb not in cls._listeners:
            cls._listeners.append(cb)

    @classmethod
    def unsubscribe(cls, cb: Callable[[dict[str, Any] | None], None]) -> None:
        if cb in cls._listeners:
            cls._listeners.remove(cb)

    @classmethod
    def _notify(cls) -> None:
        for cb in list(cls._listeners):
            try:
                cb(cls.current_user)
            except Exception:
                pass    # یک listener خراب نباید نشست را بشکند
