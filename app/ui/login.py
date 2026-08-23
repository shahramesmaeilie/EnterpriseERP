import sys
import ctypes
from pathlib import Path

from PySide6.QtCore import Qt, QRegularExpression, QPoint
from PySide6.QtGui import QIcon, QRegularExpressionValidator
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
)

from app.core.session import Session
from app.services.auth_service import login

# app/ (یک پوشه بالاتر از ui/)
BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "assets" / "images"
ICON_DIR = BASE_DIR / "assets" / "icons"

# شناسه چیدمان صفحه‌کلید English (US) در ویندوز
_EN_US_LAYOUT = "00000409"
_KLF_ACTIVATE = 0x00000001


def force_english_layout():
    """چیدمان صفحه‌کلید را به انگلیسی (US) برمی‌گرداند — فقط در ویندوز."""
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.LoadKeyboardLayoutW(_EN_US_LAYOUT, _KLF_ACTIVATE)
        except Exception:
            pass


class EnglishLineEdit(QLineEdit):
    """فیلد ورودی که فقط کاراکترهای انگلیسی/ASCII می‌پذیرد.

    - Validator هر کاراکتر غیر ASCII (از جمله فارسی) را رد می‌کند،
      حتی هنگام Paste.
    - در ویندوز، با هر فوکوس و هر کلید، چیدمان به انگلیسی برمی‌گردد
      تا تغییر به فارسی عملاً ممکن نباشد.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setInputMethodHints(Qt.ImhLatinOnly | Qt.ImhNoPredictiveText)
        self.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"[\x20-\x7E]*"), self)
        )
        # تایپ انگلیسی باید چپ‌به‌راست نمایش داده شود
        self.setLayoutDirection(Qt.LeftToRight)
        self.setAlignment(Qt.AlignLeft)

    def focusInEvent(self, event):
        force_english_layout()
        super().focusInEvent(event)

    def keyPressEvent(self, event):
        force_english_layout()
        super().keyPressEvent(event)


class EnterPushButton(QPushButton):
    """دکمه‌ای که با Enter هم کلیک می‌شود، نه فقط Space."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.click()
        else:
            super().keyPressEvent(event)


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enterprise ERP — ورود")
        self.setFixedSize(950, 600)

        # پنجره بدون قاب با پس‌زمینه شفاف تا گوشه‌های گرد دیده شوند
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        ico_path = IMAGE_DIR / "Enterprise.ico"
        if ico_path.exists():
            self.setWindowIcon(QIcon(str(ico_path)))

        # برای جابه‌جایی پنجره با درگ ماوس
        self._drag_offset: QPoint | None = None

        self._build_ui()

    # ---------- ساخت رابط ----------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_panel(), stretch=1)
        root.addWidget(self._build_right_panel(), stretch=1)

        self.setStyleSheet(self._stylesheet())

        # ترتیب فوکوس با Tab و فوکوس اولیه
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.login_button)
        self.username_input.setFocus()

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("leftPanel")

        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(18)

        svg_path = IMAGE_DIR / "Enterprise.svg"
        if svg_path.exists():
            logo = QSvgWidget(str(svg_path))
            logo.setFixedSize(160, 160)
            layout.addWidget(logo, alignment=Qt.AlignCenter)

        title = QLabel("Enterprise ERP")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("سامانه یکپارچه مدیریت کسب‌وکار")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("rightPanel")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- نوار بالایی با دکمه بستن (چون پنجره بدون قاب است) ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 10, 14, 0)
        top_bar.addStretch()

        close_button = QPushButton("✕")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setFocusPolicy(Qt.NoFocus)
        close_button.clicked.connect(self.close)
        top_bar.addWidget(close_button)

        outer.addLayout(top_bar)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedSize(360, 430)
        # فقط کارت ورود RTL می‌شود تا محتوای فارسی درست چیده شود
        card.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        heading = QLabel("ورود به سیستم")
        heading.setObjectName("cardHeading")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        layout.addSpacing(8)

        # --- نام کاربری (فقط انگلیسی) ---
        layout.addWidget(QLabel("نام کاربری"))
        self.username_input = EnglishLineEdit()
        self.username_input.setPlaceholderText("Username")
        user_icon = ICON_DIR / "user.svg"
        if user_icon.exists():
            self.username_input.addAction(
                QIcon(str(user_icon)), QLineEdit.LeadingPosition
            )
        layout.addWidget(self.username_input)

        # --- رمز عبور (فقط انگلیسی) ---
        layout.addWidget(QLabel("رمز عبور"))
        self.password_input = EnglishLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        lock_icon = ICON_DIR / "lock.svg"
        if lock_icon.exists():
            self.password_input.addAction(
                QIcon(str(lock_icon)), QLineEdit.LeadingPosition
            )
        layout.addWidget(self.password_input)

        # --- نمایش رمز ---
        self.show_password = QCheckBox("نمایش رمز عبور")
        self.show_password.toggled.connect(self._toggle_password)
        layout.addWidget(self.show_password)

        layout.addSpacing(10)

        # --- دکمه ورود (با پشتیبانی Enter) ---
        self.login_button = EnterPushButton("ورود")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedHeight(42)
        self.login_button.setCursor(Qt.PointingHandCursor)
        login_icon = ICON_DIR / "login.svg"
        if login_icon.exists():
            self.login_button.setIcon(QIcon(str(login_icon)))
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        layout.addStretch()

        # زنجیره‌ی Enter:
        # نام کاربری → رمز عبور → دکمه ورود → کلیک
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.login_button.setFocus)

        center.addWidget(card)
        outer.addLayout(center, stretch=1)

        return panel

    # ---------- جابه‌جایی پنجره بدون قاب با درگ ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    # ---------- رفتارها ----------

    def _toggle_password(self, checked: bool):
        self.password_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        success, message = login(username, password)

        if not success:
            QMessageBox.warning(self, "خطا در ورود", message)
            return

        QMessageBox.information(self, "ورود موفق", message)
        self.open_dashboard()

    def open_dashboard(self):
        try:
            from app.ui.dashboard import DashboardWindow
        except ImportError:
            QMessageBox.information(
                self,
                "در دست ساخت",
                "صفحه داشبورد هنوز آماده نشده است.",
            )
            return

        self.dashboard = DashboardWindow()
        self.dashboard.show()
        self.close()

    # ---------- استایل ----------

    @staticmethod
    def _stylesheet() -> str:
        return """
        /* گوشه‌های گرد پنجره: چون Qt فرزندان را به شعاع والد برش نمی‌دهد،
           شعاع مستقیماً روی پنل چپ (گوشه‌های چپ) و پنل راست (گوشه‌های راست)
           اعمال شده است. */
        #leftPanel {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #b39ddb, stop:1 #9575cd
            );
            border-top-left-radius: 24px;
            border-bottom-left-radius: 24px;
        }
        #rightPanel {
            background: #f5f2fa;
            border-top-right-radius: 24px;
            border-bottom-right-radius: 24px;
        }
        #appTitle {
            color: #ffffff;
            font-size: 30px;
            font-weight: bold;
        }
        #appSubtitle {
            color: #ede7f6;
            font-size: 14px;
        }
        #closeButton {
            background: transparent;
            color: #7e57c2;
            border: none;
            border-radius: 15px;
            font-size: 14px;
            font-weight: bold;
        }
        #closeButton:hover {
            background: #e57373;
            color: #ffffff;
        }
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
