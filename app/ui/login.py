import ctypes
from pathlib import Path
import sys

from PySide6.QtCore import QPoint, QRegularExpression, Qt
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator
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
)

from app.services.auth_service import login

# -----------------------------------------------------------------------------
# مسیرها و ثوابت
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "assets" / "images"
ICON_DIR = BASE_DIR / "assets" / "icons"

_EN_US_LAYOUT = "00000409"
_KLF_ACTIVATE = 0x00000001


def force_english_layout():
    """چیدمان صفحه‌کلید را به انگلیسی (US) برمی‌گرداند — فقط در ویندوز."""
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.LoadKeyboardLayoutW(_EN_US_LAYOUT, _KLF_ACTIVATE)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# ویجت‌های سفارشی
# -----------------------------------------------------------------------------
class EnglishLineEdit(QLineEdit):
    """فیلد ورودی که فقط کاراکترهای انگلیسی/ASCII می‌پذیرد."""

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
    """دکمه‌ای که علاوه بر کلیک، با کلید Enter نیز فعال می‌شود."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
        else:
            super().keyPressEvent(event)


# -----------------------------------------------------------------------------
# پنجره لاگین
# -----------------------------------------------------------------------------
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise ERP — ورود")
        self.setFixedSize(950, 600)

        # پنجره بدون قاب با پس‌زمینه شفاف
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        ico_path = IMAGE_DIR / "Enterprise.ico"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        self._drag_offset: QPoint | None = None
        self._build_ui()

    # ---------- ساخت رابط کاربری ----------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_panel(), stretch=1)
        root.addWidget(self._build_right_panel(), stretch=1)

        self.setStyleSheet(self._stylesheet())

        # ترتیب فوکوس و فوکوس اولیه
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.show_password)
        self.setTabOrder(self.show_password, self.login_button)
        self.username_input.setFocus()

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("leftPanel")

        outer_layout = QVBoxLayout(panel)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # --- نوار دکمه‌های کنترل پنجره در بالا-چپ ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(18, 16, 0, 0)
        top_bar.setSpacing(8)

        btn_font = QFont("Segoe UI", 10, QFont.Weight.Bold)

        # ۱. دکمه بستن (✕)
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("ctrlCloseBtn")
        self.close_btn.setFont(btn_font)
        self.close_btn.setFixedSize(32, 28)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.clicked.connect(self.close)
        top_bar.addWidget(self.close_btn)

        # ۲. دکمه تغییر اندازه پنجره (□)
        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("ctrlMaxBtn")
        self.max_btn.setFont(btn_font)
        self.max_btn.setFixedSize(32, 28)
        self.max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.max_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.max_btn.clicked.connect(self._toggle_maximize)
        top_bar.addWidget(self.max_btn)

        # ۳. دکمه کوچک‌کردن / Minimize (–)
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

        # --- بخش میانی (لوگو و متون) ---
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(16)

        # لوگوی SVG
        svg_path = IMAGE_DIR / "Enterprise.svg"
        if svg_path.exists():
            logo = QSvgWidget(str(svg_path))
            logo.setObjectName("appLogo")
            logo.setFixedSize(160, 160)
            center_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # عنوان برنامه
        title = QLabel("Enterprise ERP")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        # زیرعنوان فارسی
        subtitle = QLabel("سامانه یکپارچه مدیریت کسب‌وکار")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        outer_layout.addLayout(center_layout, stretch=1)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("rightPanel")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # کارت فرم ورود
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedSize(360, 440)
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        heading = QLabel("ورود به سیستم")
        heading.setObjectName("cardHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        layout.addSpacing(10)

        # نام کاربری
        layout.addWidget(QLabel("نام کاربری"))
        self.username_input = EnglishLineEdit()
        self.username_input.setPlaceholderText("Username")
        user_icon = ICON_DIR / "user.svg"
        if user_icon.exists():
            self.username_input.addAction(
                QIcon(str(user_icon)), QLineEdit.ActionPosition.LeadingPosition
            )
        layout.addWidget(self.username_input)

        # رمز عبور
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

        # نمایش رمز
        self.show_password = QCheckBox("نمایش رمز عبور")
        self.show_password.toggled.connect(self._toggle_password)
        layout.addWidget(self.show_password)

        layout.addSpacing(10)

        # دکمه ورود
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

        # اتصال کلید اینتر
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)

        center.addWidget(card)
        outer.addLayout(center, stretch=1)

        return panel

    # ---------- جابه‌جایی و کنترل پنجره ----------

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

    # ---------- رفتارها ----------

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

    # ---------- استایل (QSS) ----------

    @staticmethod
    def _stylesheet() -> str:
        return """
        #leftPanel {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #a484d8, stop:1 #8e6ecc
            );
            border-top-left-radius: 24px;
            border-bottom-left-radius: 24px;
        }
        #rightPanel {
            background: #f5f2fa;
            border-top-right-radius: 24px;
            border-bottom-right-radius: 24px;
        }
        
        /* شفافیت متون و لوگوی پنل چپ */
        #leftPanel QLabel, #leftPanel QSvgWidget {
            background: transparent;
            border: none;
        }

        #appTitle {
            color: #ffffff;
            font-size: 28px;
            font-weight: bold;
        }
        #appSubtitle {
            color: #f1ebfa;
            font-size: 13px;
        }

        /* --- استایل اختصاصی و پرقدرت دکمه‌های کنترل پنجره --- */
        #leftPanel QPushButton#ctrlCloseBtn,
        #leftPanel QPushButton#ctrlMaxBtn,
        #leftPanel QPushButton#ctrlMinBtn {
            background-color: #ffffff !important;
            color: #4b367c !important;
            border: 1px solid #dcd1f3 !important;
            border-radius: 8px !important;
            padding: 0px !important;
            margin: 0px !important;
            font-size: 13px !important;
            font-weight: bold !important;
            text-align: center !important;
        }

        #leftPanel QPushButton#ctrlMaxBtn:hover,
        #leftPanel QPushButton#ctrlMinBtn:hover {
            background-color: #eee7fa !important;
            color: #2e1762 !important;
            border-color: #bfa8ea !important;
        }

        #leftPanel QPushButton#ctrlMaxBtn:pressed,
        #leftPanel QPushButton#ctrlMinBtn:pressed {
            background-color: #dcd0f4 !important;
        }

        /* حالت هاور دکمه بستن به رنگ قرمز ملایم */
        #leftPanel QPushButton#ctrlCloseBtn:hover {
            background-color: #ef5350 !important;
            border-color: #ef5350 !important;
            color: #ffffff !important;
        }
        #leftPanel QPushButton#ctrlCloseBtn:pressed {
            background-color: #d32f2f !important;
            color: #ffffff !important;
        }

        /* کارت فرم ورود */
        #loginCard {
            background: #ffffff;
            border-radius: 18px;
            border: 1px solid #e1d8f0;
        }
        #cardHeading {
            color: #5e35b1;
            font-size: 20px;
            font-weight: bold;
        }
        QLabel {
            color: #4a4458;
            font-size: 13px;
        }
        QLineEdit {
            background: #faf8fd;
            border: 1px solid #d1c4e9;
            border-radius: 10px;
            padding: 9px 12px;
            font-size: 13px;
        }
        QLineEdit:focus {
            border: 2px solid #7e57c2;
            background: #ffffff;
        }
        QCheckBox {
            color: #6f6685;
            font-size: 12px;
        }
        #loginButton {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #9575cd, stop:1 #7e57c2
            );
            color: #ffffff;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: bold;
        }
        #loginButton:hover {
            background: #8659c9;
        }
        #loginButton:focus {
            border: 2px solid #4527a0;
        }
        #loginButton:pressed {
            background: #6a3fb5;
        }
        """
