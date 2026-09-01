# -*- coding: utf-8 -*-
"""نقطه ورود اصلی برنامه - Enterprise ERP"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from app.database.migrations import run_migrations, DB_PATH
from app.ui.login import LoginWindow
from app.core.theme_manager import theme_manager

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "app" / "assets" / "images" / "Enterprise.ico"


def main() -> int:
    """نقطه ورود اصلی برنامه"""
    
    # ایجاد برنامه Qt
    app = QApplication(sys.argv)
    
    # تنظیمات High DPI برای نمایش بهتر در مانیتورهای با رزولوشن بالا
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # تنظیم آیکون کل برنامه (Taskbar و همه پنجره‌ها)
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    else:
        print(f"⚠️ آیکون در مسیر {ICON_PATH} یافت نشد.")
    
    # اعمال تم اولیه برنامه
    try:
        theme_manager.apply_theme()
        print("✅ تم برنامه اعمال شد.")
    except Exception as e:
        print(f"⚠️ خطا در اعمال تم: {e}")
    
    # همگام‌سازی اسکیمای دیتابیس پیش از ساختن هر پنجره
    try:
        changes = run_migrations()
        print(f"[db] {DB_PATH}")
        if changes:
            print(f"[db] مهاجرت اعمال شد: {', '.join(changes)}")
    except Exception as exc:
        # دیتابیس قابل مهاجرت نیست → ادامه بی‌معنی است
        QMessageBox.critical(
            None,
            "❌ خطای دیتابیس",
            f"مهاجرت دیتابیس شکست خورد:\n{DB_PATH}\n\n{exc}",
        )
        return 1
    
    # ایجاد و نمایش پنجره ورود
    try:
        window = LoginWindow()
        window.show()
        print("✅ پنجره ورود نمایش داده شد.")
    except Exception as e:
        QMessageBox.critical(
            None,
            "❌ خطای برنامه",
            f"خطا در بارگذاری پنجره ورود:\n\n{str(e)}",
        )
        return 1
    
    # اجرای حلقه اصلی برنامه
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())