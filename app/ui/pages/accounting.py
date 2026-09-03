# -*- coding: utf-8 -*-
"""صفحه حسابداری - مدیریت اسناد، ترازنامه و دفتر کل"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDoubleSpinBox, QDialogButtonBox
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


class AccountingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("accountingPage")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # عنوان
        title = QLabel("📊 سیستم حسابداری")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4d3a78;")
        layout.addWidget(title)

        # دکمه‌ها
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
        layout.addLayout(btn_layout)

        # جدول اسناد حسابداری
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["شماره سند", "تاریخ", "شرح", "بدهکار", "بستانکار"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

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
            # اگر جدول هنوز ساخته نشده باشد
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