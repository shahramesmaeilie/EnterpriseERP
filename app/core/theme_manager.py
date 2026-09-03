# -*- coding: utf-8 -*-
"""مدیریت تم و استایل برنامه"""

from PySide6.QtCore import QSettings, QObject, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication, QWidget


class ThemeManager(QObject):
    """مدیریت تم و استایل برنامه"""

    themeChanged = Signal(str)
    colorsChanged = Signal(dict)
    fontChanged = Signal(int)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.settings = QSettings("EnterpriseERP", "Theme")
        self._current_theme = self.settings.value("theme", "light")
        self._primary_color = self.settings.value("primary_color", "#7657c8")
        self._secondary_color = self.settings.value("secondary_color", "#4d3a78")
        self._font_size = int(self.settings.value("font_size", 12))

    def get_theme(self) -> str:
        return self._current_theme

    def set_theme(self, theme: str):
        if theme != self._current_theme:
            self._current_theme = theme
            self.settings.setValue("theme", theme)
            self.themeChanged.emit(theme)
            self.apply_theme()

    def get_primary_color(self) -> str:
        return self._primary_color

    def set_primary_color(self, color: str):
        if color != self._primary_color:
            self._primary_color = color
            self.settings.setValue("primary_color", color)
            self.colorsChanged.emit({"primary": color})
            self.apply_theme()

    def get_secondary_color(self) -> str:
        return self._secondary_color

    def set_secondary_color(self, color: str):
        if color != self._secondary_color:
            self._secondary_color = color
            self.settings.setValue("secondary_color", color)
            self.colorsChanged.emit({"secondary": color})
            self.apply_theme()

    def get_font_size(self) -> int:
        return self._font_size

    def set_font_size(self, size: int):
        if size != self._font_size:
            self._font_size = size
            self.settings.setValue("font_size", size)
            self.fontChanged.emit(size)
            self.apply_theme()

    def apply_theme(self):
        """اعمال تم به کل برنامه"""
        app = QApplication.instance()
        if app:
            # تنظیم فونت
            font = app.font()
            font.setPointSize(self._font_size)
            app.setFont(font)

            # تنظیم استایل
            style_sheet = self._generate_style_sheet()
            
            # اضافه کردن استایل مخصوص لاگین
            if self._current_theme == "dark":
                style_sheet += """
                    /* استایل تاریک برای لاگین */
                    #loginContainer {
                        background-color: #1a1a2e !important;
                        border-color: #3d2d61 !important;
                    }
                    #loginTitle {
                        color: #e8e0f5 !important;
                    }
                    #loginSubtitle {
                        color: #8a7aaa !important;
                    }
                    #inputLabel {
                        color: #e8e0f5 !important;
                    }
                    #loginInput {
                        background-color: #2a2a4e !important;
                        border-color: #3d2d61 !important;
                        color: #e8e0f5 !important;
                    }
                    #loginInput:focus {
                        border-color: #7657c8 !important;
                        background-color: #1a1a2e !important;
                    }
                    #loginInput::placeholder {
                        color: #6a5a8a !important;
                    }
                    #showPassword {
                        color: #8a7aaa !important;
                    }
                    #closeBtn {
                        color: #8a7aaa !important;
                    }
                    #closeBtn:hover {
                        background: #3d2d61 !important;
                        color: #e8e0f5 !important;
                    }
                """
            
            app.setStyleSheet(style_sheet)

            # بروزرسانی همه ویجت‌ها (این خطوط برای رفع مشکل عدم اعمال تغییرات ضروری هستند)
            for widget in app.allWidgets():
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                # اعمال attribute theme برای ویجت‌ها
                widget.setProperty("theme", self._current_theme)

    def _generate_style_sheet(self) -> str:
        """تولید استایل‌شیت بر اساس تنظیمات فعلی"""
        primary = self._primary_color
        secondary = self._secondary_color

        if self._current_theme == "dark":
            return self._generate_dark_theme(primary, secondary)
        else:
            return self._generate_light_theme(primary, secondary)

    def _generate_light_theme(self, primary: str, secondary: str) -> str:
        """تولید استایل تم روشن (شامل داشبورد و لاگین)"""
        return f"""
            /* استایل کلی - تم روشن */
            QWidget {{
                background-color: #faf8ff;
                color: #1a1a2e;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }}

            /* دکمه‌ها */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary});
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
            }}
            QPushButton:pressed {{
                background: {secondary};
            }}
            QPushButton:disabled {{
                background: #b9aee6;
                color: #ffffff;
            }}

            /* دکمه ثانویه */
            QPushButton#btnSecondary {{
                background: #f0ecf8;
                color: #4a3a6a;
                border: 2px solid #e8e0f5;
            }}
            QPushButton#btnSecondary:hover {{
                background: #e8e0f5;
            }}

            /* دکمه حذف */
            QPushButton#btnDelete {{
                background: #e04b4b;
                color: #ffffff;
                border: none;
            }}
            QPushButton#btnDelete:hover {{
                background: #f05a5a;
            }}

            /* ورودی‌ها */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QTimeEdit {{
                background: #ffffff;
                border: 2px solid #e8e0f5;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                color: #1a1a2e;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border-color: {primary};
            }}

            /* جدول‌ها */
            QTableWidget, QListWidget {{
                background: #ffffff;
                border: 2px solid #e8e0f5;
                border-radius: 12px;
                gridline-color: #f0ecf8;
            }}
            QTableWidget::item:selected, QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e0f5, stop:1 #d5c8ed);
                color: #4a3a6a;
                font-weight: bold;
                border: none;
                padding: 10px 6px;
                font-size: 12px;
            }}

            /* تب‌ها */
            QTabWidget::pane {{
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 14px;
                padding: 12px;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }}

            /* گروه‌ها */
            QGroupBox {{
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 14px;
                padding: 16px;
                margin-top: 12px;
            }}
            QGroupBox::title {{
                font-weight: bold;
                color: #4a3a6a;
                padding: 0 10px;
            }}

            /* لیبل‌ها */
            QLabel {{
                color: #4a3a6a;
                font-size: 13px;
            }}

            /* اسکرول بار */
            QScrollBar:vertical {{
                background: #f5f0fa;
                border-radius: 10px;
                width: 10px;
                margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 8px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }}
            QScrollBar:horizontal {{
                background: #f5f0fa;
                border-radius: 10px;
                height: 10px;
                margin: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 8px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }}

            /* ======= استایل داشبورد (Sidebar) ======= */
            #mainContainer {{
                background-color: #faf8ff;
                border-radius: 18px;
            }}
            #header {{
                background-color: #faf8ff;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid #e6e0f5;
            }}
            #appTitle {{
                color: {secondary};
                font-size: 16px;
                font-weight: bold;
            }}
            #userLabel {{
                color: {primary};
                font-size: 13px;
                margin-left: 8px;
            }}
            #winBtn {{
                background-color: #efeaf9;
                border: none;
                border-radius: 8px;
                border-bottom: 2px solid #d5cbee;
            }}
            #winBtn:hover {{
                margin-top: -3px;
                border-bottom: 3px solid #b9a8e3;
                background-color: #e4dbf6;
            }}
            #winBtn[kind="close"]:hover {{
                background-color: #f8d7da;
                border-bottom: 3px solid #b71c1c;
            }}
            
            /* سایدبار با رنگ‌های داینامیک */
            #sidebar {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary});
                border-bottom-right-radius: 18px;
            }}
            #menuBtn {{
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.18);
            }}
            #menuBtn:hover {{
                margin-top: -4px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.28);
                background-color: rgba(255, 255, 255, 0.16);
            }}
            #menuBtn:checked {{
                background-color: rgba(255, 255, 255, 0.26);
                border-bottom: 4px solid rgba(0, 0, 0, 0.32);
                font-weight: bold;
            }}
            #logoutBtn {{
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #d32f2f;
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid #8e1b1b;
            }}
            #logoutBtn:hover {{
                margin-top: -4px;
                border-bottom: 4px solid #b71c1c;
                background-color: #e53935;
            }}
            #contentStack {{
                background-color: #faf8ff;
                border-bottom-left-radius: 18px;
            }}
            #placeholderLabel {{
                color: {secondary};
                font-size: 17px;
            }}
            #welcomeLabel {{
                color: {secondary};
                font-size: 20px;
                font-weight: bold;
                padding: 20px;
            }}
            #statsFrame {{
                background: transparent;
                padding: 10px;
            }}

            /* ======= استایل صفحه تنظیمات ======= */
            #settingsPage {{ background-color: #f4f1fa; }}
            #settingsSidebar {{ background-color: #ffffff; border-right: 1px solid #e8e0f5; }}
            #sideTitle {{ font-size: 20px; font-weight: bold; color: #4a3a6a; margin-bottom: 20px; }}
            #sidebarButton {{
                text-align: left;
                background: transparent;
                border: none;
                border-radius: 12px;
                color: #5c5470;
                font-size: 14px;
                padding: 12px;
            }}
            #sidebarButton:hover {{ background: #f0ecf8; color: {primary}; }}
            #sidebarButton:checked {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary}); color: #ffffff; font-weight: bold; }}
            #settingsCard {{ background: #ffffff; border-radius: 20px; border: 1px solid #e8e0f5; }}
            #cardTitle {{ font-size: 20px; font-weight: bold; color: #2e263d; }}
            #separatorLine {{ background-color: #f0ecf8; max-height: 1px; border: none; }}
            #btnPrimary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary}); color: white; border: none; border-radius: 12px; padding: 10px 20px; font-weight: bold; }}
            #btnSecondary {{ background: #f0ecf8; color: #4a3a6a; border: 2px solid #e8e0f5; border-radius: 12px; padding: 8px 15px; }}
            #btnDelete {{ background: #e04b4b; color: white; border: none; border-radius: 12px; padding: 8px 15px; }}
            #colorPickerBtn {{ background: #faf8fd; border: 2px dashed #d1c4e9; border-radius: 12px; padding: 10px; font-weight: bold; color: #5c5470; }}
            #colorPickerBtn:hover {{ border-color: {primary}; color: {primary}; }}
            QListWidget {{ background: #faf8fd; border: 2px solid #e8e0f5; border-radius: 12px; padding: 10px; }}
            QListWidget::item {{ padding: 10px; border-radius: 8px; }}
            QListWidget::item:selected {{ background: {primary}; color: white; }}

            /* ======= استایل فرم لاگین ======= */
            #leftPanel {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {primary}, stop:1 {secondary}
                );
                border-top-left-radius: 24px;
                border-bottom-left-radius: 24px;
            }}
            #rightPanel {{
                background: #f5f2fa;
                border-top-right-radius: 24px;
                border-bottom-right-radius: 24px;
            }}
            #leftPanel QLabel, #leftPanel QSvgWidget {{
                background: transparent;
                border: none;
            }}
            #appTitle {{
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }}
            #appSubtitle {{
                color: #f1ebfa;
                font-size: 13px;
            }}
            #leftPanel QPushButton#ctrlCloseBtn,
            #leftPanel QPushButton#ctrlMaxBtn,
            #leftPanel QPushButton#ctrlMinBtn {{
                background-color: #ffffff !important;
                color: {secondary} !important;
                border: 1px solid #dcd1f3 !important;
                border-radius: 8px !important;
                padding: 0px !important;
                margin: 0px !important;
                font-size: 13px !important;
                font-weight: bold !important;
                text-align: center !important;
            }}
            #leftPanel QPushButton#ctrlMaxBtn:hover,
            #leftPanel QPushButton#ctrlMinBtn:hover {{
                background-color: #eee7fa !important;
                color: #2e1762 !important;
                border-color: #bfa8ea !important;
            }}
            #leftPanel QPushButton#ctrlMaxBtn:pressed,
            #leftPanel QPushButton#ctrlMinBtn:pressed {{
                background-color: #dcd0f4 !important;
            }}
            #leftPanel QPushButton#ctrlCloseBtn:hover {{
                background-color: #ef5350 !important;
                border-color: #ef5350 !important;
                color: #ffffff !important;
            }}
            #leftPanel QPushButton#ctrlCloseBtn:pressed {{
                background-color: #d32f2f !important;
                color: #ffffff !important;
            }}
            #loginCard {{
                background: #ffffff;
                border-radius: 18px;
                border: 1px solid #e1d8f0;
            }}
            #cardHeading {{
                color: {secondary};
                font-size: 20px;
                font-weight: bold;
            }}
            #loginButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary}
                );
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }}
            #loginButton:hover {{
                background: {primary};
            }}
            #loginButton:focus {{
                border: 2px solid {secondary};
            }}
            #loginButton:pressed {{
                background: {secondary};
            }}
        """

    def _generate_dark_theme(self, primary: str, secondary: str) -> str:
        """تولید استایل تم تیره"""
        return f"""
            /* استایل کلی - تم تیره */
            QWidget {{
                background-color: #1a1a2e;
                color: #e8e0f5;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }}

            /* دکمه‌ها */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary});
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
            }}
            QPushButton:pressed {{
                background: {secondary};
            }}
            QPushButton:disabled {{
                background: #3d2d61;
                color: #8a7aaa;
            }}

            /* دکمه ثانویه */
            QPushButton#btnSecondary {{
                background: #2a2a4e;
                color: #e8e0f5;
                border: 2px solid #3d2d61;
            }}
            QPushButton#btnSecondary:hover {{
                background: #3d2d61;
            }}

            /* دکمه حذف */
            QPushButton#btnDelete {{
                background: #8b1a1a;
                color: #ffffff;
                border: none;
            }}
            QPushButton#btnDelete:hover {{
                background: #b71c1c;
            }}

            /* ورودی‌ها */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QTimeEdit {{
                background: #2a2a4e;
                border: 2px solid #3d2d61;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                color: #e8e0f5;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border-color: {primary};
            }}

            /* جدول‌ها */
            QTableWidget, QListWidget {{
                background: #2a2a4e;
                border: 2px solid #3d2d61;
                border-radius: 12px;
                gridline-color: #3d2d61;
            }}
            QTableWidget::item, QListWidget::item {{
                color: #e8e0f5;
            }}
            QTableWidget::item:selected, QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                color: #ffffff;
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #2a2a4e);
                color: #e8e0f5;
                font-weight: bold;
                border: none;
                padding: 10px 6px;
                font-size: 12px;
            }}

            /* تب‌ها */
            QTabWidget::pane {{
                background: #1a1a2e;
                border: 2px solid #3d2d61;
                border-radius: 14px;
                padding: 12px;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #2a2a4e);
                color: #e8e0f5;
            }}

            /* گروه‌ها */
            QGroupBox {{
                background: #1a1a2e;
                border: 2px solid #3d2d61;
                border-radius: 14px;
                padding: 16px;
                margin-top: 12px;
                color: #e8e0f5;
            }}
            QGroupBox::title {{
                font-weight: bold;
                color: #e8e0f5;
                padding: 0 10px;
            }}

            /* لیبل‌ها */
            QLabel {{
                color: #e8e0f5;
                font-size: 13px;
            }}

            /* اسکرول بار */
            QScrollBar:vertical {{
                background: #2a2a4e;
                border-radius: 10px;
                width: 10px;
                margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                border-radius: 8px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4d3a78, stop:1 #5d3a98);
            }}
            QScrollBar:horizontal {{
                background: #2a2a4e;
                border-radius: 10px;
                height: 10px;
                margin: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                border-radius: 8px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4d3a78, stop:1 #5d3a98);
            }}

            /* ======= استایل داشبورد (Sidebar) - تیره ======= */
            #mainContainer {{
                background-color: #1a1a2e;
                border-radius: 18px;
            }}
            #header {{
                background-color: #1a1a2e;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                border-bottom: 1px solid #3d2d61;
            }}
            #appTitle {{
                color: {primary};
                font-size: 16px;
                font-weight: bold;
            }}
            #userLabel {{
                color: #e8e0f5;
                font-size: 13px;
                margin-left: 8px;
            }}
            #winBtn {{
                background-color: #2a2a4e;
                border: none;
                border-radius: 8px;
                border-bottom: 2px solid #3d2d61;
            }}
            #winBtn:hover {{
                margin-top: -3px;
                border-bottom: 3px solid {primary};
                background-color: #3d2d61;
            }}
            #winBtn[kind="close"]:hover {{
                background-color: #8b1a1a;
                border-bottom: 3px solid #b71c1c;
            }}
            #sidebar {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary});
                border-bottom-right-radius: 18px;
            }}
            #menuBtn {{
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.18);
            }}
            #menuBtn:hover {{
                margin-top: -4px;
                border-bottom: 4px solid rgba(0, 0, 0, 0.28);
                background-color: rgba(255, 255, 255, 0.16);
            }}
            #menuBtn:checked {{
                background-color: rgba(255, 255, 255, 0.26);
                border-bottom: 4px solid rgba(0, 0, 0, 0.32);
                font-weight: bold;
            }}
            #logoutBtn {{
                color: #ffffff;
                text-align: right;
                padding: 10px 14px;
                font-size: 14px;
                background-color: #d32f2f;
                border: none;
                border-radius: 10px;
                border-bottom: 4px solid #8e1b1b;
            }}
            #logoutBtn:hover {{
                margin-top: -4px;
                border-bottom: 4px solid #b71c1c;
                background-color: #e53935;
            }}
            #contentStack {{
                background-color: #1a1a2e;
                border-bottom-left-radius: 18px;
            }}
            #placeholderLabel {{
                color: #e8e0f5;
                font-size: 17px;
            }}
            #welcomeLabel {{
                color: #e8e0f5;
                font-size: 20px;
                font-weight: bold;
                padding: 20px;
            }}
            #statsFrame {{
                background: transparent;
                padding: 10px;
            }}
            
            /* ======= استایل صفحه تنظیمات - تیره ======= */
            #settingsPage {{ background-color: #14142b; }}
            #settingsSidebar {{ background-color: #1a1a2e; border-right: 1px solid #3d2d61; }}
            #sideTitle {{ font-size: 20px; font-weight: bold; color: #e8e0f5; margin-bottom: 20px; }}
            #sidebarButton {{
                text-align: left;
                background: transparent;
                border: none;
                border-radius: 12px;
                color: #8a7aaa;
                font-size: 14px;
                padding: 12px;
            }}
            #sidebarButton:hover {{ background: #2a2a4e; color: #ffffff; }}
            #sidebarButton:checked {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary}); color: #ffffff; font-weight: bold; }}
            #settingsCard {{ background: #1a1a2e; border-radius: 20px; border: 1px solid #3d2d61; }}
            #cardTitle {{ font-size: 20px; font-weight: bold; color: #e8e0f5; }}
            #separatorLine {{ background-color: #3d2d61; max-height: 1px; border: none; }}
            #btnPrimary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary}); color: white; border: none; border-radius: 12px; padding: 10px 20px; font-weight: bold; }}
            #btnSecondary {{ background: #2a2a4e; color: #e8e0f5; border: 2px solid #3d2d61; border-radius: 12px; padding: 8px 15px; }}
            #btnDelete {{ background: #8b1a1a; color: white; border: none; border-radius: 12px; padding: 8px 15px; }}
            #colorPickerBtn {{ background: #2a2a4e; border: 2px dashed #5d3a98; border-radius: 12px; padding: 10px; font-weight: bold; color: #e8e0f5; }}
            #colorPickerBtn:hover {{ border-color: {primary}; color: {primary}; }}
            QListWidget {{ background: #2a2a4e; border: 2px solid #3d2d61; border-radius: 12px; padding: 10px; }}
            QListWidget::item {{ padding: 10px; border-radius: 8px; color: #e8e0f5; }}
            QListWidget::item:selected {{ background: {primary}; color: white; }}

            /* ======= استایل فرم لاگین - تیره ======= */
            #leftPanel {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {primary}, stop:1 {secondary}
                );
                border-top-left-radius: 24px;
                border-bottom-left-radius: 24px;
            }}
            #rightPanel {{
                background: #1a1a2e;
                border-top-right-radius: 24px;
                border-bottom-right-radius: 24px;
            }}
            #leftPanel QLabel, #leftPanel QSvgWidget {{
                background: transparent;
                border: none;
            }}
            #appTitle {{
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }}
            #appSubtitle {{
                color: #f1ebfa;
                font-size: 13px;
            }}
            #leftPanel QPushButton#ctrlCloseBtn,
            #leftPanel QPushButton#ctrlMaxBtn,
            #leftPanel QPushButton#ctrlMinBtn {{
                background-color: #ffffff !important;
                color: {secondary} !important;
                border: 1px solid #dcd1f3 !important;
                border-radius: 8px !important;
                padding: 0px !important;
                margin: 0px !important;
                font-size: 13px !important;
                font-weight: bold !important;
                text-align: center !important;
            }}
            #leftPanel QPushButton#ctrlMaxBtn:hover,
            #leftPanel QPushButton#ctrlMinBtn:hover {{
                background-color: #eee7fa !important;
                color: #2e1762 !important;
                border-color: #bfa8ea !important;
            }}
            #leftPanel QPushButton#ctrlMaxBtn:pressed,
            #leftPanel QPushButton#ctrlMinBtn:pressed {{
                background-color: #dcd0f4 !important;
            }}
            #leftPanel QPushButton#ctrlCloseBtn:hover {{
                background-color: #ef5350 !important;
                border-color: #ef5350 !important;
                color: #ffffff !important;
            }}
            #leftPanel QPushButton#ctrlCloseBtn:pressed {{
                background-color: #d32f2f !important;
                color: #ffffff !important;
            }}
            #loginCard {{
                background: #2a2a4e;
                border-radius: 18px;
                border: 1px solid #3d2d61;
            }}
            #cardHeading {{
                color: {primary};
                font-size: 20px;
                font-weight: bold;
            }}
            #loginButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {primary}, stop:1 {secondary}
                );
                color: #ffffff;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }}
            #loginButton:hover {{
                background: {primary};
            }}
            #loginButton:focus {{
                border: 2px solid {secondary};
            }}
            #loginButton:pressed {{
                background: {secondary};
            }}
        """


# ایجاد نمونه سراسری
theme_manager = ThemeManager()