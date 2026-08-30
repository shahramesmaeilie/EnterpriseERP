# -*- coding: utf-8 -*-
"""صفحه فروش: فاکتور با اسکن بارکد/QR، چاپ و مدیریت مشتریان"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSpinBox, QSplitter, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from app.core.session import Session

try:  # مسیر دیتابیس را با migrations یکسان نگه می‌داریم
    from app.database.migrations import DB_PATH
except Exception:  # pragma: no cover
    DB_PATH = Path(__file__).resolve().parents[3] / "enterprise.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _money(value: float) -> str:
    return f"{value:,.0f}"


# ============================================================================
# مدل‌های ساده
# ============================================================================
class Product:
    def __init__(self, id: int, name: str, barcode: str, unit_price: float, quantity: int = 0):
        self.id = id
        self.name = name
        self.barcode = barcode
        self.unit_price = unit_price
        self.quantity = quantity


class Customer:
    def __init__(self, id: int | None, name: str, phone: str = "", address: str = ""):
        self.id = id
        self.name = name
        self.phone = phone
        self.address = address


class InvoiceItem:
    def __init__(self, product_id: int, product_name: str, quantity: int, unit_price: float):
        self.product_id = product_id
        self.product_name = product_name
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


# ============================================================================
# سرویس‌ها
# ============================================================================
class ProductService:
    @staticmethod
    def find_for_scan(term: str) -> Product | None:
        term = term.strip()
        if not term:
            return None
        sql = """
            SELECT id, name, barcode,
                   COALESCE(retail_price, unit_price, price, 0) AS unit_price,
                   COALESCE(quantity, stock, 0) AS quantity
            FROM products
            WHERE barcode = ? OR name LIKE ? OR id = ?
            ORDER BY CASE WHEN barcode = ? THEN 0 ELSE 1 END, name
            LIMIT 1
        """
        with _connect() as conn:
            row = conn.execute(sql, (term, f"%{term}%", term, term)).fetchone()
            if row:
                return Product(row["id"], row["name"], row["barcode"] or "", row["unit_price"], row["quantity"])
        return None


class CustomerService:
    @staticmethod
    def list_customers(search: str = "") -> list[Customer]:
        sql = "SELECT id, full_name, phone, address FROM customers"
        params = []
        if search:
            sql += " WHERE full_name LIKE ? OR phone LIKE ?"
            params = [f"%{search}%", f"%{search}%"]
        sql += " ORDER BY full_name"
        with _connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [Customer(row["id"], row["full_name"], row["phone"] or "", row["address"] or "") for row in rows]

    @staticmethod
    def create_customer(customer: Customer) -> int | None:
        sql = "INSERT INTO customers (full_name, phone, address) VALUES (?, ?, ?)"
        with _connect() as conn:
            cur = conn.execute(sql, (customer.name, customer.phone, customer.address))
            conn.commit()
            return cur.lastrowid

    @staticmethod
    def update_customer(customer: Customer) -> bool:
        sql = "UPDATE customers SET full_name = ?, phone = ?, address = ? WHERE id = ?"
        with _connect() as conn:
            conn.execute(sql, (customer.name, customer.phone, customer.address, customer.id))
            conn.commit()
            return True

    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        sql = "DELETE FROM customers WHERE id = ?"
        with _connect() as conn:
            conn.execute(sql, (customer_id,))
            conn.commit()
            return True


class InvoiceService:
    @staticmethod
    def create_invoice(customer_id: int | None, items: List[InvoiceItem]) -> tuple[bool, str, int | None]:
        if not items:
            return False, "فاکتور خالی است.", None

        total = sum(i.total for i in items)

        conn = _connect()
        try:
            conn.execute("BEGIN IMMEDIATE")

            cur = conn.execute(
                "INSERT INTO invoices (customer_id, user_id, total) VALUES (?, ?, ?)",
                (customer_id, 1, total),
            )
            invoice_id = cur.lastrowid

            conn.executemany(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) "
                "VALUES (?, ?, ?, ?)",
                [(invoice_id, i.product_id, i.quantity, i.unit_price) for i in items],
            )

            conn.executemany(
                "UPDATE products SET quantity = MAX(COALESCE(quantity, stock, 0) - ?, 0) WHERE id = ?",
                [(i.quantity, i.product_id) for i in items],
            )

            conn.commit()
            return True, f"فاکتور #{invoice_id} ثبت شد.", invoice_id
        except sqlite3.Error as exc:
            conn.rollback()
            return False, str(exc), None
        finally:
            conn.close()

    @staticmethod
    def invoice_html(invoice_id: int, customer_name: str, items: List[InvoiceItem], date: str) -> str:
        rows = "".join(
            f"""
            <tr>
                <td>{i.product_name}</td>
                <td align="center">{i.quantity}</td>
                <td align="center">{_money(i.unit_price)}</td>
                <td align="center">{_money(i.total)}</td>
            </tr>
            """
            for i in items
        )
        total = sum(i.total for i in items)

        return f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: Tahoma, sans-serif; padding: 20px; }}
                h2 {{ color: #4b2fa8; text-align: center; }}
                .info {{ background: #f6f4ff; padding: 10px; border-radius: 8px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th {{ background: #4b2fa8; color: white; padding: 8px; }}
                td {{ padding: 6px; border: 1px solid #ddd; }}
                .total {{ font-size: 16px; font-weight: bold; color: #d32f2f; background: #fff5f5; padding: 10px; border-radius: 8px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h2>فاکتور فروش</h2>
            <div class="info">
                <p><strong>شماره فاکتور:</strong> {invoice_id}</p>
                <p><strong>تاریخ:</strong> {date}</p>
                <p><strong>مشتری:</strong> {customer_name}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>نام کالا</th>
                        <th>تعداد</th>
                        <th>قیمت واحد</th>
                        <th>جمع</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <div class="total">
                <strong>مبلغ قابل پرداخت:</strong> {_money(total)}
            </div>
        </body>
        </html>
        """


# ایجاد نمونه‌های سرویس
product_service = ProductService()
customer_service = CustomerService()
invoice_service = InvoiceService()


# ============================================================================
# دیالوگ مشتری
# ============================================================================
class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer: Customer | None = None):
        super().__init__(parent)
        self.setWindowTitle("ویرایش مشتری" if customer else "مشتری جدید")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(360)
        self._customer = customer
        self.saved_id: int | None = None

        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.addr_edit = QLineEdit()
        form.addRow("نام مشتری:", self.name_edit)
        form.addRow("تلفن:", self.phone_edit)
        form.addRow("آدرس:", self.addr_edit)

        if customer:
            self.name_edit.setText(customer.name)
            self.phone_edit.setText(customer.phone)
            self.addr_edit.setText(customer.address)

        save = QPushButton("ذخیره")
        save.setObjectName("primaryBtn")
        save.clicked.connect(self._save)
        form.addRow(save)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام مشتری اجباری است.")
            return
        c = Customer(
            self._customer.id if self._customer else None,
            name,
            self.phone_edit.text().strip(),
            self.addr_edit.text().strip()
        )
        if self._customer:
            customer_service.update_customer(c)
            self.saved_id = c.id
        else:
            self.saved_id = customer_service.create_customer(c)
        self.accept()


# ============================================================================
# تب فاکتور
# ============================================================================
class InvoiceTab(QWidget):
    COLUMNS = ["شرح کالا", "تعداد", "قیمت واحد", "جمع"]

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._items: List[InvoiceItem] = []

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # کارت انتخاب مشتری
        card_customer = QFrame()
        card_customer.setObjectName("cardFrame")
        cust_layout = QHBoxLayout(card_customer)
        cust_layout.setContentsMargins(18, 14, 18, 14)
        cust_layout.setSpacing(12)

        cust_layout.addWidget(QLabel("👤 مشتری:", objectName="pastelLabel"))
        self.cust_combo = QComboBox()
        self.cust_combo.setObjectName("pastelCombo")
        cust_layout.addWidget(self.cust_combo, 1)

        new_cust = QPushButton("➕ مشتری جدید")
        new_cust.setObjectName("btnAddItem")
        new_cust.clicked.connect(self._new_customer)
        cust_layout.addWidget(new_cust)

        root.addWidget(card_customer)

        # کارت اسکن و افزودن کالا
        card_scan = QFrame()
        card_scan.setObjectName("cardFrame")
        scan_layout = QVBoxLayout(card_scan)
        scan_layout.setContentsMargins(18, 14, 18, 14)
        scan_layout.setSpacing(10)

        # ردیف اسکن
        row_scan = QHBoxLayout()
        row_scan.addWidget(QLabel("📱 کالا:", objectName="pastelLabel"))
        self.scan_edit = QLineEdit()
        self.scan_edit.setObjectName("pastelInput")
        self.scan_edit.setPlaceholderText("اسکن بارکد/QR یا تایپ دستی شمارهٔ بارکد...")
        self.scan_edit.returnPressed.connect(self._add_item)
        row_scan.addWidget(self.scan_edit, 1)
        scan_layout.addLayout(row_scan)

        # ردیف تعداد و دکمه افزودن
        row_details = QHBoxLayout()
        row_details.setSpacing(10)

        row_details.addWidget(QLabel("🔢 تعداد:", objectName="pastelLabel"))
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(100_000)
        self.count_spin.setValue(1)
        self.count_spin.setObjectName("pastelSpin")
        row_details.addWidget(self.count_spin)

        row_details.addStretch()

        add_btn = QPushButton("➕ افزودن به فاکتور")
        add_btn.setObjectName("btnAddItem")
        add_btn.clicked.connect(self._add_item)
        row_details.addWidget(add_btn)

        scan_layout.addLayout(row_details)
        root.addWidget(card_scan)

        # جدول اقلام
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setObjectName("pastelTable")
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setLayoutDirection(Qt.RightToLeft)
        root.addWidget(self.table, 1)

        # کارت جمع کل و عملیات
        card_footer = QFrame()
        card_footer.setObjectName("cardFrame")
        footer_layout = QHBoxLayout(card_footer)
        footer_layout.setContentsMargins(18, 14, 18, 14)
        footer_layout.setSpacing(12)

        self.total_lbl = QLabel("🧮 جمع کل: ۰ ریال")
        self.total_lbl.setObjectName("totalLabel")
        footer_layout.addWidget(self.total_lbl, 1)

        rm_btn = QPushButton("🗑️ حذف قلم")
        rm_btn.setObjectName("btnDelete")
        rm_btn.clicked.connect(self._remove_item)
        footer_layout.addWidget(rm_btn)

        submit = QPushButton("✅ ثبت و چاپ فاکتور")
        submit.setObjectName("btnSubmit")
        submit.clicked.connect(self._submit)
        footer_layout.addWidget(submit)

        root.addWidget(card_footer)

        self.reload_customers()
        self.scan_edit.setFocus()

    def reload_customers(self):
        self.cust_combo.clear()
        for c in customer_service.list_customers():
            self.cust_combo.addItem(
                f"{c.name}  ({c.phone})" if c.phone else c.name,
                c.id
            )

    def _new_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.reload_customers()
            idx = self.cust_combo.findData(dlg.saved_id)
            if idx >= 0:
                self.cust_combo.setCurrentIndex(idx)

    def _add_item(self):
        text = self.scan_edit.text().strip()
        self.scan_edit.clear()

        if not text:
            return

        p = product_service.find_for_scan(text)
        if not p:
            QMessageBox.warning(
                self,
                "خطا",
                f"کالایی با شناسهٔ «{text}» یافت نشد."
            )
            self.scan_edit.setFocus()
            return

        qty = self.count_spin.value()

        # اگر کالا قبلاً در فاکتور هست، تعدادش جمع شود
        for it in self._items:
            if it.product_id == p.id:
                it.quantity += qty
                break
        else:
            self._items.append(InvoiceItem(p.id, p.name, qty, p.unit_price))

        self._refresh_table()
        self.scan_edit.setFocus()
        self.count_spin.setValue(1)

    def _remove_item(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._items):
            del self._items[row]
            self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self._items))
        for row, it in enumerate(self._items):
            values = (
                it.product_name,
                f"{it.quantity:,}",
                f"{it.unit_price:,.0f}",
                f"{it.total:,.0f}"
            )
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        total = sum(i.total for i in self._items)
        self.total_lbl.setText(f"🧮 جمع کل: {total:,.0f} ریال")

    def _submit(self):
        if self.cust_combo.currentIndex() < 0:
            QMessageBox.warning(self, "⚠️ خطا", "ابتدا مشتری را انتخاب یا ثبت کنید.")
            return

        if not self._items:
            QMessageBox.warning(self, "⚠️ خطا", "فاکتور خالی است.")
            return

        customer_id = self.cust_combo.currentData()
        ok, msg, inv_id = invoice_service.create_invoice(customer_id, self._items)

        if not ok:
            QMessageBox.warning(self, "⚠️ خطا", msg)
            return

        html = invoice_service.invoice_html(
            inv_id,
            self.cust_combo.currentText(),
            self._items,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        self._print(html)

        self._items = []
        self._refresh_table()
        self.scan_edit.setFocus()

    def _print(self, html: str):
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("چاپ فاکتور")

        if dlg.exec() == QPrintDialog.Accepted:
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print_(printer)


# ============================================================================
# تب مشتریان
# ============================================================================
class CustomersTab(QWidget):
    COLUMNS = ["نام مشتری", "تلفن", "آدرس"]

    def __init__(self, on_change=None):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._on_change = on_change
        self._customers: List[Customer] = []

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # کارت جستجو و عملیات
        card_toolbar = QFrame()
        card_toolbar.setObjectName("cardFrame")
        toolbar = QHBoxLayout(card_toolbar)
        toolbar.setContentsMargins(18, 14, 18, 14)
        toolbar.setSpacing(12)

        toolbar.addWidget(QLabel("🔍 جستجو:", objectName="pastelLabel"))
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("pastelInput")
        self.search_edit.setPlaceholderText("جستجوی نام یا تلفن...")
        self.search_edit.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search_edit, 1)

        for text, slot, obj in (
            ("➕ افزودن", self._add, "btnAddItem"),
            ("✏️ ویرایش", self._edit, "btnEdit"),
            ("🗑️ حذف", self._delete, "btnDelete")
        ):
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn)

        root.addWidget(card_toolbar)

        # جدول مشتریان
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setObjectName("pastelTable")
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setLayoutDirection(Qt.RightToLeft)
        root.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        self._customers = customer_service.list_customers(
            self.search_edit.text().strip()
        )
        self.table.setRowCount(len(self._customers))

        for row, c in enumerate(self._customers):
            values = (c.name, c.phone, c.address)
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

        if self._on_change:
            self._on_change()

    def _selected(self) -> Customer | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._customers):
            return self._customers[row]
        return None

    def _add(self):
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self):
        c = self._selected()
        if not c:
            QMessageBox.information(
                self,
                "💡 راهنما",
                "ابتدا یک مشتری انتخاب کنید."
            )
            return

        dlg = CustomerDialog(self, c)
        if dlg.exec():
            self.refresh()

    def _delete(self):
        c = self._selected()
        if not c:
            QMessageBox.information(
                self,
                "💡 راهنما",
                "ابتدا یک مشتری انتخاب کنید."
            )
            return

        if QMessageBox.question(
            self,
            "🗑️ حذف مشتری",
            f"آیا از حذف مشتری «{c.name}» اطمینان دارید؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            customer_service.delete_customer(c.id)
            self.refresh()


# ============================================================================
# صفحه اصلی فروش
# ============================================================================
class SalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # عنوان صفحه
        title = QLabel("🛒 فروش و فاکتور", objectName="pageTitle")
        root.addWidget(title)

        # تب‌ها
        tabs = QTabWidget()
        tabs.setObjectName("pastelTabs")
        self.invoice_tab = InvoiceTab()
        self.customers_tab = CustomersTab(
            on_change=self.invoice_tab.reload_customers
        )
        tabs.addTab(self.invoice_tab, "📄 فاکتور جدید")
        tabs.addTab(self.customers_tab, "👥 مشتریان")
        root.addWidget(tabs, 1)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            /* استایل کلی صفحه */
            #pageTitle {
                color: #5B4A8A;
                font-size: 22px;
                font-weight: bold;
                padding: 8px 0;
            }
            
            /* کارت‌های گرد با سایه ملایم */
            #cardFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f6ff);
                border: 1px solid #e8e0f5;
                border-radius: 20px;
                padding: 6px;
            }
            #cardFrame:hover {
                border-color: #d5c8ed;
            }
            
            /* لیبل‌های پاستیلی */
            #pastelLabel {
                color: #6B5A8A;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 10px;
                background: rgba(235, 225, 250, 0.3);
                border-radius: 12px;
                min-width: 50px;
            }
            
            /* ورودی‌های گرد و پاستیلی */
            #pastelInput {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 13px;
                color: #4a3a6a;
                transition: all 0.3s ease;
                min-height: 32px;
            }
            #pastelInput:hover {
                border-color: #d5c8ed;
                background: #ffffff;
            }
            #pastelInput:focus {
                border-color: #a48ad6;
                background: #ffffff;
                box-shadow: 0 0 0 4px rgba(164, 138, 214, 0.15);
            }
            #pastelInput::placeholder {
                color: #b0a8c8;
                font-style: italic;
                font-size: 12px;
            }
            
            /* کامبو باکس پاستیلی */
            #pastelCombo {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 13px;
                color: #4a3a6a;
                min-height: 32px;
            }
            #pastelCombo:hover {
                border-color: #d5c8ed;
            }
            #pastelCombo:focus {
                border-color: #a48ad6;
                box-shadow: 0 0 0 4px rgba(164, 138, 214, 0.15);
            }
            #pastelCombo::drop-down {
                border: none;
                border-radius: 12px;
            }
            
            /* اسپین باکس پاستیلی */
            #pastelSpin {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 4px 10px;
                font-size: 13px;
                color: #4a3a6a;
                min-height: 32px;
                min-width: 80px;
            }
            #pastelSpin:hover {
                border-color: #d5c8ed;
            }
            #pastelSpin:focus {
                border-color: #a48ad6;
                box-shadow: 0 0 0 4px rgba(164, 138, 214, 0.15);
            }
            
            /* دکمه‌ها */
            #btnAddItem, #btnEdit, #btnDelete, #btnSubmit {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                border: none;
                border-radius: 16px;
                transition: all 0.3s ease;
                min-height: 36px;
            }
            
            #btnAddItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a48ad6, stop:1 #8a6ed6);
            }
            #btnAddItem:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(138, 110, 214, 0.4);
            }
            #btnAddItem:pressed {
                transform: translateY(0px);
            }
            
            #btnEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0c27a, stop:1 #e0a84a);
            }
            #btnEdit:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(224, 168, 74, 0.4);
            }
            #btnEdit:pressed {
                transform: translateY(0px);
            }
            
            #btnDelete {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5a0b0, stop:1 #e8739a);
            }
            #btnDelete:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(232, 115, 154, 0.35);
            }
            #btnDelete:pressed {
                transform: translateY(0px);
            }
            
            #btnSubmit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7bc8a4, stop:1 #5ab88a);
            }
            #btnSubmit:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(90, 184, 138, 0.4);
            }
            #btnSubmit:pressed {
                transform: translateY(0px);
            }
            
            /* جمع کل */
            #totalLabel {
                font-size: 16px;
                font-weight: bold;
                color: #5B4A8A;
                background: rgba(235, 225, 250, 0.3);
                padding: 8px 18px;
                border-radius: 16px;
                border: 2px solid #e8e0f5;
                min-height: 40px;
            }
            
            /* جدول پاستیلی */
            #pastelTable {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 18px;
                gridline-color: #f0ecf8;
                padding: 4px;
            }
            #pastelTable::item {
                padding: 8px;
                border-radius: 10px;
                font-size: 13px;
            }
            #pastelTable::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
                border-radius: 10px;
            }
            #pastelTable::item:hover {
                background: rgba(213, 200, 237, 0.25);
                border-radius: 10px;
            }
            
            /* هدر جدول */
            #pastelTable QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e0f5, stop:1 #d5c8ed);
                color: #4a3a6a;
                font-weight: bold;
                border: none;
                border-right: 1px solid #f0ecf8;
                padding: 10px 6px;
                font-size: 12px;
            }
            #pastelTable QHeaderView::section:last {
                border-right: none;
            }
            
            /* اسکرول بار جدول */
            QScrollBar:vertical {
                background: #f5f0fa;
                border-radius: 12px;
                width: 12px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 10px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar:horizontal {
                background: #f5f0fa;
                border-radius: 12px;
                height: 12px;
                margin: 4px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #c0b0e0);
                border-radius: 10px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c0b0e0, stop:1 #a48ad6);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            
            /* سلول‌های جدول */
            #pastelTable QTableWidget::item {
                padding: 8px 6px;
                border-radius: 8px;
                font-size: 13px;
            }
            
            /* تب‌ها */
            #pastelTabs::pane {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 18px;
                padding: 12px;
            }
            #pastelTabs QTabBar::tab {
                padding: 10px 24px;
                border-radius: 14px 14px 0 0;
                font-size: 13px;
                font-weight: 600;
                color: #6a5a8a;
                background: transparent;
                margin-right: 4px;
            }
            #pastelTabs QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }
            #pastelTabs QTabBar::tab:hover:!selected {
                background: rgba(213, 200, 237, 0.3);
                border-radius: 14px 14px 0 0;
            }
            
            /* پیام‌های باکس */
            QMessageBox {
                background: #faf8ff;
                border-radius: 16px;
            }
            QMessageBox QLabel {
                color: #4a3a6a;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 6px 18px;
                font-weight: bold;
                font-size: 12px;
            }
            QMessageBox QPushButton:hover {
                background: #8a6ed6;
            }
        """)