# -*- coding: utf-8 -*-
"""صفحهٔ فروش — منطبق بر اسکیمای واقعی enterprise.db.

جداول مورد استفاده:
    invoices(id, customer_id, user_id NOT NULL, total, created_at)
    invoice_items(id, invoice_id, product_id, quantity, unit_price)
    customers(id, full_name, phone, created_at)
    products(id, name, barcode, retail_price, quantity, stock, price, ...)
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
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


# ----------------------------------------------------------------------------
# لایهٔ داده
# ----------------------------------------------------------------------------
class SalesRepo:
    """دسترسی به داده‌های فروش. همهٔ کوئری‌ها پارامتری هستند."""

    @staticmethod
    def find_product(term: str) -> sqlite3.Row | None:
        term = term.strip()
        if not term:
            return None
        sql = """
            SELECT id, name, barcode,
                   COALESCE(retail_price, unit_price, price, 0) AS sale_price,
                   COALESCE(quantity, stock, 0)                 AS on_hand
            FROM products
            WHERE barcode = ? OR name LIKE ?
            ORDER BY CASE WHEN barcode = ? THEN 0 ELSE 1 END, name
            LIMIT 1
        """
        with _connect() as conn:
            return conn.execute(sql, (term, f"%{term}%", term)).fetchone()

    @staticmethod
    def list_customers() -> list[sqlite3.Row]:
        with _connect() as conn:
            return conn.execute(
                "SELECT id, full_name, phone FROM customers ORDER BY full_name"
            ).fetchall()

    @staticmethod
    def create_customer(full_name: str, phone: str) -> tuple[bool, str, int | None]:
        full_name = full_name.strip()
        if not full_name:
            return False, "نام مشتری الزامی است.", None
        try:
            with _connect() as conn:
                cur = conn.execute(
                    "INSERT INTO customers (full_name, phone) VALUES (?, ?)",
                    (full_name, phone.strip()),
                )
                return True, "مشتری ثبت شد.", cur.lastrowid
        except sqlite3.Error as exc:
            return False, f"خطای دیتابیس: {exc}", None

    @staticmethod
    def resolve_user_id(preferred: int | None) -> int | None:
        """invoices.user_id مقدار NOT NULL دارد؛ اگر شناسه نداشتیم اولین کاربر."""
        with _connect() as conn:
            if preferred:
                row = conn.execute(
                    "SELECT id FROM users WHERE id = ?", (preferred,)
                ).fetchone()
                if row:
                    return row["id"]
            row = conn.execute(
                "SELECT id FROM users WHERE COALESCE(is_active, 1) = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            return row["id"] if row else None

    @staticmethod
    def create_invoice(
        customer_id: int | None,
        user_id: int,
        items: list[dict],
        discount: float = 0.0,
    ) -> tuple[bool, str, int | None]:
        if not items:
            return False, "فاکتور خالی است.", None

        subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
        total = max(subtotal - discount, 0.0)

        conn = _connect()
        try:
            conn.execute("BEGIN IMMEDIATE")

            # کنترل موجودی داخل تراکنش تا فروش هم‌زمان موجودی منفی نسازد
            for item in items:
                row = conn.execute(
                    "SELECT COALESCE(quantity, stock, 0) AS on_hand, name "
                    "FROM products WHERE id = ?",
                    (item["product_id"],),
                ).fetchone()
                if row is None:
                    raise ValueError(f"کالای «{item['name']}» یافت نشد.")
                if row["on_hand"] < item["quantity"]:
                    raise ValueError(
                        f"موجودی «{row['name']}» کافی نیست "
                        f"(موجود: {row['on_hand']}، درخواست: {item['quantity']})."
                    )

            cur = conn.execute(
                "INSERT INTO invoices (customer_id, user_id, total) VALUES (?, ?, ?)",
                (customer_id, user_id, total),
            )
            invoice_id = cur.lastrowid

            conn.executemany(
                "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price) "
                "VALUES (?, ?, ?, ?)",
                [
                    (invoice_id, i["product_id"], i["quantity"], i["unit_price"])
                    for i in items
                ],
            )

            # هر دو ستون موازی موجودی را هم‌زمان کم می‌کنیم
            conn.executemany(
                "UPDATE products SET "
                "  quantity = MAX(COALESCE(quantity, stock, 0) - ?, 0), "
                "  stock    = MAX(COALESCE(stock, quantity, 0) - ?, 0) "
                "WHERE id = ?",
                [(i["quantity"], i["quantity"], i["product_id"]) for i in items],
            )

            conn.commit()
            return True, f"فاکتور #{invoice_id} ثبت شد.", invoice_id
        except (sqlite3.Error, ValueError) as exc:
            conn.rollback()
            return False, str(exc), None
        finally:
            conn.close()

    @staticmethod
    def list_invoices(limit: int = 200) -> list[sqlite3.Row]:
        sql = """
            SELECT i.id, i.total, i.created_at,
                   COALESCE(c.full_name, 'مشتری متفرقه') AS customer,
                   COALESCE(u.full_name, u.username, '-') AS seller,
                   (SELECT COUNT(*) FROM invoice_items it WHERE it.invoice_id = i.id) AS lines
            FROM invoices i
            LEFT JOIN customers c ON c.id = i.customer_id
            LEFT JOIN users     u ON u.id = i.user_id
            ORDER BY i.id DESC
            LIMIT ?
        """
        with _connect() as conn:
            return conn.execute(sql, (limit,)).fetchall()

    @staticmethod
    def invoice_detail(invoice_id: int) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
        with _connect() as conn:
            head = conn.execute(
                "SELECT i.id, i.total, i.created_at, "
                "       COALESCE(c.full_name, 'مشتری متفرقه') AS customer "
                "FROM invoices i LEFT JOIN customers c ON c.id = i.customer_id "
                "WHERE i.id = ?",
                (invoice_id,),
            ).fetchone()
            lines = conn.execute(
                "SELECT p.name, it.quantity, it.unit_price, "
                "       (it.quantity * it.unit_price) AS line_total "
                "FROM invoice_items it JOIN products p ON p.id = it.product_id "
                "WHERE it.invoice_id = ?",
                (invoice_id,),
            ).fetchall()
        return head, lines


# ----------------------------------------------------------------------------
# دیالوگ افزودن مشتری
# ----------------------------------------------------------------------------
class CustomerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("مشتری جدید")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(320)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام و نام خانوادگی")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("۰۹۱۲…")

        form = QFormLayout()
        form.addRow("نام:", self.name_edit)
        form.addRow("تلفن:", self.phone_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self
        )
        buttons.button(QDialogButtonBox.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.Cancel).setText("انصراف")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str]:
        return self.name_edit.text(), self.phone_edit.text()


# ----------------------------------------------------------------------------
# صفحهٔ فروش
# ----------------------------------------------------------------------------
class SalesPage(QWidget):
    """صفحهٔ فروش؛ با SalesPage() و SalesPage(user_id) هر دو کار می‌کند."""

    inventory_updated = Signal()

    COLS = ("نام کالا", "بارکد", "تعداد", "قیمت واحد", "جمع ردیف", "")

    def __init__(self, current_user_id: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._items: list[dict] = []
        self._user_id = SalesRepo.resolve_user_id(current_user_id)
        self._print_dialog = None  # برای جلوگیری از جمع‌آوری زباله
        self._invoice_printer = None  # کش ماژول چاپ

        tabs = QTabWidget()
        tabs.addTab(self._build_new_invoice_tab(), "فاکتور جدید")
        tabs.addTab(self._build_history_tab(), "فاکتورهای اخیر")

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.addWidget(tabs)

        self._apply_styles()
        self.reload_customers()
        self.reload_invoices()

        if self._user_id is None:
            QMessageBox.warning(
                self,
                "کاربر نامعتبر",
                "هیچ کاربر فعالی در دیتابیس نیست؛ ثبت فاکتور غیرفعال می‌شود.",
            )
            self.save_btn.setEnabled(False)

    # ------------------------------------------------------------------ راه‌اندازی ماژول چاپ
    def _get_invoice_printer(self):
        """دریافت ماژول چاپ فاکتور با مدیریت خطا"""
        if self._invoice_printer is not None:
            return self._invoice_printer

        try:
            # تلاش برای import از مسیر اصلی
            from app.ui.utils.invoice_printer import InvoicePrinter
            self._invoice_printer = InvoicePrinter
            return self._invoice_printer
        except ImportError:
            try:
                # تلاش برای import از مسیر نسبی
                from ..utils.invoice_printer import InvoicePrinter
                self._invoice_printer = InvoicePrinter
                return self._invoice_printer
            except ImportError:
                # اگر هیچکدام کار نکرد، یک کلاس جایگزین با پیام خطا
                class DummyPrinter:
                    @staticmethod
                    def print_pdf(*args, **kwargs):
                        QMessageBox.warning(None, "خطا", "ماژول چاپ یافت نشد. لطفاً فایل invoice_printer.py را در مسیر app/ui/utils/ قرار دهید.")
                        return False
                    
                    @staticmethod
                    def print_excel(*args, **kwargs):
                        QMessageBox.warning(None, "خطا", "ماژول چاپ یافت نشد. لطفاً فایل invoice_printer.py را در مسیر app/ui/utils/ قرار دهید.")
                        return False
                    
                    @staticmethod
                    def print_preview(*args, **kwargs):
                        QMessageBox.warning(None, "خطا", "ماژول چاپ یافت نشد. لطفاً فایل invoice_printer.py را در مسیر app/ui/utils/ قرار دهید.")
                        return False
                
                self._invoice_printer = DummyPrinter
                return self._invoice_printer

    # ------------------------------------------------------------------ ساخت UI
    def _build_new_invoice_tab(self) -> QWidget:
        page = QWidget()

        # --- نوار اسکن
        scan_box = QGroupBox("اسکن / جست‌وجوی کالا")
        self.scan_edit = QLineEdit()
        self.scan_edit.setPlaceholderText("بارکد را اسکن کنید یا نام کالا را بنویسید و Enter بزنید")
        self.scan_edit.setAccessibleName("ورودی بارکد یا نام کالا")
        self.scan_edit.returnPressed.connect(self._on_scan)

        add_btn = QPushButton("افزودن")
        add_btn.setObjectName("btnPrimary")
        add_btn.clicked.connect(self._on_scan)

        scan_row = QHBoxLayout(scan_box)
        scan_row.addWidget(self.scan_edit, 1)
        scan_row.addWidget(add_btn)

        # --- جدول اقلام
        self.items_table = QTableWidget(0, len(self.COLS))
        self.items_table.setHorizontalHeaderLabels(self.COLS)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, len(self.COLS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        # --- مشتری و جمع‌بندی
        self.customer_combo = QComboBox()
        self.customer_combo.setAccessibleName("انتخاب مشتری")
        new_customer_btn = QPushButton("مشتری جدید")
        new_customer_btn.clicked.connect(self._on_new_customer)

        customer_row = QHBoxLayout()
        customer_row.addWidget(QLabel("مشتری:"))
        customer_row.addWidget(self.customer_combo, 1)
        customer_row.addWidget(new_customer_btn)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 1_000_000_000)
        self.discount_spin.setDecimals(0)
        self.discount_spin.setSingleStep(1000)
        self.discount_spin.setSuffix(" ریال")
        self.discount_spin.setAccessibleName("تخفیف فاکتور")
        self.discount_spin.valueChanged.connect(self._refresh_totals)

        self.subtotal_label = QLabel("۰")
        self.total_label = QLabel("۰")
        self.total_label.setObjectName("totalValue")

        summary = QFormLayout()
        summary.addRow("جمع اقلام:", self.subtotal_label)
        summary.addRow("تخفیف:", self.discount_spin)
        summary.addRow("مبلغ قابل پرداخت:", self.total_label)

        summary_frame = QFrame()
        summary_frame.setObjectName("summaryCard")
        summary_frame.setLayout(summary)

        self.save_btn = QPushButton("ثبت فاکتور")
        self.save_btn.setObjectName("btnPrimary")
        self.save_btn.clicked.connect(self._on_save)

        clear_btn = QPushButton("پاک‌کردن فاکتور")
        clear_btn.setObjectName("btnDelete")
        clear_btn.clicked.connect(self._clear_invoice)

        action_row = QHBoxLayout()
        action_row.addWidget(self.save_btn)
        action_row.addWidget(clear_btn)
        action_row.addStretch(1)

        layout = QVBoxLayout(page)
        layout.addWidget(scan_box)
        layout.addWidget(self.items_table, 1)
        layout.addLayout(customer_row)
        layout.addWidget(summary_frame)
        layout.addLayout(action_row)
        return page

    def _build_history_tab(self) -> QWidget:
        page = QWidget()

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(
            ("شماره", "تاریخ", "مشتری", "تعداد ردیف", "مبلغ")
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.itemSelectionChanged.connect(self._show_selected_invoice)

        self.preview = QTextBrowser()
        self.preview.setAccessibleName("پیش‌نمایش فاکتور")

        refresh_btn = QPushButton("بازخوانی")
        refresh_btn.clicked.connect(self.reload_invoices)

        # دکمه چاپ فاکتور انتخاب شده
        print_btn = QPushButton("🖨 چاپ فاکتور")
        print_btn.clicked.connect(self._print_selected_invoice)
        print_btn.setObjectName("btnPrimary")

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(print_btn)
        buttons_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.history_table)
        splitter.addWidget(self.preview)
        splitter.setSizes((520, 380))

        layout = QVBoxLayout(page)
        layout.addWidget(splitter, 1)
        layout.addLayout(buttons_layout)
        return page

    # --------------------------------------------------------------- بارگذاری
    def reload_customers(self) -> None:
        current = self.customer_combo.currentData()
        self.customer_combo.clear()
        self.customer_combo.addItem("مشتری متفرقه", None)
        for row in SalesRepo.list_customers():
            label = row["full_name"]
            if row["phone"]:
                label = f"{label} — {row['phone']}"
            self.customer_combo.addItem(label, row["id"])
        if current is not None:
            index = self.customer_combo.findData(current)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)

    def reload_invoices(self) -> None:
        rows = SalesRepo.list_invoices()
        self.history_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = (
                str(row["id"]),
                (row["created_at"] or "")[:16],
                row["customer"],
                str(row["lines"]),
                _money(row["total"] or 0),
            )
            for c, text in enumerate(values):
                cell = QTableWidgetItem(text)
                if c in (0, 3, 4):
                    cell.setTextAlignment(Qt.AlignCenter)
                cell.setData(Qt.UserRole, row["id"])
                self.history_table.setItem(r, c, cell)

    # ----------------------------------------------------------------- رفتارها
    def _on_scan(self) -> None:
        term = self.scan_edit.text().strip()
        if not term:
            return
        product = SalesRepo.find_product(term)
        if product is None:
            QMessageBox.information(self, "یافت نشد", f"کالایی با «{term}» پیدا نشد.")
            self.scan_edit.selectAll()
            return
        if product["on_hand"] <= 0:
            QMessageBox.warning(
                self, "موجودی صفر", f"موجودی «{product['name']}» صفر است."
            )
            self.scan_edit.clear()
            return

        for item in self._items:
            if item["product_id"] == product["id"]:
                if item["quantity"] >= product["on_hand"]:
                    QMessageBox.warning(
                        self,
                        "سقف موجودی",
                        f"حداکثر {product['on_hand']} عدد از این کالا موجود است.",
                    )
                else:
                    item["quantity"] += 1
                break
        else:
            self._items.append(
                {
                    "product_id": product["id"],
                    "name": product["name"],
                    "barcode": product["barcode"] or "-",
                    "quantity": 1,
                    "unit_price": float(product["sale_price"] or 0),
                    "on_hand": int(product["on_hand"]),
                }
            )

        self.scan_edit.clear()
        self._render_items()

    def _render_items(self) -> None:
        self.items_table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            name_cell = QTableWidgetItem(item["name"])
            name_cell.setToolTip(f"موجودی: {item['on_hand']}")
            self.items_table.setItem(row, 0, name_cell)

            barcode_cell = QTableWidgetItem(item["barcode"])
            barcode_cell.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 1, barcode_cell)

            qty = QSpinBox()
            qty.setRange(1, max(item["on_hand"], 1))
            qty.setValue(item["quantity"])
            qty.setAccessibleName(f"تعداد {item['name']}")
            qty.valueChanged.connect(
                lambda value, r=row: self._update_item(r, "quantity", value)
            )
            self.items_table.setCellWidget(row, 2, qty)

            price = QDoubleSpinBox()
            price.setRange(0, 1_000_000_000)
            price.setDecimals(0)
            price.setSingleStep(1000)
            price.setValue(item["unit_price"])
            price.setAccessibleName(f"قیمت واحد {item['name']}")
            price.valueChanged.connect(
                lambda value, r=row: self._update_item(r, "unit_price", value)
            )
            self.items_table.setCellWidget(row, 3, price)

            line_total = QTableWidgetItem(_money(item["quantity"] * item["unit_price"]))
            line_total.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, 4, line_total)

            remove = QPushButton("حذف")
            remove.setObjectName("btnDelete")
            remove.setAccessibleName(f"حذف {item['name']} از فاکتور")
            remove.clicked.connect(lambda _=False, r=row: self._remove_item(r))
            self.items_table.setCellWidget(row, 5, remove)

        self._refresh_totals()

    def _update_item(self, row: int, key: str, value: float) -> None:
        if 0 <= row < len(self._items):
            self._items[row][key] = int(value) if key == "quantity" else float(value)
            item = self._items[row]
            cell = self.items_table.item(row, 4)
            if cell is not None:
                cell.setText(_money(item["quantity"] * item["unit_price"]))
            self._refresh_totals()

    def _remove_item(self, row: int) -> None:
        if 0 <= row < len(self._items):
            del self._items[row]
            self._render_items()

    def _refresh_totals(self) -> None:
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self._items)
        total = max(subtotal - self.discount_spin.value(), 0.0)
        self.subtotal_label.setText(_money(subtotal))
        self.total_label.setText(_money(total))

    def _on_new_customer(self) -> None:
        dialog = CustomerDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        ok, message, customer_id = SalesRepo.create_customer(*dialog.values())
        if not ok:
            QMessageBox.warning(self, "خطا", message)
            return
        self.reload_customers()
        index = self.customer_combo.findData(customer_id)
        if index >= 0:
            self.customer_combo.setCurrentIndex(index)

    def _on_save(self) -> None:
        if not self._items:
            QMessageBox.information(self, "فاکتور خالی", "ابتدا کالا اضافه کنید.")
            return
        if self._user_id is None:
            QMessageBox.warning(self, "کاربر نامعتبر", "کاربر فعال برای ثبت فاکتور نیست.")
            return

        # گرفتن اطلاعات فاکتور قبل از ثبت
        customer_name = self.customer_combo.currentText()
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self._items)
        discount = self.discount_spin.value()
        total = max(subtotal - discount, 0.0)
        
        # تهیه نسخه از آیتم‌ها برای چاپ
        items_copy = [
            {
                "name": item["name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "line_total": item["quantity"] * item["unit_price"]
            }
            for item in self._items
        ]

        ok, message, invoice_id = SalesRepo.create_invoice(
            self.customer_combo.currentData(),
            self._user_id,
            self._items,
            discount,
        )
        
        if not ok:
            QMessageBox.critical(self, "ثبت نشد", message)
            return

        # بروزرسانی اطلاعات فاکتور
        invoice_data = {
            "id": invoice_id,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "customer": customer_name,
            "seller": Session.current_user.get("full_name", "سیستم") if Session.current_user else "سیستم",
            "total": total,
            "discount": discount,
        }

        # نمایش پیام موفقیت
        QMessageBox.information(self, "ثبت شد", message)
        
        # پاک کردن فرم
        self._clear_invoice()
        self.reload_invoices()
        self.inventory_updated.emit()
        
        # نمایش دیالوگ انتخاب چاپ
        self._show_print_options(invoice_data, items_copy)
        
        # نمایش پیش‌نمایش فاکتور
        if invoice_id:
            self._render_preview(invoice_id)

    def _show_print_options(self, invoice_data: Dict, items: List[Dict]) -> None:
        """نمایش گزینه‌های چاپ فاکتور"""
        from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("چاپ فاکتور")
        dialog.setModal(True)
        dialog.resize(400, 200)
        dialog.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        
        # پیام
        msg = QLabel("فاکتور با موفقیت ثبت شد.\nلطفاً روش خروجی مورد نظر را انتخاب کنید:")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(msg)
        
        # دکمه‌ها
        btn_layout = QHBoxLayout()
        
        btn_preview = QPushButton("👁 پیش‌نمایش")
        btn_preview.clicked.connect(lambda: self._show_preview_dialog(invoice_data, items))
        
        btn_pdf = QPushButton("📄 PDF")
        btn_pdf.clicked.connect(lambda: self._save_pdf(invoice_data, items))
        
        btn_excel = QPushButton("📊 Excel")
        btn_excel.clicked.connect(lambda: self._save_excel(invoice_data, items))
        
        btn_skip = QPushButton("✖ بعداً")
        btn_skip.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(btn_preview)
        btn_layout.addWidget(btn_pdf)
        btn_layout.addWidget(btn_excel)
        btn_layout.addWidget(btn_skip)
        
        layout.addLayout(btn_layout)
        
        # ذخیره مرجع دیالوگ
        self._print_dialog = dialog
        dialog.exec()
        self._print_dialog = None

    def _show_preview_dialog(self, invoice_data: Dict, items: List[Dict]) -> None:
        """نمایش دیالوگ پیش‌نمایش"""
        printer = self._get_invoice_printer()
        try:
            printer.print_preview(invoice_data, items, self)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در نمایش پیش‌نمایش:\n{str(e)}")

    def _save_pdf(self, invoice_data: Dict, items: List[Dict]) -> None:
        """ذخیره به صورت PDF"""
        printer = self._get_invoice_printer()
        try:
            printer.print_pdf(invoice_data, items, self)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در ذخیره PDF:\n{str(e)}")

    def _save_excel(self, invoice_data: Dict, items: List[Dict]) -> None:
        """ذخیره به صورت Excel"""
        printer = self._get_invoice_printer()
        try:
            printer.print_excel(invoice_data, items, self)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در ذخیره Excel:\n{str(e)}")

    def _clear_invoice(self) -> None:
        self._items.clear()
        self.discount_spin.setValue(0)
        self.items_table.setRowCount(0)
        self._refresh_totals()
        self.scan_edit.setFocus()

    def _show_selected_invoice(self) -> None:
        items = self.history_table.selectedItems()
        if items:
            self._render_preview(int(items[0].data(Qt.UserRole)))

    def _render_preview(self, invoice_id: int) -> None:
        head, lines = SalesRepo.invoice_detail(invoice_id)
        if head is None:
            self.preview.clear()
            return
        rows = "".join(
            "<tr>"
            f"<td>{line['name']}</td>"
            f"<td align='center'>{line['quantity']}</td>"
            f"<td align='center'>{_money(line['unit_price'])}</td>"
            f"<td align='center'>{_money(line['line_total'])}</td>"
            "</tr>"
            for line in lines
        )
        self.preview.setHtml(
            f"""
            <div dir="rtl" style="font-family:Tahoma;">
              <h3>فاکتور فروش #{head['id']}</h3>
              <p>مشتری: {head['customer']}<br>تاریخ: {(head['created_at'] or '')[:16]}</p>
              <table width="100%" border="1" cellspacing="0" cellpadding="4">
                <tr><th>کالا</th><th>تعداد</th><th>قیمت واحد</th><th>جمع</th></tr>
                {rows}
              </table>
              <h4>مبلغ کل: {_money(head['total'] or 0)}</h4>
            </div>
            """
        )

    def _print_selected_invoice(self) -> None:
        """چاپ فاکتور انتخاب شده از تاریخچه"""
        selected = self.history_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "خطا", "لطفاً یک فاکتور را انتخاب کنید.")
            return
        
        invoice_id = selected[0].data(Qt.UserRole)
        self._print_invoice_from_history(invoice_id)

    def _print_invoice_from_history(self, invoice_id: int) -> None:
        """چاپ فاکتور از تاریخچه"""
        try:
            head, lines = SalesRepo.invoice_detail(invoice_id)
            if head is None:
                QMessageBox.warning(self, "خطا", "فاکتور یافت نشد.")
                return
            
            # دریافت اطلاعات فروشنده
            seller_name = "سیستم"
            if Session.current_user:
                seller_name = Session.current_user.get("full_name", "سیستم")
            
            invoice_data = {
                "id": head["id"],
                "created_at": head["created_at"],
                "customer": head["customer"],
                "seller": seller_name,
                "total": head["total"],
                "discount": 0,  # اگر تخفیف در دیتابیس ذخیره شود
            }
            
            items = [
                {
                    "name": line["name"],
                    "quantity": line["quantity"],
                    "unit_price": line["unit_price"],
                    "line_total": line["line_total"],
                }
                for line in lines
            ]
            
            # نمایش گزینه‌های چاپ
            self._show_print_options(invoice_data, items)
            
        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در چاپ فاکتور:\n{str(e)}")

    # ------------------------------------------------------------------ استایل
    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #d9d3f0; border-radius: 12px;
                margin-top: 12px; padding: 12px; font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; right: 12px; padding: 0 6px; }
            QFrame#summaryCard {
                background: #f6f4ff; border: 1px solid #d9d3f0;
                border-radius: 12px; padding: 12px;
            }
            QLabel#totalValue { font-size: 16px; font-weight: bold; color: #4b2fa8; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #cfc8ea; border-radius: 8px; padding: 6px;
            }
            QPushButton {
                border: 1px solid #cfc8ea; border-radius: 10px;
                padding: 7px 16px; background: #ffffff;
            }
            QPushButton:hover { background: #f0ecff; }
            QPushButton#btnPrimary {
                background: #5b3ec8; color: #ffffff; border: none; font-weight: bold;
            }
            QPushButton#btnPrimary:hover { background: #6d4ee0; }
            QPushButton#btnPrimary:disabled { background: #b9aee6; }
            QPushButton#btnDelete { background: #e04b4b; color: #ffffff; border: none; }
            QPushButton#btnDelete:hover { background: #f05a5a; }
            QTableWidget {
                border: 1px solid #d9d3f0; border-radius: 10px; gridline-color: #ece8fa;
            }
            QHeaderView::section {
                background: #efeaff; padding: 6px; border: none; font-weight: bold;
            }
            """
        )