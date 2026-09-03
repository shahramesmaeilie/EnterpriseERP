# -*- coding: utf-8 -*-
import ctypes
from pathlib import Path
import sys

from PySide6.QtCore import QByteArray, QPoint, QRegularExpression, Qt
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QRegularExpressionValidator
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy
)

from app.services.auth_service import login

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "assets" / "images"
ICON_DIR = BASE_DIR / "assets" / "icons"

_EN_US_LAYOUT = "00000409"
_KLF_ACTIVATE = 0x00000001

# کد SVG لوگو با رنگ سفید (Hardcoded)
LOGO_SVG_WHITE = """
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="83" viewBox="0 0 80 83">
<g transform="translate(0.000000,83.000000) scale(0.100000,-0.100000)"
fill="#FFFFFF" stroke="none">
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


def force_english_layout():
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.LoadKeyboardLayoutW(_EN_US_LAYOUT, _KLF_ACTIVATE)
        except Exception:
            pass


def create_white_logo_pixmap(size: int = 160) -> QPixmap:
    """ساخت لوگوی سفید به صورت برنامه‌نویسی شده"""
    renderer = QSvgRenderer(QByteArray(LOGO_SVG_WHITE.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))  # پس‌زمینه شفاف
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class EnglishLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setInputMethodHints(
            Qt.InputMethodHint.ImhLatinOnly
            | Qt.InputMethodHint.ImhNoPredictiveText
        )
        self.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[\x20-\x7E]*"), self)
        )
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def focusInEvent(self, event):
        force_english_layout()
        super().focusInEvent(event)

    def keyPressEvent(self, event):
        force_english_layout()
        super().keyPressEvent(event)


class EnterPushButton(QPushButton):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
        else:
            super().keyPressEvent(event)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise ERP — ورود")
        # قابل تغییر اندازه
        self.setMinimumSize(700, 500)
        self.resize(950, 600)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        ico_path = IMAGE_DIR / "Enterprise.ico"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        self._drag_offset: QPoint | None = None
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        # در RTL: پنل چپ راست، پنل راست چپ
        root.addWidget(left_panel, 45)
        root.addWidget(right_panel, 55)

        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.show_password)
        self.setTabOrder(self.show_password, self.login_button)
        self.username_input.setFocus()

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setMinimumWidth(250)

        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(18, 16, 0, 0)
        top_bar.setSpacing(8)

        btn_font = QFont("Segoe UI", 10, QFont.Weight.Bold)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("ctrlCloseBtn")
        self.close_btn.setFont(btn_font)
        self.close_btn.setFixedSize(32, 28)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.clicked.connect(self.close)
        top_bar.addWidget(self.close_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("ctrlMaxBtn")
        self.max_btn.setFont(btn_font)
        self.max_btn.setFixedSize(32, 28)
        self.max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.max_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.max_btn.clicked.connect(self._toggle_maximize)
        top_bar.addWidget(self.max_btn)

        self.min_btn = QPushButton("–")
        self.min_btn.setObjectName("ctrlMinBtn")
        self.min_btn.setFont(btn_font)
        self.min_btn.setFixedSize(32, 28)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.min_btn.clicked.connect(self.showMinimized)
        top_bar.addWidget(self.min_btn)

        top_bar.addStretch()
        outer_layout.addLayout(top_bar)

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(16)

        # لوگوی سفید (به جای فایل SVG)
        logo = QLabel()
        logo.setPixmap(create_white_logo_pixmap(160))
        logo.setFixedSize(160, 160)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(logo)

        title = QLabel("Enterprise ERP")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        subtitle = QLabel("سامانه یکپارچه مدیریت کسب‌وکار")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        outer_layout.addLayout(center_layout, stretch=1)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("rightPanel")
        panel.setMinimumWidth(320)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setMinimumWidth(300)
        card.setMaximumWidth(380)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        heading = QLabel("ورود به سیستم")
        heading.setObjectName("cardHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        layout.addSpacing(10)

        layout.addWidget(QLabel("نام کاربری"))
        self.username_input = EnglishLineEdit()
        self.username_input.setPlaceholderText("Username")
        user_icon = ICON_DIR / "user.svg"
        if user_icon.exists():
            self.username_input.addAction(
                QIcon(str(user_icon)), QLineEdit.ActionPosition.LeadingPosition
            )
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("رمز عبور"))
        self.password_input = EnglishLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        lock_icon = ICON_DIR / "lock.svg"
        if lock_icon.exists():
            self.password_input.addAction(
                QIcon(str(lock_icon)), QLineEdit.ActionPosition.LeadingPosition
            )
        layout.addWidget(self.password_input)

        self.show_password = QCheckBox("نمایش رمز عبور")
        self.show_password.toggled.connect(self._toggle_password)
        # اعمال فونت و رنگ هماهنگ با لیبل‌های نام کاربری و رمز عبور
        self.show_password.setStyleSheet("""
            QCheckBox {
                color: #4a4458; 
                font-size: 13px;
            }
        """)
        layout.addWidget(self.show_password)

        layout.addSpacing(10)

        self.login_button = EnterPushButton("ورود")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedHeight(42)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_icon = ICON_DIR / "login.svg"
        if login_icon.exists():
            self.login_button.setIcon(QIcon(str(login_icon)))
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        layout.addStretch()

        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        center.addWidget(card)
        outer.addLayout(center, stretch=1)

        return panel

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _toggle_password(self, checked: bool):
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "خطا", "لطفاً نام کاربری و رمز عبور را وارد کنید.")
            return

        success, message = login(username, password)

        if not success:
            QMessageBox.warning(self, "خطا در ورود", message)
            return

        self.open_dashboard()

    def open_dashboard(self):
        from app.ui.dashboard import Dashboard

        self.dashboard = Dashboard()
        self.dashboard.showMaximized()
        self.close()