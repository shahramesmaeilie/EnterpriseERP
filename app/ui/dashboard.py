# -*- coding: utf-8 -*-
"""app/ui/dashboard.py — داشبورد اصلی Enterprise ERP (Responsive & Resizable)"""

from pathlib import Path
from typing import Optional, Set

from PySide6.QtCore import Qt, QSize, QByteArray, QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QButtonGroup, QFrame, QSizePolicy, QScrollArea,
    QGridLayout
)

from app.core.session import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGO_SVG = PROJECT_ROOT / "Enterprise.svg"

# ================================================================ SVG ICONS
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
    "accounting": '<rect x="3" y="3" width="18" height="18" rx="2"/>'
                  '<line x1="8" y1="8" x2="16" y2="16"/>'
                  '<line x1="16" y1="8" x2="8" y2="16"/>'
}

# ================================================================ MAIN LOGO
_MAIN_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="83" viewBox="0 0 80 83">
<g transform="translate(0.000000,83.000000) scale(0.100000,-0.100000)" fill="#4d3a78" stroke="none">
<path d="M305 731 c-16 -10 -74 -44 -128 -76 l-99 -57 51 -29 50 -29 88 53
c93 56 104 73 89 133 -8 29 -12 29 -51 5z"/>
<path d="M452 738 c-7 -7 -12 -29 -12 -49 0 -37 2 -39 94 -93 l94 -56 46 26
c41 23 59 44 38 44 -4 0 -61 32 -126 70 -64 39 -119 70 -120 70 -1 0 -7 -5
-14 -12z"/>
<path d="M323 538 c-40 -23 -70 -45 -67 -49 2 -4 36 -26 75 -48 l71 -41 74 42
c41 23 74 45 74 48 0 8 -136 90 -147 90 -4 0 -40 -19 -80 -42z"/>
<path d="M54 557 c-2 -7 -3 -76 -2 -152 3 -130 4 -140 23 -144 10 -2 34 5 52
14 l33 18 0 95 0 94 25 -16 c24 -15 25 -15 25 2 0 12 -24 33 -70 60 -79 47
-79 47 -86 29z"/>
<path d="M665 527 c-40 -25 -71 -50 -73 -61 -4 -19 -3 -19 22 -3 l25 17 3 -92
c3 -92 3 -92 35 -111 20 -11 41 -16 53 -12 19 6 20 14 20 150 0 79 -4 146 -8
149 -4 2 -39 -14 -77 -37z"/>
<path d="M240 376 l0 -85 68 -41 c38 -22 71 -40 75 -40 4 0 7 37 7 83 l0 83
-67 39 c-38 22 -71 42 -75 43 -5 2 -8 -35 -8 -82z"/>
<path d="M488 419 l-68 -40 0 -84 c0 -47 3 -85 6 -85 10 0 128 74 136 85 10
13 10 165 1 165 -5 -1 -38 -19 -75 -41z"/>
<path d="M153 203 c-24 -13 -43 -28 -43 -31 0 -11 263 -171 272 -166 4 3 8 29
8 58 l0 54 -93 56 c-51 31 -95 56 -97 55 -3 -1 -24 -12 -47 -26z"/>
<path d="M510 176 l-85 -53 -3 -62 -3 -62 34 18 c59 32 247 148 247 153 0 5
-94 60 -101 60 -2 -1 -42 -25 -89 -54z"/>
</g>
</svg>
"""


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


def create_logo_icon(size: int = 40) -> QIcon:
    """ساخت آیکون لوگوی اصلی با رنگ بنفش برای هدر."""
    renderer = QSvgRenderer(QByteArray(_MAIN_LOGO_SVG.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ================================================================ DASHBOARD
class Dashboard(QWidget):
    """داشبورد اصلی با قابلیت تغییر اندازه، اسکرول و واکنش‌گرا"""

    MENU_ITEMS = [
        ("home", "🏠 داشبورد", "home"),
        ("users", "👥 مدیریت کاربران", "users"),
        ("inventory", "📦 انبار و کالا", "inventory"),
        ("purchases", "🛒 خرید / ورود انبار", "inventory"),
        ("sales", "💰 فروش", "sales"),
        ("accounting", "💹 حسابداری", "accounting"),
        ("reports", "📊 گزارش‌ها", "reports"),
        ("settings", "⚙️ تنظیمات", "settings"),
    ]

    _PERMISSION_ALIASES = {
        "products": "inventory",
        "customers": "sales",
        "invoices": "sales",
        "purchases": "inventory",
        "accounting": "accounting",
    }

    def __init__(self, current_user_id: Optional[int] = None):
        super().__init__()
        self._current_user_id = current_user_id
        self._drag_pos: Optional[QPoint] = None
        self._login = None
        self._page_cache: dict = {}
        self._current_page_key: str = "home"

        # قابل تغییر اندازه
        self.setMinimumSize(800, 600)
        self.resize(1200, 720)

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        self._select_first_page()

    # ============================================================ UI SETUP (Responsive)
    def _setup_ui(self) -> None:
        self.setWindowTitle("Enterprise ERP")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)

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
        
        # در RTL: سایدبار سمت راست، محتوا سمت چپ
        body.addWidget(self._build_sidebar(), 0)  # سایدبار با عرض انعطاف‌پذیر
        body.addWidget(self.stack, 1)              # فضای باقی‌مانده

    def _connect_signals(self) -> None:
        pass

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

    def _permissions(self) -> Set[str]:
        raw = self._current_user().get("permissions") or ""
        perms = {p.strip() for p in raw.split(",") if p.strip()}
        return {self._PERMISSION_ALIASES.get(p, p) for p in perms}

    def has_access(self, key: str) -> bool:
        if key == "home":
            return True
        if self._role() == "admin":
            return True
        return key in self._permissions()

    # ============================================================ HEADER
    def _build_header(self) -> QFrame:
        header = QFrame(objectName="header")
        header.setFixedHeight(58)

        lay = QHBoxLayout(header)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(10)

        logo_label = QLabel()
        logo_label.setPixmap(create_logo_icon(40).pixmap(QSize(40, 40)))
        logo_label.setFixedSize(40, 40)
        logo_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo_label)

        # title = QLabel("Enterprise ERP", objectName="appTitle")
        # lay.addWidget(title)
        # lay.addStretch(1)

        role_fa = "مدیر سیستم" if self._role() == "admin" else "کاربر"
        user_lbl = QLabel(f"{self._display_name()}  |  {role_fa}",
                          objectName="userLabel")
        lay.addWidget(user_lbl)

        window_buttons = [
            ("minimize", self.showMinimized),
            ("maximize", self._toggle_maximize),
            ("close", self.close),
        ]
        for name, slot in window_buttons:
            btn = QPushButton(objectName="winBtn")
            btn.setProperty("kind", name)
            btn.setIcon(create_svg_icon(ICONS[name], "#4d3a78", 16))
            btn.setFixedSize(34, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        return header

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ============================================================ SIDEBAR (Responsive)
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(objectName="sidebar")
        # سایدبار انعطاف‌پذیر با حداقل و حداکثر عرض
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(280)
        sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 18, 12, 18)
        lay.setSpacing(8)

        self.menu_group = QButtonGroup(self)
        self.menu_group.setExclusive(True)

        for key, label, icon_key in self.MENU_ITEMS:
            if not self.has_access(key):
                continue

            page = self._create_page(key, label)
            index = self.stack.addWidget(page)
            self._page_cache[key] = page

            btn = QPushButton(f"  {label}", objectName="menuBtn")
            btn.setIcon(create_svg_icon(ICONS[icon_key], "#ffffff", 20))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(
                lambda checked=False, idx=index, k=key: self._on_menu_clicked(idx, k)
            )
            self.menu_group.addButton(btn)
            lay.addWidget(btn)

        lay.addStretch(1)
        lay.addSpacing(20)

        logout = QPushButton("  🚪 خروج از حساب", objectName="logoutBtn")
        logout.setIcon(create_svg_icon(ICONS["logout"], "#ffffff", 20))
        logout.setIconSize(QSize(20, 20))
        logout.setCursor(Qt.PointingHandCursor)
        logout.clicked.connect(self._logout)
        lay.addWidget(logout)

        self._connect_page_signals()
        return sidebar

    def _on_menu_clicked(self, index: int, key: str) -> None:
        self.stack.setCurrentIndex(index)
        self._current_page_key = key

    def _select_first_page(self) -> None:
        if self.menu_group.buttons():
            self.menu_group.buttons()[0].setChecked(True)

    def _connect_page_signals(self) -> None:
        purchases_page = self._page_cache.get("purchases")
        inventory_page = self._page_cache.get("inventory")
        sales_page = self._page_cache.get("sales")

        if purchases_page and inventory_page:
            if hasattr(purchases_page, "inventory_updated") and hasattr(inventory_page, "refresh"):
                try:
                    purchases_page.inventory_updated.connect(inventory_page.refresh)
                except Exception:
                    pass

        if sales_page and inventory_page:
            if hasattr(sales_page, "inventory_updated") and hasattr(inventory_page, "refresh"):
                try:
                    sales_page.inventory_updated.connect(inventory_page.refresh)
                except Exception:
                    pass

            if hasattr(sales_page, "data_changed"):
                try:
                    sales_page.data_changed.connect(self._on_dashboard_data_changed)
                except Exception:
                    pass

        if purchases_page and hasattr(purchases_page, "data_changed"):
            try:
                purchases_page.data_changed.connect(self._on_dashboard_data_changed)
            except Exception:
                pass

    # ============================================================ PAGES (Responsive & Scrollable)
    def _create_page(self, key: str, label: str) -> QWidget:
        """ساخت صفحه با قابلیت اسکرول (Responsive)"""
        try:
            if key == "home":
                return self._create_home_page()

            if key == "users":
                from app.ui.pages.users import UsersPage
                return self._wrap_in_scroll(UsersPage())

            if key == "inventory":
                from app.ui.pages.inventory import InventoryPage
                return self._wrap_in_scroll(InventoryPage())

            if key == "purchases":
                from app.ui.pages.purchases import PurchasesPage
                return self._wrap_in_scroll(PurchasesPage())

            if key == "sales":
                from app.ui.pages.sales import SalesPage
                return self._wrap_in_scroll(SalesPage(current_user_id=self._current_user_id))

            if key == "accounting":
                from app.ui.pages.accounting import AccountingPage
                return self._wrap_in_scroll(AccountingPage())

            if key == "reports":
                from app.ui.pages.reports import ReportsPage
                return self._wrap_in_scroll(ReportsPage())

            if key == "settings":
                from app.ui.pages.settings import SettingsPage
                return self._wrap_in_scroll(SettingsPage())

        except ImportError as exc:
            return self._placeholder(f"❌ خطا در بارگذاری صفحه {label}:\n{exc}")
        except Exception as exc:
            return self._placeholder(f"❌ خطای غیرمنتظره در صفحه {label}:\n{exc}")

        return self._placeholder(f"📄 صفحه «{label}» هنوز آماده نشده است.")

    def _wrap_in_scroll(self, widget: QWidget) -> QScrollArea:
        """قرار دادن هر صفحه در QScrollArea برای واکنش‌گرایی و اسکرول"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(widget)
        return scroll

    def _create_home_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("homePage")

        lay = QVBoxLayout(page)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)

        welcome = QLabel(
            f"🌟 خوش آمدید، {self._display_name()} عزیز!\n\n"
            "از منوی کنار برای دسترسی به بخش‌های سیستم استفاده کنید.\n"
            "📊 برای مشاهده گزارش‌ها و آمار به بخش «گزارش‌ها» مراجعه کنید.",
            objectName="welcomeLabel"
        )
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setWordWrap(True)
        lay.addWidget(welcome)

        # آمار سریع با QGridLayout واکنش‌گرا
        stats_frame = QFrame(objectName="statsFrame")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)

        stats_data = self._get_quick_stats()
        for i, (title, value, icon, color) in enumerate(stats_data):
            card = self._create_quick_stat_card(icon, title, value, color)
            stats_layout.addWidget(card, i // 2, i % 2)  # دو ستون

        lay.addWidget(stats_frame)
        lay.addStretch()

        return page

    def _get_quick_stats(self) -> list:
        try:
            from app.database.connection import get_connection
            with get_connection() as conn:
                products = conn.execute("SELECT COUNT(*) as count FROM products").fetchone()
                product_count = products["count"] if products else 0

                customers = conn.execute("SELECT COUNT(*) as count FROM customers").fetchone()
                customer_count = customers["count"] if customers else 0

                invoices = conn.execute("SELECT COUNT(*) as count FROM invoices").fetchone()
                invoice_count = invoices["count"] if invoices else 0

                sales = conn.execute("SELECT COALESCE(SUM(total), 0) as total FROM invoices").fetchone()
                total_sales = sales["total"] if sales else 0

                return [
                    ("📦", "کل کالاها", str(product_count), "#5b3ec8"),
                    ("👥", "مشتریان", str(customer_count), "#2e7d32"),
                    ("📄", "فاکتورها", str(invoice_count), "#c62828"),
                    ("💰", "کل فروش", f"{total_sales:,.0f}", "#e65100"),
                ]
        except Exception:
            return [
                ("📦", "کل کالاها", "۰", "#5b3ec8"),
                ("👥", "مشتریان", "۰", "#2e7d32"),
                ("📄", "فاکتورها", "۰", "#c62828"),
                ("💰", "کل فروش", "۰", "#e65100"),
            ]

    def _create_quick_stat_card(self, icon: str, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("quickStatCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card.setMinimumSize(140, 90)
        card.setStyleSheet(f"""
            #quickStatCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f6ff);
                border: 2px solid {color}33;
                border-radius: 16px;
                padding: 16px;
            }}
            #quickStatCard:hover {{
                border-color: {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 24px;")

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("color: #1a1a2e; font-size: 20px; font-weight: bold;")

        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)

        return card

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lbl = QLabel(text, objectName="placeholderLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        return page

    # ============================================================ DATA UPDATES
    def _on_dashboard_data_changed(self) -> None:
        self._refresh_inventory_page()
        self._refresh_home_page_stats()

    def _refresh_inventory_page(self) -> None:
        inventory_page = self._page_cache.get("inventory")
        if inventory_page and hasattr(inventory_page, "refresh"):
            try:
                inventory_page.refresh()
            except Exception:
                pass

    def _refresh_home_page_stats(self) -> None:
        home_page = self._page_cache.get("home")
        if home_page and hasattr(home_page, "reload_stats"):
            try:
                home_page.reload_stats()
            except Exception:
                pass

    def refresh_current_page(self) -> None:
        current_page = self.stack.currentWidget()
        if current_page and hasattr(current_page, "refresh"):
            try:
                current_page.refresh()
            except Exception:
                pass

    # ============================================================ LOGOUT
    def _logout(self) -> None:
        Session.current_user = None
        from app.ui.login import LoginWindow
        self._login = LoginWindow()
        self._login.show()
        self.close()

    # ============================================================ WINDOW DRAG
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

    # ============================================================ STYLES
    def _apply_styles(self) -> None:
        pass