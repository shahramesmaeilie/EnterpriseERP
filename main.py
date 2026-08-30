import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from app.database.migrations import run_migrations, DB_PATH
from app.ui.login import LoginWindow

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "app" / "assets" / "images" / "Enterprise.ico"


def main() -> int:
    app = QApplication(sys.argv)

    # آیکون کل برنامه (Taskbar و همه‌ی پنجره‌ها این را به ارث می‌برند)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    # همگام‌سازی اسکیمای دیتابیس پیش از ساختن هر پنجره
    try:
        changes = run_migrations()
    except Exception as exc:  # دیتابیس قابل مهاجرت نیست → ادامه بی‌معنی است
        QMessageBox.critical(
            None,
            "خطای دیتابیس",
            f"مهاجرت دیتابیس شکست خورد:\n{DB_PATH}\n\n{exc}",
        )
        return 1

    print(f"[db] {DB_PATH}")
    if changes:
        print("[db] مهاجرت اعمال شد:", ", ".join(changes))

    window = LoginWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
