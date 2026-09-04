# -*- coding: utf-8 -*-
"""صفحه حسابداری - مدیریت اسناد، ترازنامه، دفتر کل و ثبت چک‌ها"""

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDoubleSpinBox, QDialogButtonBox,
    QTabWidget, QDateEdit, QComboBox
)

from app.database.connection import get_connection


class NewDocDialog(QDialog):
    """فرم ثبت سند حسابداری جدید"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ثبت سند حسابداری جدید")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.doc_number = QLineEdit()
        self.doc_number.setPlaceholderText("مثلاً: 1001")
        form.addRow("شماره سند:", self.doc_number)

        self.date = QLineEdit()
        self.date.setPlaceholderText("1403/01/01")
        form.addRow("تاریخ:", self.date)

        self.description = QTextEdit()
        self.description.setPlaceholderText("شرح سند...")
        self.description.setFixedHeight(80)
        form.addRow("شرح:", self.description)

        self.debit = QDoubleSpinBox()
        self.debit.setRange(0, 999999999)
        self.debit.setDecimals(0)
        self.debit.setSuffix(" ریال")
        form.addRow("بدهکار:", self.debit)

        self.credit = QDoubleSpinBox()
        self.credit.setRange(0, 999999999)
        self.credit.setDecimals(0)
        self.credit.setSuffix(" ریال")
        form.addRow("بستانکار:", self.credit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("ذخیره سند")
        buttons.button(QDialogButtonBox.Cancel).setText("انصراف")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _validate(self):
        if not self.doc_number.text().strip():
            QMessageBox.warning(self, "خطا", "شماره سند الزامی است.")
            return
        if not self.date.text().strip():
            QMessageBox.warning(self, "خطا", "تاریخ سند الزامی است.")
            return
        if self.debit.value() == 0 and self.credit.value() == 0:
            QMessageBox.warning(self, "خطا", "مبلغ بدهکار یا بستانکار باید وارد شود.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "doc_number": self.doc_number.text().strip(),
            "date": self.date.text().strip(),
            "description": self.description.toPlainText().strip(),
            "debit": self.debit.value(),
            "credit": self.credit.value(),
        }


class CheckDialog(QDialog):
    """فرم ثبت چک جدید"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ثبت چک جدید")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.check_number = QLineEdit()
        self.check_number.setPlaceholderText("شماره سریال چک...")
        form.addRow("شماره چک:", self.check_number)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 999999999)
        self.amount.setSuffix(" ریال")
        form.addRow("مبلغ:", self.amount)

        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate())
        form.addRow("تاریخ سررسید:", self.due_date)

        self.bank = QLineEdit()
        self.bank.setPlaceholderText("نام بانک...")
        form.addRow("بانک:", self.bank)

        self.status = QComboBox()
        self.status.addItem("دریافتی", "دریافتی")
        self.status.addItem("پرداختی", "پرداختی")
        form.addRow("نوع چک:", self.status)

        self.description = QTextEdit()
        self.description.setPlaceholderText("توضیحات چک...")
        self.description.setFixedHeight(60)
        form.addRow("توضیحات:", self.description)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("ذخیره چک")
        buttons.button(QDialogButtonBox.Cancel).setText("انصراف")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _validate(self):
        if not self.check_number.text().strip():
            QMessageBox.warning(self, "خطا", "شماره چک الزامی است.")
            return
        if self.amount.value() == 0:
            QMessageBox.warning(self, "خطا", "مبلغ چک الزامی است.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "check_number": self.check_number.text().strip(),
            "amount": self.amount.value(),
            "due_date": self.due_date.date().toString("yyyy/MM/dd"),
            "bank": self.bank.text().strip(),
            "status": self.status.currentData(),
            "description": self.description.toPlainText().strip(),
        }


class ChecksTab(QWidget):
    """تب مدیریت چک‌ها"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_checks()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ ثبت چک جدید")
        self.add_btn.setStyleSheet(
            "QPushButton{background:#7c3aed;color:white;border-radius:8px;padding:8px 16px;font-weight:bold;}"
            "QPushButton:hover{background:#6d28d9;}"
        )
        self.add_btn.clicked.connect(self._add_check)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["شماره چک", "مبلغ", "تاریخ سررسید", "بانک", "نوع", "توضیحات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _load_checks(self):
        """بارگذاری چک‌ها از دیتابیس"""
        try:
            with get_connection() as conn:
                rows = conn.execute("SELECT * FROM checks ORDER BY id DESC").fetchall()
                self.table.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    values = [
                        str(row["check_number"]),
                        f"{row['amount']:,}",
                        row["due_date"],
                        row["bank"],
                        row["status"],
                        row["description"] or "—"
                    ]
                    for c, val in enumerate(values):
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(r, c, item)
        except Exception:
            self.table.setRowCount(0)

    def _add_check(self):
        dlg = CheckDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()

        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO checks (check_number, amount, due_date, bank, status, description) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (data["check_number"], data["amount"], data["due_date"], data["bank"], data["status"], data["description"])
                )
            QMessageBox.information(self, "موفق", "چک با موفقیت ثبت شد.")
            self._load_checks()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ثبت چک:\n{str(e)}")


class AccountingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("accountingPage")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("📊 سیستم حسابداری")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4d3a78;")
        layout.addWidget(title)

        # ایجاد تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setObjectName("accountingTabs")

        # تب ۱: اسناد حسابداری (کد قبلی)
        self.docs_tab = QWidget()
        docs_layout = QVBoxLayout(self.docs_tab)
        docs_layout.setContentsMargins(10, 10, 10, 10)
        docs_layout.setSpacing(10)

        # دکمه‌های اسناد
        btn_layout = QHBoxLayout()
        self.btn_new_doc = QPushButton("➕ ثبت سند جدید")
        self.btn_new_doc.setObjectName("btnPrimary")
        self.btn_new_doc.setStyleSheet(
            "QPushButton{background:#7c3aed;color:white;border-radius:8px;padding:8px 16px;font-weight:bold;}"
            "QPushButton:hover{background:#6d28d9;}"
        )
        self.btn_new_doc.clicked.connect(self._create_new_doc)
        btn_layout.addWidget(self.btn_new_doc)

        self.btn_balance = QPushButton("📑 ترازنامه")
        self.btn_balance.setObjectName("btnSecondary")
        btn_layout.addWidget(self.btn_balance)

        self.btn_ledger = QPushButton("📒 دفتر کل")
        self.btn_ledger.setObjectName("btnSecondary")
        btn_layout.addWidget(self.btn_ledger)

        btn_layout.addStretch()
        docs_layout.addLayout(btn_layout)

        # جدول اسناد حسابداری
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["شماره سند", "تاریخ", "شرح", "بدهکار", "بستانکار"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        docs_layout.addWidget(self.table)

        self.tabs.addTab(self.docs_tab, "📒 اسناد حسابداری")

        # تب ۲: ثبت چک
        self.checks_tab = ChecksTab()
        self.tabs.addTab(self.checks_tab, "🏦 ثبت چک")

        layout.addWidget(self.tabs)

        self._load_data()

    def _load_data(self):
        """بارگذاری اسناد از دیتابیس"""
        try:
            with get_connection() as conn:
                rows = conn.execute("SELECT * FROM accounting_docs ORDER BY id DESC").fetchall()
                self.table.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    values = [
                        str(row["doc_number"]),
                        row["date"],
                        row["description"],
                        f"{row['debit']:,}",
                        f"{row['credit']:,}"
                    ]
                    for c, val in enumerate(values):
                        item = QTableWidgetItem(val)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(r, c, item)
        except Exception:
            self.table.setRowCount(0)

    def _create_new_doc(self):
        """باز کردن فرم ثبت سند جدید"""
        dlg = NewDocDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        data = dlg.get_data()

        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO accounting_docs (doc_number, date, description, debit, credit) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (data["doc_number"], data["date"], data["description"], data["debit"], data["credit"])
                )
            QMessageBox.information(self, "موفق", "سند حسابداری با موفقیت ثبت شد.")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ثبت سند:\n{str(e)}")