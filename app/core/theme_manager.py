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

            # بروزرسانی همه ویجت‌ها
            for widget in app.allWidgets():
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
        """تولید استایل تم روشن"""
        return """
            /* استایل کلی - تم روشن */
            QWidget {
                background-color: #faf8ff;
                color: #1a1a2e;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }

            /* دکمه‌ها */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 """ + primary + """, stop:1 """ + secondary + """);
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
            }
            QPushButton:pressed {
                background: """ + secondary + """;
            }
            QPushButton:disabled {
                background: #b9aee6;
                color: #ffffff;
            }

            /* دکمه ثانویه */
            QPushButton#btnSecondary {
                background: #f0ecf8;
                color: #4a3a6a;
                border: 2px solid #e8e0f5;
            }
            QPushButton#btnSecondary:hover {
                background: #e8e0f5;
            }

            /* دکمه حذف */
            QPushButton#btnDelete {
                background: #e04b4b;
                color: #ffffff;
                border: none;
            }
            QPushButton#btnDelete:hover {
                background: #f05a5a;
            }

            /* ورودی‌ها */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QTimeEdit {
                background: #ffffff;
                border: 2px solid #e8e0f5;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                color: #1a1a2e;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: """ + primary + """;
            }

            /* جدول‌ها */
            QTableWidget, QListWidget {
                background: #ffffff;
                border: 2px solid #e8e0f5;
                border-radius: 12px;
                gridline-color: #f0ecf8;
            }
            QTableWidget::item:selected, QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e0f5, stop:1 #d5c8ed);
                color: #4a3a6a;
                font-weight: bold;
                border: none;
                padding: 10px 6px;
                font-size: 12px;
            }

            /* تب‌ها */
            QTabWidget::pane {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 14px;
                padding: 12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }

            /* گروه‌ها */
            QGroupBox {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 14px;
                padding: 16px;
                margin-top: 12px;
            }
            QGroupBox::title {
                font-weight: bold;
                color: #4a3a6a;
                padding: 0 10px;
            }

            /* لیبل‌ها */
            QLabel {
                color: #4a3a6a;
                font-size: 13px;
            }

            /* اسکرول بار */
            QScrollBar:vertical {
                background: #f5f0fa;
                border-radius: 10px;
                width: 10px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 8px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }
            QScrollBar:horizontal {
                background: #f5f0fa;
                border-radius: 10px;
                height: 10px;
                margin: 4px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 8px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }
        """

    def _generate_dark_theme(self, primary: str, secondary: str) -> str:
        """تولید استایل تم تیره"""
        return """
            /* استایل کلی - تم تیره */
            QWidget {
                background-color: #1a1a2e;
                color: #e8e0f5;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }

            /* دکمه‌ها */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 """ + primary + """, stop:1 """ + secondary + """);
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
            }
            QPushButton:pressed {
                background: """ + secondary + """;
            }
            QPushButton:disabled {
                background: #3d2d61;
                color: #8a7aaa;
            }

            /* دکمه ثانویه */
            QPushButton#btnSecondary {
                background: #2a2a4e;
                color: #e8e0f5;
                border: 2px solid #3d2d61;
            }
            QPushButton#btnSecondary:hover {
                background: #3d2d61;
            }

            /* دکمه حذف */
            QPushButton#btnDelete {
                background: #8b1a1a;
                color: #ffffff;
                border: none;
            }
            QPushButton#btnDelete:hover {
                background: #b71c1c;
            }

            /* ورودی‌ها */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QTimeEdit {
                background: #2a2a4e;
                border: 2px solid #3d2d61;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                color: #e8e0f5;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: """ + primary + """;
            }

            /* جدول‌ها */
            QTableWidget, QListWidget {
                background: #2a2a4e;
                border: 2px solid #3d2d61;
                border-radius: 12px;
                gridline-color: #3d2d61;
            }
            QTableWidget::item, QListWidget::item {
                color: #e8e0f5;
            }
            QTableWidget::item:selected, QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                color: #ffffff;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #2a2a4e);
                color: #e8e0f5;
                font-weight: bold;
                border: none;
                padding: 10px 6px;
                font-size: 12px;
            }

            /* تب‌ها */
            QTabWidget::pane {
                background: #1a1a2e;
                border: 2px solid #3d2d61;
                border-radius: 14px;
                padding: 12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #2a2a4e);
                color: #e8e0f5;
            }

            /* گروه‌ها */
            QGroupBox {
                background: #1a1a2e;
                border: 2px solid #3d2d61;
                border-radius: 14px;
                padding: 16px;
                margin-top: 12px;
                color: #e8e0f5;
            }
            QGroupBox::title {
                font-weight: bold;
                color: #e8e0f5;
                padding: 0 10px;
            }

            /* لیبل‌ها */
            QLabel {
                color: #e8e0f5;
                font-size: 13px;
            }

            /* اسکرول بار */
            QScrollBar:vertical {
                background: #2a2a4e;
                border-radius: 10px;
                width: 10px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                border-radius: 8px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4d3a78, stop:1 #5d3a98);
            }
            QScrollBar:horizontal {
                background: #2a2a4e;
                border-radius: 10px;
                height: 10px;
                margin: 4px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d2d61, stop:1 #4d3a78);
                border-radius: 8px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4d3a78, stop:1 #5d3a98);
            }
        """


# ایجاد نمونه سراسری
theme_manager = ThemeManager()