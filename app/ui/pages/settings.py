# -*- coding: utf-8 -*-
"""صفحه تنظیمات برنامه - مدیریت کاربران، تنظیمات سیستم و پشتیبان‌گیری با قابلیت تغییر زنده رنگ سراسری"""

from __future__ import annotations

import sqlite3
import os
import shutil
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from PySide6.QtCore import Qt, QTimer, QSettings, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QGroupBox, QFrame, QMessageBox, QTabWidget,
    QSpinBox, QCheckBox, QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QTextEdit, QApplication, QStyle, QStyleFactory,
    QColorDialog, QFontDialog, QScrollArea, QGridLayout,
    QDoubleSpinBox, QDateEdit, QTimeEdit, QSlider, QRadioButton,
    QButtonGroup, QProgressBar, QListWidget, QListWidgetItem,
    QSplitter
)

from app.core.session import Session
from app.database.connection import get_connection, DB_PATH
from app.core.theme_manager import theme_manager

try:
    from app.database.migrations import DB_PATH as MIGRATIONS_DB_PATH
except Exception:
    MIGRATIONS_DB_PATH = DB_PATH


class SettingsPage(QWidget):
    """صفحه تنظیمات برنامه با اعمال بلادرنگ تم به تمام صفحات"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        
        # اتصال به سیگنال‌های theme_manager
        if hasattr(theme_manager, "themeChanged"):
            theme_manager.themeChanged.connect(self._on_theme_changed)
        if hasattr(theme_manager, "colorsChanged"):
            theme_manager.colorsChanged.connect(self._on_colors_changed)
        if hasattr(theme_manager, "fontChanged"):
            theme_manager.fontChanged.connect(self._on_font_changed)
        
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # عنوان صفحه
        title_layout = QHBoxLayout()
        title = QLabel("⚙️ تنظیمات سیستم", objectName="pageTitle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e263d;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # دکمه ذخیره تنظیمات
        self.btn_save = QPushButton("💾 ذخیره تنظیمات")
        self.btn_save.setObjectName("btnPrimary")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_settings)
        title_layout.addWidget(self.btn_save)

        main_layout.addLayout(title_layout)

        # تب‌های تنظیمات
        self.tabs = QTabWidget()
        self.tabs.setObjectName("settingsTabs")

        # تب‌های مختلف
        self.tabs.addTab(self._create_general_tab(), "🔧 عمومی")
        self.tabs.addTab(self._create_appearance_tab(), "🎨 ظاهر و رنگ‌بندی")
        self.tabs.addTab(self._create_database_tab(), "💾 دیتابیس")
        self.tabs.addTab(self._create_backup_tab(), "📦 پشتیبان‌گیری")
        self.tabs.addTab(self._create_users_tab(), "👤 کاربران")
        self.tabs.addTab(self._create_about_tab(), "ℹ️ درباره")

        main_layout.addWidget(self.tabs, 1)

    def _create_general_tab(self) -> QWidget:
        """تب تنظیمات عمومی"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        general_group = QGroupBox("تنظیمات عمومی")
        general_group.setObjectName("settingsGroup")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("نام شرکت...")
        general_layout.addRow("🏢 نام شرکت:", self.company_name)

        self.app_name = QLineEdit()
        self.app_name.setPlaceholderText("نام برنامه...")
        general_layout.addRow("📱 نام برنامه:", self.app_name)

        self.currency = QComboBox()
        self.currency.addItems(["ریال", "تومان", "دلار", "یورو"])
        general_layout.addRow("💰 واحد پول:", self.currency)

        self.date_format = QComboBox()
        self.date_format.addItems(["YYYY/MM/DD", "DD/MM/YYYY", "MM/DD/YYYY"])
        general_layout.addRow("📅 فرمت تاریخ:", self.date_format)

        layout.addWidget(general_group)

        default_group = QGroupBox("تنظیمات پیش‌فرض")
        default_group.setObjectName("settingsGroup")
        default_layout = QFormLayout(default_group)
        default_layout.setSpacing(10)

        self.default_discount = QDoubleSpinBox()
        self.default_discount.setRange(0, 100)
        self.default_discount.setSuffix(" %")
        default_layout.addRow("💸 تخفیف پیش‌فرض:", self.default_discount)

        self.default_tax = QDoubleSpinBox()
        self.default_tax.setRange(0, 100)
        self.default_tax.setSuffix(" %")
        default_layout.addRow("🧾 مالیات پیش‌فرض:", self.default_tax)

        layout.addWidget(default_group)
        layout.addStretch()
        return tab

    def _create_appearance_tab(self) -> QWidget:
        """تب تنظیمات ظاهر و انتخاب رنگ سراسری"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        # ۱. انتخاب حالت تیره / روشن
        theme_group = QGroupBox("حالت تم (Theme Mode)")
        theme_group.setObjectName("settingsGroup")
        theme_layout = QVBoxLayout(theme_group)

        theme_radio_group = QButtonGroup(self)
        theme_options_layout = QHBoxLayout()

        self.theme_light = QRadioButton("☀️ روشن (Light)")
        self.theme_dark = QRadioButton("🌙 تیره (Dark)")
        self.theme_system = QRadioButton("💻 هماهنگ با سیستم")

        theme_radio_group.addButton(self.theme_light)
        theme_radio_group.addButton(self.theme_dark)
        theme_radio_group.addButton(self.theme_system)

        self.theme_light.toggled.connect(lambda: self._on_theme_radio_changed("light"))
        self.theme_dark.toggled.connect(lambda: self._on_theme_radio_changed("dark"))
        self.theme_system.toggled.connect(lambda: self._on_theme_radio_changed("system"))

        theme_options_layout.addWidget(self.theme_light)
        theme_options_layout.addWidget(self.theme_dark)
        theme_options_layout.addWidget(self.theme_system)
        theme_layout.addLayout(theme_options_layout)

        layout.addWidget(theme_group)

        # ۲. پالت‌های رنگی آماده سراسری
        preset_group = QGroupBox("پالت‌های رنگی آماده سراسری (کلیک برای اعمال آنی)")
        preset_group.setObjectName("settingsGroup")
        preset_layout = QHBoxLayout(preset_group)
        preset_layout.setSpacing(10)

        palettes = [
            ("بنفش سلطنتی", "#7c3aed", "#5b21b6"),
            ("آبی نیلگون", "#0284c7", "#0369a1"),
            ("سبز زمردی", "#059669", "#047857"),
            ("نارنجی کهربایی", "#ea580c", "#c2410c"),
            ("سرخ یاقوتی", "#e11d48", "#be123c"),
            ("مشکی فیبر کربن", "#334155", "#1e293b"),
        ]

        for name, p_col, s_col in palettes:
            p_btn = QPushButton(name)
            p_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            p_btn.setFixedHeight(34)
            p_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p_col}, stop:1 {s_col});
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.2);
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)
            p_btn.clicked.connect(lambda _, p=p_col, s=s_col: self._apply_preset_palette(p, s))
            preset_layout.addWidget(p_btn)

        layout.addWidget(preset_group)

        # ۳. انتخاب رنگ اختصاصی (Color Picker)
        color_group = QGroupBox("انتخاب رنگ‌های دلخواه (سراسری)")
        color_group.setObjectName("settingsGroup")
        color_layout = QGridLayout(color_group)
        color_layout.setSpacing(10)

        color_layout.addWidget(QLabel("رنگ اصلی برنامه (Primary Color):"), 0, 0)
        self.primary_color_btn = QPushButton("انتخاب رنگ اصلی...")
        self.primary_color_btn.setObjectName("colorPickerBtn")
        self.primary_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary_color_btn.clicked.connect(lambda: self._select_color("primary"))
        color_layout.addWidget(self.primary_color_btn, 0, 1)

        color_layout.addWidget(QLabel("رنگ ثانویه / گرادینت (Secondary Color):"), 1, 0)
        self.secondary_color_btn = QPushButton("انتخاب رنگ ثانویه...")
        self.secondary_color_btn.setObjectName("colorPickerBtn")
        self.secondary_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.secondary_color_btn.clicked.connect(lambda: self._select_color("secondary"))
        color_layout.addWidget(self.secondary_color_btn, 1, 1)

        # نوار پیش‌نمایش گرادینت فعلی
        self.theme_preview = QFrame()
        self.theme_preview.setObjectName("themePreview")
        self.theme_preview.setFixedHeight(36)
        color_layout.addWidget(self.theme_preview, 2, 0, 1, 2)

        layout.addWidget(color_group)

        # ۴. تنظیم اندازه فونت
        font_group = QGroupBox("فونت و تایپوگرافی")
        font_group.setObjectName("settingsGroup")
        font_layout = QHBoxLayout(font_group)

        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(theme_manager.get_font_size())
        self.font_size.setSuffix(" pt")
        self.font_size.valueChanged.connect(self._on_font_size_changed)

        font_layout.addWidget(QLabel("سایز فونت سراسری:"))
        font_layout.addWidget(self.font_size)
        font_layout.addStretch()

        self.btn_font = QPushButton("انتخاب قلم (Font)...")
        self.btn_font.setObjectName("btnSecondary")
        self.btn_font.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_font.clicked.connect(self._select_font)
        font_layout.addWidget(self.btn_font)

        layout.addWidget(font_group)

        # ۵. بازنشانی
        reset_btn = QPushButton("🔄 بازنشانی تم و رنگ‌ها به حالت اولیه")
        reset_btn.setObjectName("btnSecondary")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_appearance)
        layout.addWidget(reset_btn)

        layout.addStretch()
        return tab

    def _create_database_tab(self) -> QWidget:
        """تب مدیریت دیتابیس"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        info_group = QGroupBox("اطلاعات دیتابیس")
        info_group.setObjectName("settingsGroup")
        info_layout = QFormLayout(info_group)

        self.db_path_label = QLabel(str(DB_PATH))
        self.db_path_label.setWordWrap(True)
        info_layout.addRow("📍 مسیر دیتابیس:", self.db_path_label)

        self.db_size_label = QLabel("در حال محاسبه...")
        info_layout.addRow("📊 حجم دیتابیس:", self.db_size_label)

        self.db_tables_label = QLabel("در حال محاسبه...")
        info_layout.addRow("📋 تعداد جدول‌ها:", self.db_tables_label)

        self.db_records_label = QLabel("در حال محاسبه...")
        info_layout.addRow("📝 تعداد رکوردها:", self.db_records_label)

        layout.addWidget(info_group)

        actions_group = QGroupBox("عملیات دیتابیس")
        actions_group.setObjectName("settingsGroup")
        actions_layout = QVBoxLayout(actions_group)

        actions_row = QHBoxLayout()

        btn_optimize = QPushButton("🔧 بهینه‌سازی دیتابیس")
        btn_optimize.setObjectName("btnSecondary")
        btn_optimize.clicked.connect(self._optimize_database)
        actions_row.addWidget(btn_optimize)

        btn_check = QPushButton("✅ بررسی سلامت")
        btn_check.setObjectName("btnSecondary")
        btn_check.clicked.connect(self._check_database)
        actions_row.addWidget(btn_check)

        actions_layout.addLayout(actions_row)

        btn_export = QPushButton("📤 خروجی کامل دیتابیس (SQL)")
        btn_export.setObjectName("btnSecondary")
        btn_export.clicked.connect(self._export_database)
        actions_layout.addWidget(btn_export)

        layout.addWidget(actions_group)
        layout.addStretch()

        self._update_db_info()
        return tab

    def _create_backup_tab(self) -> QWidget:
        """تب پشتیبان‌گیری"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        backup_group = QGroupBox("پشتیبان‌گیری")
        backup_group.setObjectName("settingsGroup")
        backup_layout = QVBoxLayout(backup_group)

        backup_info = QLabel("از دیتابیس خود پشتیبان بگیرید یا پشتیبان قبلی را بازیابی کنید.")
        backup_info.setWordWrap(True)
        backup_layout.addWidget(backup_info)

        backup_buttons = QHBoxLayout()

        btn_backup = QPushButton("📦 ایجاد پشتیبان")
        btn_backup.setObjectName("btnPrimary")
        btn_backup.clicked.connect(self._create_backup)
        backup_buttons.addWidget(btn_backup)

        btn_restore = QPushButton("🔄 بازیابی پشتیبان")
        btn_restore.setObjectName("btnSecondary")
        btn_restore.clicked.connect(self._restore_backup)
        backup_buttons.addWidget(btn_restore)

        backup_layout.addLayout(backup_buttons)
        layout.addWidget(backup_group)

        backup_list_group = QGroupBox("پشتیبان‌های موجود")
        backup_list_group.setObjectName("settingsGroup")
        backup_list_layout = QVBoxLayout(backup_list_group)

        self.backup_list = QListWidget()
        self.backup_list.itemDoubleClicked.connect(self._restore_backup_from_list)
        backup_list_layout.addWidget(self.backup_list)

        refresh_backups_btn = QPushButton("🔄 بروزرسانی لیست")
        refresh_backups_btn.setObjectName("btnSecondary")
        refresh_backups_btn.clicked.connect(self._refresh_backup_list)
        backup_list_layout.addWidget(refresh_backups_btn)

        layout.addWidget(backup_list_group)
        self._refresh_backup_list()
        return tab

    def _create_users_tab(self) -> QWidget:
        """تب مدیریت کاربران"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        users_group = QGroupBox("مدیریت کاربران")
        users_group.setObjectName("settingsGroup")
        users_layout = QVBoxLayout(users_group)

        toolbar = QHBoxLayout()

        self.btn_add_user = QPushButton("➕ افزودن کاربر")
        self.btn_add_user.setObjectName("btnPrimary")
        self.btn_add_user.clicked.connect(self._add_user)
        toolbar.addWidget(self.btn_add_user)

        self.btn_edit_user = QPushButton("✏️ ویرایش کاربر")
        self.btn_edit_user.setObjectName("btnSecondary")
        self.btn_edit_user.clicked.connect(self._edit_user)
        toolbar.addWidget(self.btn_edit_user)

        self.btn_delete_user = QPushButton("🗑️ حذف کاربر")
        self.btn_delete_user.setObjectName("btnDelete")
        self.btn_delete_user.clicked.connect(self._delete_user)
        toolbar.addWidget(self.btn_delete_user)

        toolbar.addStretch()
        users_layout.addLayout(toolbar)

        self.users_table = QTableWidget()
        self.users_table.setObjectName("usersTable")
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "شناسه", "نام کاربری", "نام کامل", "نقش", "وضعیت"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        users_layout.addWidget(self.users_table, 1)

        layout.addWidget(users_group)
        self._load_users()
        return tab

    def _create_about_tab(self) -> QWidget:
        """تب درباره برنامه"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("📱 Enterprise ERP")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #7c3aed;")
        layout.addWidget(title)

        version = QLabel("نسخه 2.5.0 — تم پویا و هوشمند")
        version.setObjectName("aboutVersion")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        desc = QLabel(
            "سیستم یکپارچه مدیریت منابع سازمانی (ERP)\n"
            "توسعه‌یافته با Python و فریم‌ورک قدرتمند PySide6\n\n"
            "© تمامی حقوق محفوظ است."
        )
        desc.setObjectName("aboutDesc")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        info_group = QGroupBox("اطلاعات محیط اجرا")
        info_group.setObjectName("settingsGroup")
        info_layout = QFormLayout(info_group)

        info_layout.addRow("🐍 نسخه Python:", QLabel(f"{sys.version.split()[0]}"))
        info_layout.addRow("📦 نسخه PySide6:", QLabel("6.8.0"))
        info_layout.addRow("💾 دیتابیس:", QLabel("SQLite 3"))
        info_layout.addRow("🖥️ سیستم‌عامل:", QLabel(sys.platform))

        layout.addWidget(info_group)
        layout.addStretch()
        return tab

    # ========================================================================
    # متدهای اختصاصی اعمال زنده تم و رنگ‌ها به کل نرم‌افزار
    # ========================================================================

    def _apply_preset_palette(self, primary: str, secondary: str):
        """اعمال پالت رنگی آماده به صورت سراسری"""
        theme_manager.set_primary_color(primary)
        theme_manager.set_secondary_color(secondary)
        self._sync_global_styles()

    def _select_color(self, color_type: str):
        """انتخاب رنگ دلخواه از پالت استاندارد و اعمال به کل برنامه"""
        curr = theme_manager.get_primary_color() if color_type == "primary" else theme_manager.get_secondary_color()
        color = QColorDialog.getColor(QColor(curr), self, f"انتخاب رنگ {'اصلی' if color_type == 'primary' else 'ثانویه'}")
        if color.isValid():
            hex_val = color.name()
            if color_type == "primary":
                theme_manager.set_primary_color(hex_val)
            else:
                theme_manager.set_secondary_color(hex_val)
            self._sync_global_styles()

    def _sync_global_styles(self):
        """همگام‌سازی و اعمال بلادرنگ استایل‌شیت به کل برنامه (QApplication)"""
        p_col = theme_manager.get_primary_color()
        s_col = theme_manager.get_secondary_color()

        # ۱. بروزرسانی پیش‌نمایش و دکمه‌های صفحه تنظیمات
        self._on_colors_changed({"primary": p_col, "secondary": s_col})

        # ۲. تولید استایل‌شیت جدید سراسری و تزریق به اپلیکیشن
        app = QApplication.instance()
        if app:
            # اگر ThemeManager متد اعمال استایل دارد صدا می‌زند، وگرنه استایل تولیدی را مستقیم ست می‌کند
            if hasattr(theme_manager, "apply_theme"):
                theme_manager.apply_theme()
            elif hasattr(theme_manager, "get_stylesheet"):
                app.setStyleSheet(theme_manager.get_stylesheet())
            else:
                # استایل پایه استاندارد با رنگ‌های جدید برای تمام صفحات
                new_qss = f"""
                    #btnPrimary {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p_col}, stop:1 {s_col});
                        color: #ffffff;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: bold;
                        border: none;
                    }}
                    #btnPrimary:hover {{
                        background: {p_col};
                    }}
                    QTabBar::tab:selected {{
                        background: {p_col};
                        color: white;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                    }}
                """
                app.setStyleSheet(app.styleSheet() + "\n" + new_qss)

    def _on_theme_radio_changed(self, theme: str):
        """تغییر تم از رادیو باتن"""
        if theme == "light" and self.theme_light.isChecked():
            theme_manager.set_theme("light")
        elif theme == "dark" and self.theme_dark.isChecked():
            theme_manager.set_theme("dark")
        elif theme == "system" and self.theme_system.isChecked():
            theme_manager.set_theme("system")
        self._sync_global_styles()

    def _on_theme_changed(self, theme: str):
        """واکنش به سیگنال تغییر تم"""
        self.theme_light.blockSignals(True)
        self.theme_dark.blockSignals(True)
        self.theme_system.blockSignals(True)
        
        if theme == "dark":
            self.theme_dark.setChecked(True)
        elif theme == "system":
            self.theme_system.setChecked(True)
        else:
            self.theme_light.setChecked(True)
        
        self.theme_light.blockSignals(False)
        self.theme_dark.blockSignals(False)
        self.theme_system.blockSignals(False)

    def _on_colors_changed(self, colors: dict):
        """بروزرسانی بصری دکمه‌های رنگ و نوار پیش‌نمایش"""
        p_col = colors.get("primary", theme_manager.get_primary_color())
        s_col = colors.get("secondary", theme_manager.get_secondary_color())

        if hasattr(self, "primary_color_btn"):
            self.primary_color_btn.setStyleSheet(f"""
                background-color: {p_col};
                color: #ffffff;
                font-weight: bold;
                border-radius: 8px;
                min-height: 32px;
                border: 2px solid #ede8f5;
            """)
            self.primary_color_btn.setText(f"رنگ اصلی: {p_col.upper()}")

        if hasattr(self, "secondary_color_btn"):
            self.secondary_color_btn.setStyleSheet(f"""
                background-color: {s_col};
                color: #ffffff;
                font-weight: bold;
                border-radius: 8px;
                min-height: 32px;
                border: 2px solid #ede8f5;
            """)
            self.secondary_color_btn.setText(f"رنگ ثانویه: {s_col.upper()}")

        if hasattr(self, "theme_preview"):
            self.theme_preview.setStyleSheet(f"""
                #themePreview {{
                    border: 2px solid #ede8f5;
                    border-radius: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {p_col}, stop:1 {s_col});
                }}
            """)

    def _on_font_changed(self, size: int):
        self.font_size.blockSignals(True)
        self.font_size.setValue(size)
        self.font_size.blockSignals(False)

    def _on_font_size_changed(self, size: int):
        theme_manager.set_font_size(size)
        self._sync_global_styles()

    def _select_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.font_size.setValue(font.pointSize())

    def _reset_appearance(self):
        reply = QMessageBox.question(
            self,
            "بازنشانی",
            "آیا از بازنشانی رنگ‌ها و تم به حالت بنفش پیش‌فرض اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            theme_manager.set_theme("light")
            theme_manager.set_primary_color("#7c3aed")
            theme_manager.set_secondary_color("#5b21b6")
            theme_manager.set_font_size(12)
            self._sync_global_styles()
            QMessageBox.information(self, "موفق", "تنظیمات ظاهر بازنشانی شد.")

    # ========================================================================
    # توابع بارگذاری و ذخیره تنظیمات
    # ========================================================================

    def _load_settings(self):
        """بارگذاری تنظیمات ذخیره شده"""
        settings = QSettings("EnterpriseERP", "Settings")

        self.company_name.setText(settings.value("general/company_name", ""))
        self.app_name.setText(settings.value("general/app_name", "Enterprise ERP"))
        
        currency_index = self.currency.findText(settings.value("general/currency", "ریال"))
        if currency_index >= 0:
            self.currency.setCurrentIndex(currency_index)

        date_format_index = self.date_format.findText(settings.value("general/date_format", "YYYY/MM/DD"))
        if date_format_index >= 0:
            self.date_format.setCurrentIndex(date_format_index)

        self.default_discount.setValue(float(settings.value("defaults/discount", 0)))
        self.default_tax.setValue(float(settings.value("defaults/tax", 0)))

        # تم و رنگ‌ها
        theme = theme_manager.get_theme()
        self._on_theme_changed(theme)
        self.font_size.setValue(theme_manager.get_font_size())
        self._on_colors_changed({
            "primary": theme_manager.get_primary_color(),
            "secondary": theme_manager.get_secondary_color()
        })

    def _save_settings(self):
        """ذخیره تنظیمات و اعمال کامل تم و رنگ‌ها به صورت سراسری"""
        settings = QSettings("EnterpriseERP", "Settings")

        # ذخیره تنظیمات عمومی
        settings.setValue("general/company_name", self.company_name.text())
        settings.setValue("general/app_name", self.app_name.text())
        settings.setValue("general/currency", self.currency.currentText())
        settings.setValue("general/date_format", self.date_format.currentText())

        settings.setValue("defaults/discount", self.default_discount.value())
        settings.setValue("defaults/tax", self.default_tax.value())

        # اعمال مقادیر انتخاب شده در تم و رنگ‌ها به ThemeManager
        if self.theme_light.isChecked():
            theme_manager.set_theme("light")
        elif self.theme_dark.isChecked():
            theme_manager.set_theme("dark")
        elif self.theme_system.isChecked():
            theme_manager.set_theme("system")

        theme_manager.set_primary_color(theme_manager.get_primary_color())
        theme_manager.set_secondary_color(theme_manager.get_secondary_color())
        theme_manager.set_font_size(self.font_size.value())

        # فراخوانی کامل اعمال تم روی کل برنامه
        self._sync_global_styles()
        
        QMessageBox.information(self, "موفق", "تنظیمات سیستم و تم با موفقیت ذخیره و اعمال شد.")

    # ========================================================================
    # توابع دیتابیس
    # ========================================================================

    def _update_db_info(self):
        try:
            db_path = Path(DB_PATH)
            if db_path.exists():
                size = db_path.stat().st_size
                self.db_size_label.setText(self._format_size(size))

            with get_connection() as conn:
                tables = conn.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'").fetchone()
                self.db_tables_label.setText(str(tables["count"]))

                total_records = 0
                for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    try:
                        count = conn.execute(f"SELECT COUNT(*) as count FROM {table['name']}").fetchone()
                        total_records += count["count"]
                    except:
                        pass
                self.db_records_label.setText(f"{total_records:,}")

        except Exception:
            self.db_size_label.setText("خطا")
            self.db_tables_label.setText("خطا")
            self.db_records_label.setText("خطا")

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def _optimize_database(self):
        try:
            with get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            QMessageBox.information(self, "موفق", "دیتابیس با موفقیت بهینه‌سازی شد.")
            self._update_db_info()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بهینه‌سازی دیتابیس:\n{str(e)}")

    def _check_database(self):
        try:
            with get_connection() as conn:
                conn.execute("PRAGMA integrity_check")
            QMessageBox.information(self, "موفق", "دیتابیس سالم است.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"دیتابیس مشکل دارد:\n{str(e)}")

    def _export_database(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "خروجی دیتابیس",
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
            "SQL Files (*.sql)"
        )

        if file_path:
            try:
                import subprocess
                cmd = f'sqlite3 "{DB_PATH}" .dump > "{file_path}"'
                subprocess.run(cmd, shell=True, check=True)
                QMessageBox.information(self, "موفق", f"خروجی دیتابیس در مسیر زیر ذخیره شد:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در خروجی دیتابیس:\n{str(e)}")

    # ========================================================================
    # توابع پشتیبان‌گیری
    # ========================================================================

    def _create_backup(self):
        try:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"enterprise_backup_{timestamp}.db"

            shutil.copy2(DB_PATH, backup_path)
            QMessageBox.information(self, "موفق", f"پشتیبان با موفقیت ایجاد شد.\nمسیر: {backup_path}")
            self._refresh_backup_list()

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد پشتیبان:\n{str(e)}")

    def _restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل پشتیبان", "backups/", "Database Files (*.db)"
        )
        if file_path:
            self._restore_from_file(file_path)

    def _restore_backup_from_list(self, item: QListWidgetItem):
        file_path = item.data(Qt.UserRole)
        if file_path:
            reply = QMessageBox.question(
                self, "تأیید بازیابی",
                "آیا از بازیابی این پشتیبان اطمینان دارید؟ داده‌های فعلی جایگزین خواهند شد.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._restore_from_file(file_path)

    def _restore_from_file(self, file_path: str):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            current_backup = backup_dir / f"enterprise_before_restore_{timestamp}.db"
            shutil.copy2(DB_PATH, current_backup)

            shutil.copy2(file_path, DB_PATH)
            QMessageBox.information(self, "موفق", "پشتیبان با موفقیت بازیابی شد.")
            self._refresh_backup_list()

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بازیابی پشتیبان:\n{str(e)}")

    def _refresh_backup_list(self):
        self.backup_list.clear()
        backup_dir = Path("backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("enterprise_backup_*.db"), reverse=True)
            for backup in backups[:20]:
                size = backup.stat().st_size
                item = QListWidgetItem(f"{backup.name} ({self._format_size(size)})")
                item.setData(Qt.UserRole, str(backup))
                self.backup_list.addItem(item)

            if not backups:
                self.backup_list.addItem("هیچ پشتیبانی یافت نشد.")

    # ========================================================================
    # توابع مدیریت کاربران
    # ========================================================================

    def _load_users(self):
        try:
            with get_connection() as conn:
                rows = conn.execute("""
                    SELECT id, username, full_name, role, is_active
                    FROM users
                    ORDER BY id
                """).fetchall()

                self.users_table.setRowCount(len(rows))

                for r, row in enumerate(rows):
                    values = [
                        str(row["id"]),
                        row["username"],
                        row["full_name"] or "-",
                        self._get_role_persian(row["role"]),
                        "فعال" if row["is_active"] else "غیرفعال"
                    ]
                    for c, val in enumerate(values):
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.users_table.setItem(r, c, item)

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری کاربران:\n{str(e)}")

    def _get_role_persian(self, role: str) -> str:
        roles = {
            "admin": "مدیر سیستم",
            "manager": "مدیر",
            "user": "کاربر",
            "viewer": "بیننده"
        }
        return roles.get(role, role)

    def _add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            self._load_users()
            QMessageBox.information(self, "موفق", "کاربر با موفقیت اضافه شد.")

    def _edit_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک کاربر را انتخاب کنید.")
            return

        user_id = self.users_table.item(row, 0).text()
        dialog = UserDialog(self, int(user_id))
        if dialog.exec():
            self._load_users()
            QMessageBox.information(self, "موفق", "کاربر با موفقیت ویرایش شد.")

    def _delete_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "خطا", "لطفاً یک کاربر را انتخاب کنید.")
            return

        user_id = self.users_table.item(row, 0).text()
        username = self.users_table.item(row, 1).text()

        if Session.current_user and Session.current_user.get("id") == int(user_id):
            QMessageBox.warning(self, "خطا", "نمی‌توانید کاربر فعلی را حذف کنید.")
            return

        reply = QMessageBox.question(
            self, "تأیید حذف", f"آیا از حذف کاربر «{username}» اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                with get_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.commit()
                self._load_users()
                QMessageBox.information(self, "موفق", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در حذف کاربر:\n{str(e)}")


class UserDialog(QDialog):
    """دیالوگ افزودن/ویرایش کاربر"""

    def __init__(self, parent: QWidget | None = None, user_id: int | None = None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("ویرایش کاربر" if user_id else "افزودن کاربر جدید")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(400)
        self.setup_ui()
        if user_id:
            self.load_user_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(8)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("نام کاربری...")
        form.addRow("👤 نام کاربری:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("رمز عبور...")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("🔑 رمز عبور:", self.password_edit)

        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("تکرار رمز عبور...")
        self.password_confirm.setEchoMode(QLineEdit.Password)
        form.addRow("🔑 تکرار رمز:", self.password_confirm)

        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("نام و نام خانوادگی...")
        form.addRow("👤 نام کامل:", self.full_name_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["مدیر سیستم", "مدیر", "کاربر", "بیننده"])
        form.addRow("🎯 نقش:", self.role_combo)

        self.is_active = QCheckBox("فعال")
        self.is_active.setChecked(True)
        form.addRow("✅ وضعیت:", self.is_active)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.Cancel).setText("انصراف")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def load_user_data(self):
        try:
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT username, full_name, role, is_active FROM users WHERE id = ?",
                    (self.user_id,)
                ).fetchone()

                if row:
                    self.username_edit.setText(row["username"])
                    self.full_name_edit.setText(row["full_name"] or "")
                    
                    role_index = self.role_combo.findText(self._get_role_persian(row["role"]))
                    if role_index >= 0:
                        self.role_combo.setCurrentIndex(role_index)
                    
                    self.is_active.setChecked(bool(row["is_active"]))
                    self.username_edit.setReadOnly(True)
                    self.password_edit.setPlaceholderText("برای تغییر رمز عبور وارد کنید...")

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری کاربر:\n{str(e)}")

    def _get_role_persian(self, role: str) -> str:
        roles = {
            "admin": "مدیر سیستم",
            "manager": "مدیر",
            "user": "کاربر",
            "viewer": "بیننده"
        }
        return roles.get(role, role)

    def _get_role_english(self, role_persian: str) -> str:
        roles = {
            "مدیر سیستم": "admin",
            "مدیر": "manager",
            "کاربر": "user",
            "بیننده": "viewer"
        }
        return roles.get(role_persian, "user")

    def accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        password_confirm = self.password_confirm.text()
        full_name = self.full_name_edit.text().strip()
        role_persian = self.role_combo.currentText()
        role = self._get_role_english(role_persian)
        is_active = 1 if self.is_active.isChecked() else 0

        if not username:
            QMessageBox.warning(self, "خطا", "نام کاربری اجباری است.")
            return

        if not self.user_id and not password:
            QMessageBox.warning(self, "خطا", "رمز عبور اجباری است.")
            return

        if password and password != password_confirm:
            QMessageBox.warning(self, "خطا", "رمز عبور و تکرار آن مطابقت ندارند.")
            return

        try:
            with get_connection() as conn:
                if self.user_id:
                    if password:
                        conn.execute("""
                            UPDATE users 
                            SET username=?, password_hash=?, full_name=?, role=?, is_active=?
                            WHERE id=?
                        """, (username, self._hash_password(password), full_name, role, is_active, self.user_id))
                    else:
                        conn.execute("""
                            UPDATE users 
                            SET username=?, full_name=?, role=?, is_active=?
                            WHERE id=?
                        """, (username, full_name, role, is_active, self.user_id))
                else:
                    conn.execute("""
                        INSERT INTO users (username, password_hash, full_name, role, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, self._hash_password(password), full_name, role, is_active))

                conn.commit()
                super().accept()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلاً ثبت شده است.")
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره کاربر:\n{str(e)}")

    def _hash_password(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()