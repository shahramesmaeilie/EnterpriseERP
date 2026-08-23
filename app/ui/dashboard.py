# -*- coding: utf-8 -*-
"""app/ui/dashboard.py — داشبورد اصلی Enterprise ERP"""

from pathlib import Path

from PySide6.QtCore import Qt, QSize, QByteArray, QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QButtonGroup, QFrame, QSizePolicy,
)

from app.core.session import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGO_SVG = PROJECT_ROOT / "Enterprise.svg"

# ---------------------------------------------------------------- SVG icons
_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">{}</svg>'
)

ICONS = {
    "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
            '<polyline points="9 22 9 12 15 12 15 22"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
             '<circle cx="9" cy="7" r="4"/>'
             '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>'
             '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "inventory": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4'
                 'A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4'
                 'A2 2 0 0 0 21 16z"/>'
                 '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
                 '<line x1="12" y1="22.08" x2="12" y2="12"/>',
    "sales": '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>'
             '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 '
             '2-1.61L23 6H6"/>',
    "reports": '<line x1="12" y1="20" x2="12" y2="10"/>'
               '<line x1="18" y1="20" x2="18" y2="4"/>'
               '<line x1="6" y1="20" x2="6" y2="16"/>',
    "settings": '<circle cx="12" cy="12" r="3"/>'
                '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 '
                '0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 '
                '1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09'
                'A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 '
                '0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 '
                '.33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 '
                '2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82'
                'l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 '
                '1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 '
                '2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 '
                '0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06'
                '.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 '
                '2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
              '<polyline points="16 17 21 12 16 7"/>'
              '<line x1="21" y1="12" x2="9" y2="12"/>',
    "close": '<line x1="18" y1="6" x2="6" y2="18"/>'
             '<line x1="6" y1="6" x2="18" y2="18"/>',
    "minimize": '<line x1="5" y1="12" x2="19" y2="12"/>',
    "maximize": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
}


def create_svg_icon(svg_str: str, color: str = "#ffffff", size: int = 24) -> QIcon:
    """رندر SVG درون‌کد با رنگ دلخواه به QIcon."""
    svg = _SVG_TEMPLATE.format(svg_str).replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------- Dashboard
class Dashboard(QWidget):
    """داشبورد اصلی با کنترل دسترسی مبتنی بر نقش و permissions."""

    # (کلید، عنوان فارسی، نام آیکون)
    MENU_ITEMS = [
        ("home",      "داشبورد",         "home"),
        ("users",     "مدیریت کاربران",  "users"),
        ("inventory", "انبار و کالا",     "inventory"),
        ("sales",     "فروش",            "sales"),
        ("reports",   "گزارش‌ها",        "reports"),
        ("settings",  "تنظیمات",         "settings"),
    ]

    # نگاشت نام‌های قدیمی ذخیره‌شده در دیتابیس به کلیدهای واقعی منو
    _PERMISSION_ALIASES = {
        "products":  "inventory",
        "customers": "sales",
        "invoices":  "sales",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise ERP")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1200, 720)
        self._drag_pos = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame(objectName="mainContainer")
        outer.addWidget(self.container)

        root = QVBoxLayout(self.container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        self.stack = QStackedWidget(objectName="contentStack")
        body.addWidget(self._build_sidebar())
        body.addWidget(self.stack, 1)

        self._apply_styles()

    # ------------------------------------------------------------ کاربر جاری
    def _current_user(self) -> dict:
        return Session.current_user or {}

    def _display_name(self) -> str:
        user = self._current_user()
        full = (user.get("full_name") or "").strip()
        if full:
            return full
        first = (user.get("first_name") or "").strip()
        last = (user.get("last_name") or "").strip()
        if first or last:
            return f"{first} {last}".strip()
        return user.get("username") or "کاربر"

    def _role(self) -> str:
        return (self._current_user().get("role") or "user").lower()

    # ------------------------------------------------------------ دسترسی‌ها
    def _permissions(self) -> set[str]:
        """permissions کاربر با اعمال alias برای نام‌های قدیمی دیتابیس."""
        raw = self._current_user().get("permissions") or ""
        perms = {p.strip() for p in raw.split(",") if p.strip()}
        return {self._PERMISSION_ALIASES.get(p, p) for p in perms}

    def has_access(self, key: str) -> bool:
        if key == "home":
            return True
        if self._role() == "admin":
            return True
        return key in self._permissions()

    # ------------------------------------------------------------ header
    def _build_header(self) -> QFrame:
        header = QFrame(objectName="header")
        header.setFixedHeight(58)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(10)

        if LOGO_SVG.exists():
            logo = QLabel()
            logo.setPixmap(QIcon(str(LOGO_SVG)).pixmap(QSize(36, 36)))
            lay.addWidget(logo)

        title = QLabel("Enterprise ERP", objectName="appTitle")
        lay.addWidget(title)
        lay.addStretch(1)

        role_fa = "مدیر سیستم" if self._role() == "admin" else "کاربر"
        user_lbl = QLabel(f"{self._display_name()}  |  {role_fa}",
                          objectName="userLabel")
        lay.addWidget(user_lbl)

        for name, slot in (("minimize", self.showMinimized),
                           ("maximize", self._toggle_maximize),
                           ("close", self.close)):
            btn = QPushButton(objectName="winBtn")
            btn.setProperty("kind", name)
            btn.setIcon(create_svg_icon(ICONS[name], "#4d3a78", 16))
            btn.setFixedSize(34, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        return header

    def _toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(230)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 18, 12, 18)
        lay.setSpacing(8)

        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)

        # فقط آیتم‌های مجاز ساخته می‌شوند تا اندیس دکمه و صفحه هماهنگ بماند
        for key, label, icon in self.MENU_ITEMS:
            if not self.has_access(key):
                continue
            index = self.stack.count()
            self.stack.addWidget(self._create_page(key, label))

            btn = QPushButton(f"  {label}", objectName="menuBtn")
            btn.setIcon(create_svg_icon(ICONS[icon], "#ffffff", 20))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _=False, i=index: self.stack.setCurrentIndex(i))
            self.menu_group.addButton(btn)
            lay.addWidget(btn)

        if self.menu_group.buttons():
            self.menu_group.buttons()[0].setChecked(True)
            self.stack.setCurrentIndex(0)

        lay.addStretch(1)

        logout = QPushButton("  خروج از حساب", objectName="logoutBtn")
        logout.setIcon(create_svg_icon(ICONS["logout"], "#ffffff", 20))
        logout.setIconSize(QSize(20, 20))
        logout.setCursor(Qt.PointingHandCursor)
        logout.clicked.connect(self._logout)
        lay.addWidget(logout)

        return sidebar

    # ------------------------------------------------------------ صفحات
    def _create_page(self, key: str, label: str) -> QWidget:
        if key == "users":
            try:
                from app.ui.pages.users import UsersPage  # import محلی برای جلوگیری از circular import
                return UsersPage()
            except ImportError as exc:
                return self._placeholder(f"خطا در بارگذاری صفحه کاربران:\n{exc}")
        if key == "home":
            return self._placeholder(
                f"خوش آمدید، {self._display_name()} عزیز!\n"
                "از منوی کنار برای دسترسی به بخش‌های سیستم استفاده کنید."
            )
        return self._placeholder(f"صفحه «{label}» هنوز آماده نشده است.")

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lbl = QLabel(text, objectName="placeholderLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        return page

    # ------------------------------------------------------------ logout
    def _logout(self):
        Session.current_user = None
        from app.ui.login import LoginWindow  # import محلی برای جلوگیری از circular import
        self._login = LoginWindow()
        self._login.show()
        self.close()

    # ------------------------------------------------------------ drag پنجره
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() <= 58:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------ استایل
    def _apply_styles(self):
        self.setStyleSheet("""
            #mainContainer {
                background-color: #faf8ff;
                border-radius: 18px;
            }
            #header {
                background-color: #faf8ff;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid #e6e0f5;
            }
            #appTitle {
                color: #4d3a78;
                font-size: 16px;
                font-weight: bold;
            }
            #userLabel {
                color: #7657c8;
                font-size: 13px;
                margin-left: 8px;
            }
            #winBtn {
                background-color: #efeaf9;
                border: none;
                border-radius: 8px;
                border-bottom: 2px solid #d5cbee;
            }
            #winBtn:hover {
                margin-top: -3px;
                border-bottom: 3px solid #b9a8e3;
                background-color: #e4dbf6;
            }
            #winBtn[kind="close"]:hover {
                background-color: #f8d7da;
                border-bottom: 3px solid #b71c1c;
            }
            #sidebar {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7657c8, stop:1 #4d3a78);
                border-bottom-right-radius: 18px;
            }
            #menuBtn {
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.18);
            }
            #menuBtn:hover {
                margin-top: -4px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.28);
                background-color: rgba(255, 255, 255, 0.16);
            }
            #menuBtn:checked {
                background-color: rgba(255, 255, 255, 0.26);
                border-bottom: 4px solid rgba(0, 0, 0, 0.32);
                font-weight: bold;
            }
            #logoutBtn {
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #d32f2f;
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid #8e1b1b;
            }
            #logoutBtn:hover {
                margin-top: -4px;
                border-bottom: 4px solid #b71c1c;
                background-color: #e53935;
            }
            #contentStack {
                background-color: #faf8ff;
                border-bottom-left-radius: 18px;
            }
            #placeholderLabel {
                color: #4d3a78;
                font-size: 17px;
            }
        """)
