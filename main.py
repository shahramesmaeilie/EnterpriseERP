# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from app.ui.login import LoginWindow


def main():
    app = QApplication(sys.argv)

    # آیکون کل برنامه (Taskbar و همه‌ی پنجره‌ها این را به ارث می‌برند)
    app.setWindowIcon(QIcon("app/assets/images/Enterprise.ico"))

    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
