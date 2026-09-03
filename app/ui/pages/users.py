# -*- coding: utf-8 -*-
import sqlite3
import bcrypt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QComboBox, QCheckBox, QMessageBox, QDialogButtonBox, QGroupBox,
)

from app.database.connection import get_connection
from app.core.session import Session

# کلید دسترسی -> عنوان فارسی (باید با منوهای داشبورد یکی باشد)
PAGE_PERMISSIONS = [
    ("users", "مدیریت کاربران"),
    ("products", "کالاها"),
    ("customers", "مشتریان"),
    ("invoices", "فاکتورها"),
    ("accounting", "حسابداری"),
    ("reports", "گزارش‌ها"),
]


class UserDialog(QDialog):
    """افزودن/ویرایش کاربر. در حالت ویرایش، رمز خالی یعنی بدون تغییر."""

    def __init__(self, parent=None, user: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("ویرایش کاربر" if user else "افزودن کاربر")
        self.setMinimumWidth(380)

        form = QFormLayout(self)
        self.username_input = QLineEdit(user["username"] if user else "")
        self.fullname_input = QLineEdit(user.get("full_name") or "" if user else "")
        self.email_input = QLineEdit(user.get("email") or "" if user else "")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        if user:
            self.password_input.setPlaceholderText("خالی = بدون تغییر")

        self.role_combo = QComboBox()
        self.role_combo.addItem("کاربر عادی", "user")
        self.role_combo.addItem("مدیر", "admin")
        if user and user.get("role") == "admin":
            self.role_combo.setCurrentIndex(1)

        self.active_check = QCheckBox("فعال")
        self.active_check.setChecked(bool(user["is_active"]) if user else True)

        form.addRow("نام کاربری:", self.username_input)
        form.addRow("نام کامل:", self.fullname_input)
        form.addRow("ایمیل:", self.email_input)
        form.addRow("رمز عبور:", self.password_input)
        form.addRow("نقش:", self.role_combo)
        form.addRow("", self.active_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self._is_edit = user is not None

    def _validate(self):
        if not self.username_input.text().strip():
            QMessageBox.warning(self, "خطا", "نام کاربری الزامی است.")
            return
        if not self._is_edit and not self.password_input.text():
            QMessageBox.warning(self, "خطا", "رمز عبور برای کاربر جدید الزامی است.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "username": self.username_input.text().strip(),
            "full_name": self.fullname_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.password_input.text(),
            "role": self.role_combo.currentData(),
            "is_active": 1 if self.active_check.isChecked() else 0,
        }


class PermissionsDialog(QDialog):
    """تعیین دسترسی کاربر به صفحات داشبورد با چک‌باکس."""

    def __init__(self, parent=None, username: str = "", current: str = ""):
        super().__init__(parent)
        self.setWindowTitle(f"دسترسی‌های {username}")
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)

        box = QGroupBox("صفحات مجاز")
        box_layout = QVBoxLayout(box)
        current_set = {p for p in current.split(",") if p}
        self._checks: dict[str, QCheckBox] = {}
        for key, title in PAGE_PERMISSIONS:
            cb = QCheckBox(title)
            cb.setChecked(key in current_set)
            self._checks[key] = cb
            box_layout.addWidget(cb)
        layout.addWidget(box)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_permissions(self) -> str:
        return ",".join(k for k, cb in self._checks.items() if cb.isChecked())


class UsersPage(QWidget):
    COLUMNS = ["شناسه", "نام کاربری", "نام کامل", "ایمیل", "نقش", "وضعیت", "عملیات"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("مدیریت کاربران")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4c1d95;")
        layout.addWidget(title)

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جست‌وجو بر اساس نام کاربری، نام یا ایمیل...")
        self.search_input.textChanged.connect(self.load_users)
        add_btn = QPushButton("+ افزودن کاربر")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton{background:#7c3aed;color:white;border-radius:8px;"
            "padding:8px 16px;font-weight:bold;}"
            "QPushButton:hover{background:#6d28d9;}"
        )
        add_btn.clicked.connect(self.add_user)
        top.addWidget(self.search_input, 1)
        top.addWidget(add_btn)
        layout.addLayout(top)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 220)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

    # ---------- داده ----------

    def load_users(self):
        term = f"%{self.search_input.text().strip()}%" if hasattr(self, "search_input") else "%%"
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, username, full_name, email, role, permissions, is_active "
                "FROM users WHERE username LIKE ? OR full_name LIKE ? OR email LIKE ? "
                "ORDER BY id",
                (term, term, term),
            ).fetchall()
        except sqlite3.OperationalError:
            # اگر ستون permissions هنوز ساخته نشده باشد
            rows = conn.execute(
                "SELECT id, username, full_name, email, role, is_active "
                "FROM users WHERE username LIKE ? OR full_name LIKE ? OR email LIKE ? "
                "ORDER BY id",
                (term, term, term),
            ).fetchall()
        finally:
            conn.close()

        self.table.setRowCount(0)
        for row in rows:
            user = dict(row)
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                str(user["id"]), user["username"], user.get("full_name") or "—",
                user.get("email") or "—",
                "مدیر" if user["role"] == "admin" else "کاربر عادی",
                "فعال" if user["is_active"] else "غیرفعال",
            ]
            for c, v in enumerate(values):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
            self.table.setCellWidget(r, 6, self._action_buttons(user))
            self.table.setRowHeight(r, 44)

    def _action_buttons(self, user: dict) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(6)
        style = ("QPushButton{{background:{bg};color:white;border-radius:6px;"
                 "padding:4px 10px;}} QPushButton:hover{{background:{hover};}}")

        edit_btn = QPushButton("ویرایش")
        edit_btn.setStyleSheet(style.format(bg="#8b5cf6", hover="#7c3aed"))
        edit_btn.clicked.connect(lambda _, u=user: self.edit_user(u))

        perm_btn = QPushButton("دسترسی")
        perm_btn.setStyleSheet(style.format(bg="#0ea5e9", hover="#0284c7"))
        perm_btn.clicked.connect(lambda _, u=user: self.set_permissions(u))

        del_btn = QPushButton("حذف")
        del_btn.setStyleSheet(style.format(bg="#ef4444", hover="#dc2626"))
        del_btn.clicked.connect(lambda _, u=user: self.delete_user(u))

        for b in (edit_btn, perm_btn, del_btn):
            b.setCursor(Qt.PointingHandCursor)
            h.addWidget(b)
        return w

    # ---------- عملیات ----------

    def add_user(self):
        dlg = UserDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        password_hash = bcrypt.hashpw(
            d["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, email, role, permissions, is_active) "
                "VALUES (?, ?, ?, ?, ?, '', ?)",
                (d["username"], password_hash, d["full_name"], d["email"], d["role"], d["is_active"]),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلاً ثبت شده است.")
        finally:
            conn.close()
        self.load_users()

    def edit_user(self, user: dict):
        dlg = UserDialog(self, user=user)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        conn = get_connection()
        try:
            if d["password"]:
                password_hash = bcrypt.hashpw(
                    d["password"].encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                conn.execute(
                    "UPDATE users SET username=?, full_name=?, email=?, role=?, is_active=?, password_hash=? WHERE id=?",
                    (d["username"], d["full_name"], d["email"], d["role"], d["is_active"], password_hash, user["id"]),
                )
            else:
                conn.execute(
                    "UPDATE users SET username=?, full_name=?, email=?, role=?, is_active=? WHERE id=?",
                    (d["username"], d["full_name"], d["email"], d["role"], d["is_active"], user["id"]),
                )
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطا", "این نام کاربری قبلاً ثبت شده است.")
        finally:
            conn.close()
        self.load_users()

    def set_permissions(self, user: dict):
        if user["role"] == "admin":
            QMessageBox.information(self, "دسترسی", "مدیر به همه‌ی بخش‌ها دسترسی کامل دارد.")
            return
        dlg = PermissionsDialog(self, username=user["username"],
                                current=user.get("permissions") or "")
        if dlg.exec() != QDialog.Accepted:
            return
        conn = get_connection()
        try:
            conn.execute("UPDATE users SET permissions=? WHERE id=?",
                         (dlg.get_permissions(), user["id"]))
            conn.commit()
        finally:
            conn.close()
        self.load_users()

    def delete_user(self, user: dict):
        current = Session.current_user or {}
        if current.get("id") == user["id"]:
            QMessageBox.warning(self, "خطا", "نمی‌توانید حساب کاربری خودتان را حذف کنید.")
            return
        if QMessageBox.question(
            self, "حذف کاربر",
            f"کاربر «{user['username']}» حذف شود؟",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        conn = get_connection()
        try:
            conn.execute("DELETE FROM users WHERE id=?", (user["id"],))
            conn.commit()
        finally:
            conn.close()
        self.load_users()