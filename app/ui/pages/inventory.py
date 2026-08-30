# -*- coding: utf-8 -*-
"""صفحهٔ انبار و کالا — بارکدخوان (1D / QR) و ثبت دستی"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.product import Product
from app.services import product_service


class ProductDialog(QDialog):
    """فرم افزودن / ویرایش کالا"""

    def __init__(self, parent=None, product: Product | None = None):
        super().__init__(parent)
        self.setWindowTitle("ویرایش کالا" if product else "افزودن کالا")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(420)
        self._product = product

        form = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("pastelInput")
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setObjectName("pastelInput")
        self.barcode_edit.setPlaceholderText("اسکن یا ورود دستی بارکد")

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("pastelCombo")
        self.type_combo.addItem("بارکد معمولی (1D)", "1D")
        self.type_combo.addItem("QR کد", "QR")

        self.qty_spin = QSpinBox()
        self.qty_spin.setObjectName("pastelSpin")
        self.qty_spin.setMaximum(1_000_000)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setObjectName("pastelSpin")
        self.price_spin.setMaximum(1e12)
        self.price_spin.setDecimals(0)

        self.retail_price_spin = QDoubleSpinBox()
        self.retail_price_spin.setObjectName("pastelSpin")
        self.retail_price_spin.setMaximum(1e12)
        self.retail_price_spin.setDecimals(0)

        self.desc_edit = QLineEdit()
        self.desc_edit.setObjectName("pastelInput")

        form.addRow("📦 نام کالا:", self.name_edit)
        form.addRow("📱 بارکد:", self.barcode_edit)
        form.addRow("🔖 نوع بارکد:", self.type_combo)
        form.addRow("📊 موجودی اولیه:", self.qty_spin)
        form.addRow("💰 قیمت واحد:", self.price_spin)
        form.addRow("🏷️ قیمت مصرف‌کننده:", self.retail_price_spin)
        form.addRow("📝 توضیحات:", self.desc_edit)

        if product:
            self.name_edit.setText(product.name)
            self.barcode_edit.setText(product.barcode or "")
            self.type_combo.setCurrentIndex(
                1 if product.barcode_type == "QR" else 0
            )
            self.qty_spin.setValue(product.quantity)
            self.price_spin.setValue(product.unit_price)
            self.retail_price_spin.setValue(product.retail_price)
            self.desc_edit.setText(product.description or "")

        save_btn = QPushButton("💾 ذخیره", objectName="primaryBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        form.addRow(save_btn)

        self._apply_styles()

    def _save(self):
        name = self.name_edit.text().strip()
        barcode = self.barcode_edit.text().strip()

        if not name or not barcode:
            QMessageBox.warning(
                self,
                "⚠️ خطا",
                "نام کالا و بارکد اجباری هستند.",
            )
            return

        product = Product(
            id=self._product.id if self._product else None,
            name=name,
            barcode=barcode,
            barcode_type=self.type_combo.currentData(),
            quantity=self.qty_spin.value(),
            unit_price=self.price_spin.value(),
            retail_price=self.retail_price_spin.value(),
            description=self.desc_edit.text().strip(),
        )

        if self._product:
            ok, msg = product_service.update_product(product)
        else:
            ok, msg = product_service.create_product(product)

        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "⚠️ خطا", msg)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: #f8f6ff;
                border-radius: 20px;
            }
            QLabel {
                color: #6B5A8A;
                font-size: 13px;
                font-weight: 600;
            }
            #pastelInput {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 13px;
                color: #4a3a6a;
            }
            #pastelInput:focus {
                border-color: #a48ad6;
                background: #ffffff;
            }
            #pastelCombo {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 13px;
                color: #4a3a6a;
                min-height: 35px;
            }
            #pastelCombo:focus {
                border-color: #a48ad6;
            }
            #pastelSpin {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 4px 10px;
                font-size: 13px;
                color: #4a3a6a;
                min-height: 30px;
            }
            #pastelSpin:focus {
                border-color: #a48ad6;
            }
            #primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a48ad6, stop:1 #8a6ed6);
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 28px;
                border: none;
                border-radius: 16px;
            }
            #primaryBtn:hover {
                background: #8a6ed6;
            }
        """)


class InventoryPage(QWidget):
    COLUMNS = [
        "نام کالا",
        "بارکد",
        "نوع بارکد",
        "موجودی",
        "قیمت واحد",
        "قیمت مصرف‌کننده",
        "توضیحات",
    ]
    QTY_COL = 3

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._products: list[Product] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # عنوان
        title = QLabel("📦 مدیریت انبار و کالا")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        # پنل اسکن
        root.addWidget(self._build_scan_panel())

        # نوار ابزار
        root.addLayout(self._build_toolbar())

        # جدول - با تنظیمات پایه و مطمئن
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f6ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                gridline-color: #f0ecf8;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-radius: 8px;
                color: #4a3a6a;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
            }
            QTableWidget::item:hover {
                background: rgba(213, 200, 237, 0.3);
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e0f5, stop:1 #d5c8ed);
                color: #4a3a6a;
                font-weight: bold;
                border: none;
                border-right: 1px solid #f0ecf8;
                padding: 12px 8px;
                font-size: 12px;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)
        root.addWidget(self.table, 1)

        self._apply_styles()
        self.refresh()
        self.scan_edit.setFocus()

    # ---------------------------------------------- پنل اسکن
    def _build_scan_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("scanPanel")
        panel.setStyleSheet("""
            #scanPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f6ff);
                border: 2px solid #e8e0f5;
                border-radius: 20px;
                padding: 10px;
            }
            #scanPanel:hover {
                border-color: #d5c8ed;
            }
        """)

        lay = QHBoxLayout(panel)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(12)

        lbl_barcode = QLabel("📱 بارکد:")
        lbl_barcode.setStyleSheet("color: #6B5A8A; font-weight: 600; font-size: 13px;")
        lay.addWidget(lbl_barcode)

        self.scan_edit = QLineEdit()
        self.scan_edit.setPlaceholderText("🔍 اسکن بارکد/QR یا ورود دستی بارکد...")
        self.scan_edit.setStyleSheet("""
            QLineEdit {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 13px;
                color: #4a3a6a;
            }
            QLineEdit:focus {
                border-color: #a48ad6;
                background: #ffffff;
            }
            QLineEdit::placeholder {
                color: #b0a8c8;
                font-style: italic;
            }
        """)
        self.scan_edit.returnPressed.connect(self._on_scan)
        lay.addWidget(self.scan_edit, 1)

        manual_btn = QPushButton("📥 ثبت دستی")
        manual_btn.setObjectName("primaryBtn")
        manual_btn.setStyleSheet("""
            #primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a48ad6, stop:1 #8a6ed6);
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 22px;
                border: none;
                border-radius: 16px;
            }
            #primaryBtn:hover {
                background: #8a6ed6;
            }
        """)
        manual_btn.setCursor(Qt.PointingHandCursor)
        manual_btn.clicked.connect(self._on_scan)
        lay.addWidget(manual_btn)

        self.in_radio = QRadioButton("📥 ورود کالا")
        self.out_radio = QRadioButton("📤 خروج کالا")
        self.in_radio.setChecked(True)
        self.in_radio.setStyleSheet("color: #6B5A8A; font-size: 13px; font-weight: 500;")
        self.out_radio.setStyleSheet("color: #6B5A8A; font-size: 13px; font-weight: 500;")

        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.in_radio)
        self._mode_group.addButton(self.out_radio)
        lay.addWidget(self.in_radio)
        lay.addWidget(self.out_radio)

        lay.addWidget(QLabel("🔢 تعداد:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100_000)
        self.count_spin.setValue(1)
        self.count_spin.setStyleSheet("""
            QSpinBox {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 4px 10px;
                font-size: 13px;
                color: #4a3a6a;
                min-height: 30px;
            }
            QSpinBox:focus {
                border-color: #a48ad6;
            }
        """)
        lay.addWidget(self.count_spin)

        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("statusLbl")
        self.status_lbl.setMinimumWidth(240)
        self.status_lbl.setStyleSheet("""
            #statusLbl {
                font-size: 13px;
                font-weight: bold;
                padding: 6px 14px;
                background: rgba(245, 240, 255, 0.5);
                border-radius: 14px;
                color: #8a7aaa;
            }
        """)
        lay.addWidget(self.status_lbl)

        return panel

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 جستجو بر اساس نام یا بارکد...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 13px;
                color: #4a3a6a;
            }
            QLineEdit:focus {
                border-color: #a48ad6;
                background: #ffffff;
            }
            QLineEdit::placeholder {
                color: #b0a8c8;
                font-style: italic;
            }
        """)
        self.search_edit.textChanged.connect(lambda _t: self.refresh())
        toolbar.addWidget(self.search_edit, 1)

        buttons = (
            ("➕ افزودن", self._add, "#a48ad6"),
            ("✏️ ویرایش", self._edit, "#a48ad6"),
            ("🗑️ حذف", self._delete, "#e8739a"),
        )
        for text, slot, color in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 13px;
                    padding: 8px 22px;
                    border: none;
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {color}, stop:1 #8a6ed6);
                }}
            """)
            toolbar.addWidget(btn)

        return toolbar

    def _on_scan(self):
        barcode = self.scan_edit.text().strip()
        self.scan_edit.clear()

        if not barcode:
            self.scan_edit.setFocus()
            return

        count = self.count_spin.value()
        delta = count if self.in_radio.isChecked() else -count
        ok, msg, product = product_service.adjust_stock(barcode, delta)

        if ok:
            sign = "+" if delta > 0 else "-"
            self._set_status(
                f"✅ {product.name} {sign}{count} → موجودی: {product.quantity:,}",
                True,
            )
        else:
            self._set_status(f"❌ {msg}", False)

        self.refresh()
        self.scan_edit.setFocus()

    def _set_status(self, text: str, ok: bool):
        self.status_lbl.setText(text)
        color = "#5ab88a" if ok else "#e8739a"
        self.status_lbl.setStyleSheet(f"""
            #statusLbl {{
                color: {color};
                font-weight: bold;
                font-size: 13px;
                padding: 6px 14px;
                background: rgba(245, 240, 255, 0.5);
                border-radius: 14px;
            }}
        """)

    # ---------------------------------------------- منطق داده‌ها
    def refresh(self):
        query = self.search_edit.text().strip()
        self._products = product_service.list_products(query)

        self.table.setRowCount(len(self._products))

        for row, p in enumerate(self._products):
            b_type = p.barcode_type if p.barcode_type else "1D"
            formatted_price = f"{p.unit_price:,.0f} ریال"
            formatted_retail = f"{p.retail_price:,.0f} ریال"

            values = (
                p.name,
                p.barcode or "",
                b_type,
                f"{p.quantity:,}",
                formatted_price,
                formatted_retail,
                p.description or "",
            )

            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)

                if col == self.QTY_COL and p.quantity <= 0:
                    item.setForeground(QColor("#e8739a"))

                self.table.setItem(row, col, item)

    def _selected(self) -> Product | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._products):
            return self._products[row]
        return None

    # ---------------------------------------------- عملیات دکمه‌ها
    def _add(self):
        if ProductDialog(self).exec():
            self.refresh()

    def _edit(self):
        p = self._selected()

        if not p:
            QMessageBox.information(
                self, "💡 توجه", "ابتدا یک کالا انتخاب کنید."
            )
            return

        if ProductDialog(self, p).exec():
            self.refresh()

    def _delete(self):
        p = self._selected()

        if not p:
            QMessageBox.information(
                self, "💡 توجه", "ابتدا یک کالا انتخاب کنید."
            )
            return

        confirm = QMessageBox.question(
            self,
            "🗑️ حذف کالا",
            f"آیا از حذف کالای «{p.name}» مطمئن هستید؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            product_service.delete_product(p.id)
            self.refresh()

    # ---------------------------------------------- استایل‌دهی
    def _apply_styles(self):
        self.setStyleSheet("""
            #pageTitle {
                color: #5B4A8A;
                font-size: 20px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)