from pathlib import Path

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox,
)

from app.core.session import Session
from app.ui.pages.users import UsersPage

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "assets" / "images"

MENU_ICONS = {
    "users": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
        </svg>
    """,
    "products": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M20 2H4c-1 0-2 .9-2 2v3.01c0 .72.43 1.34 1 1.69V20c0 1.1 1.1 2 2 2h14c.9 0 2-.9 2-2V8.7c.57-.35 1-.97 1-1.69V4c0-1.1-1-2-2-2zm-5 12H9v-2h6v2zm5-7H4V4h16v3z"/>
        </svg>
    """,
    "customers": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
    """,
    "invoices": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
        </svg>
    """,
    "reports": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
        </svg>
    """,
    "logout": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path fill="{color}" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/>
        </svg>
    """,
}


def create_svg_icon(svg_content, color="#ffffff", size=24):
    svg_data = svg_content.format(color=color).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg_data))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class PlaceholderPage(QWidget):
    """صفحه موقت تا زمان ساخت صفحه واقعی هر بخش."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"بخش «{title}» در مراحل بعدی ساخته می‌شود.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #7a6ba8; font-size: 18px;")
        layout.addWidget(label)


class DashboardWindow(QMainWindow):
    MENU_ITEMS = [
        ("users", "کاربران"),
        ("products", "کالاها"),
        ("customers", "مشتریان"),
        ("invoices", "فاکتورها"),
        ("reports", "گزارش‌ها"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise ERP")
        self.resize(1250, 720)

        ico_path = IMAGE_DIR / "Enterprise.ico"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main_area(), stretch=1)

        self._menu_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    # ---------- سایدبار ----------

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(6)

        app_name = QLabel("Enterprise ERP")
        app_name.setObjectName("appName")
        app_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_name)

        user = Session.current_user or {}
        display_name = (
            f"{user.get('first_name', '') or ''} {user.get('last_name', '') or ''}".strip()
            or user.get("full_name")
            or user.get("username", "")
        )
        user_label = QLabel(display_name)
        user_label.setObjectName("userName")
        user_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_label)
        layout.addSpacing(18)

        self._menu_buttons = []
        for index, (key, title) in enumerate(self.MENU_ITEMS):
            btn = QPushButton(f"  {title}")
            btn.setObjectName("menuButton")
            btn.setIcon(create_svg_icon(MENU_ICONS[key], "#ffffff", 20))
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, i=index: self._switch_page(i)
            )
            layout.addWidget(btn)
            self._menu_buttons.append(btn)

        layout.addStretch()

        logout_btn = QPushButton("  خروج")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setIcon(create_svg_icon(MENU_ICONS["logout"], "#ffd7d7", 20))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7657c8, stop:1 #5a3fa8
                );
            }
            QLabel#appName {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 4px 0;
            }
            QLabel#userName {
                color: #e5ddf8;
                font-size: 13px;
            }
            QPushButton#menuButton {
                color: white;
                background: transparent;
                border: none;
                border-radius: 9px;
                padding: 11px 14px;
                text-align: right;
                font-size: 14px;
            }
            QPushButton#menuButton:hover {
                background: rgba(255, 255, 255, 0.14);
            }
            QPushButton#menuButton:checked {
                background: rgba(255, 255, 255, 0.24);
                font-weight: bold;
            }
            QPushButton#logoutButton {
                color: #ffd7d7;
                background: rgba(0, 0, 0, 0.15);
                border: none;
                border-radius: 9px;
                padding: 11px 14px;
                text-align: right;
                font-size: 14px;
            }
            QPushButton#logoutButton:hover {
                background: rgba(0, 0, 0, 0.28);
            }
        """)
        return sidebar

    # ---------- ناحیه اصلی ----------

    def _build_main_area(self):
        container = QFrame()
        container.setStyleSheet("background: #f5f3ff;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(UsersPage())
        for _, title in self.MENU_ITEMS[1:]:
            self.stack.addWidget(PlaceholderPage(title))

        layout.addWidget(self.stack)
        return container

    def _switch_page(self, index):
        for i, btn in enumerate(self._menu_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def logout(self):
        answer = QMessageBox.question(
            self, "خروج",
            "آیا می‌خواهید از حساب کاربری خارج شوید؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        Session.clear()
        self.close()
        from app.ui.login import LoginWindow
        self._login = LoginWindow()
        self._login.show()
