import sqlite3

import bcrypt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QCheckBox, QMessageBox, QDialogButtonBox,
)

from app.core.session import Session
from app.database.connection import get_connection


class UserDialog(QDialog):
    """دیالوگ افزودن یا ویرایش کاربر."""

    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("ویرایش کاربر" if user else "افزودن کاربر")
        self.setMinimumWidth(380)

        form = QFormLayout(self)
        form.setSpacing(12)

        self.username_input = QLineEdit()
        self.fullname_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.active_checkbox = QCheckBox("حساب فعال باشد")
        self.active_checkbox.setChecked(True)

        form.addRow("نام کاربری:", self.username_input)
        form.addRow("نام کامل:", self.fullname_input)
        form.addRow("ایمیل:", self.email_input)
        password_label = "رمز عبور (خالی = بدون تغییر):" if user else "رمز عبور:"
        form.addRow(password_label, self.password_input)
        form.addRow("", self.active_checkbox)

        if user:
            self.username_input.setText(user["username"])
            self.fullname_input.setText(user.get("full_name") or "")
            self.email_input.setText(user.get("email") or "")
            self.active_checkbox.setChecked(bool(user.get("is_active", 1)))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("ذخیره")
        buttons.button(QDialogButtonBox.Cancel).setText("انصراف")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self.setStyleSheet("""
            QDialog { background: #faf8ff; }
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #d5cbf0;
                border-radius: 8px;
                background: white;
            }
            QLineEdit:focus { border: 1px solid #7657c8; }
            QPushButton {
                background: #7657c8; color: white;
                border: none; border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #5a3fa8; }
        """)

    def _validate_and_accept(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "خطا", "نام کاربری را وارد کنید.")
            return
        if self.user is None and not self.password_input.text():
            QMessageBox.warning(self, "خطا", "رمز عبور را وارد کنید.")
            return
        self.accept()

    def get_data(self):
        return {
            "username": self.username_input.text().strip(),
            "full_name": self.fullname_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.password_input.text(),
            "is_active": 1 if self.active_checkbox.isChecked() else 0,
        }


class UsersPage(QWidget):
    """صفحه مدیریت کاربران: جدول، جست‌وجو، افزودن/ویرایش/حذف."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # هدر
        header = QHBoxLayout()
        title = QLabel("مدیریت کاربران")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4a3a7a;")
        header.addWidget(title)
        header.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جست‌وجو…")
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.load_users)
        header.addWidget(self.search_input)

        add_btn = QPushButton("＋ افزودن کاربر")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_user)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # جدول
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["شناسه", "نام کاربری", "نام کامل", "ایمیل", "وضعیت", "عملیات"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #d5cbf0;
                border-radius: 8px;
                background: white;
            }
            QLineEdit:focus { border: 1px solid #7657c8; }
            QPushButton {
                background: #7657c8; color: white;
                border: none; border-radius: 8px;
                padding: 9px 18px; font-size: 13px;
            }
            QPushButton:hover { background: #5a3fa8; }
            QTableWidget {
                background: white;
                border: 1px solid #e3dcf7;
                border-radius: 10px;
                gridline-color: #efeafc;
            }
            QHeaderView::section {
                background: #ede7fb; color: #4a3a7a;
                padding: 10px; border: none; font-weight: bold;
            }
        """)

        self.load_users()

    # ---------- داده ----------

    def load_users(self):
        term = self.search_input.text().strip()
        conn = get_connection()
        if term:
            rows = conn.execute(
                """SELECT id, username, full_name, email, is_active FROM users
                   WHERE username LIKE ? OR full_name LIKE ? OR email LIKE ?
                   ORDER BY id""",
                (f"%{term}%", f"%{term}%", f"%{term}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, username, full_name, email, is_active FROM users ORDER BY id"
            ).fetchall()

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            user = dict(row)
            self.table.setItem(r, 0, QTableWidgetItem(str(user["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(user["username"]))
            self.table.setItem(r, 2, QTableWidgetItem(user.get("full_name") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(user.get("email") or "—"))
            status = QTableWidgetItem("فعال" if user.get("is_active", 1) else "غیرفعال")
            status.setForeground(Qt.darkGreen if user.get("is_active", 1) else Qt.red)
            self.table.setItem(r, 4, status)

            actions = QWidget()
            h = QHBoxLayout(actions)
            h.setContentsMargins(4, 2, 4, 2)
            edit_btn = QPushButton("ویرایش")
            del_btn = QPushButton("حذف")
            del_btn.setStyleSheet(
                "background: #e05c6a; border-radius: 6px; padding: 5px 12px;"
            )
            edit_btn.setStyleSheet(
                "background: #9b7fe0; border-radius: 6px; padding: 5px 12px;"
            )
            edit_btn.clicked.connect(lambda _, u=user: self.edit_user(u))
            del_btn.clicked.connect(lambda _, u=user: self.delete_user(u))
            h.addWidget(edit_btn)
            h.addWidget(del_btn)
            self.table.setCellWidget(r, 5, actions)

    # ---------- عملیات ----------

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        password_hash = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO users (username, password_hash, full_name, email, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                (data["username"], password_hash, data["full_name"],
                 data["email"], data["is_active"]),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلاً ثبت شده است.")
            return
        self.load_users()

    def edit_user(self, user):
        dialog = UserDialog(self, user=user)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        conn = get_connection()
        conn.execute(
            """UPDATE users SET username = ?, full_name = ?, email = ?, is_active = ?
               WHERE id = ?""",
            (data["username"], data["full_name"], data["email"],
             data["is_active"], user["id"]),
        )
        if data["password"]:
            password_hash = bcrypt.hashpw(
                data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (password_hash, user["id"]),
            )
        conn.commit()
        self.load_users()

    def delete_user(self, user):
        current = Session.current_user or {}
        if user["id"] == current.get("id"):
            QMessageBox.warning(self, "خطا", "نمی‌توانید حساب خودتان را حذف کنید.")
            return
        answer = QMessageBox.question(
            self, "حذف کاربر",
            f"کاربر «{user['username']}» حذف شود؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        conn = get_connection()
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        conn.commit()
        self.load_users()
