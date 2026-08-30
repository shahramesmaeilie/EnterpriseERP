# -*- coding: utf-8 -*-
"""صفحه خرید و ورود کالا به انبار با پشتیبانی از قیمت خرید و قیمت مصرف‌کننده"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QDoubleSpinBox,
    QSpinBox, QComboBox, QMessageBox, QHeaderView, QFrame
)

from app.models.product import Product
from app.services.product_service import find_for_scan, create_product, update_product, adjust_stock


class PurchasesPage(QWidget):
    """نمای فاکتور خرید و ورود کالا به انبار"""

    # سیگنال برای اطلاع‌رسانی به صفحه انبار هنگام ثبت خرید جدید
    inventory_updated = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # عنوان و نوار بالا
        header_layout = QHBoxLayout()
        title = QLabel("🛒 خرید و ورود به انبار", objectName="pageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_new_invoice = QPushButton("📄 فاکتور خرید جدید")
        self.btn_new_invoice.setObjectName("btnTabActive")
        self.btn_history = QPushButton("📋 سابقۀ خریدها")
        self.btn_history.setObjectName("btnTab")
        header_layout.addWidget(self.btn_history)
        header_layout.addWidget(self.btn_new_invoice)
        main_layout.addLayout(header_layout)

        # کارت اطلاعات سربرگ فاکتور
        card_header = QFrame()
        card_header.setObjectName("cardFrame")
        layout_card_header = QHBoxLayout(card_header)
        layout_card_header.setContentsMargins(18, 14, 18, 14)
        layout_card_header.setSpacing(12)

        lbl_inv_no = QLabel("📝 شمارهٔ فاکتور:")
        lbl_inv_no.setObjectName("pastelLabel")
        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("شمارهٔ برگۀ فاکتور (اختیاری)")
        self.invoice_input.setObjectName("pastelInput")
        self.invoice_input.installEventFilter(self)

        lbl_seller = QLabel("🏢 شرکت فروشنده:")
        lbl_seller.setObjectName("pastelLabel")
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("نام شرکت...")
        self.company_input.setObjectName("pastelInput")
        self.company_input.installEventFilter(self)

        layout_card_header.addWidget(lbl_inv_no)
        layout_card_header.addWidget(self.invoice_input, 2)
        layout_card_header.addWidget(lbl_seller)
        layout_card_header.addWidget(self.company_input, 3)
        main_layout.addWidget(card_header)

        # کارت افزودن قلم کالا
        card_item = QFrame()
        card_item.setObjectName("cardFrame")
        layout_card_item = QVBoxLayout(card_item)
        layout_card_item.setContentsMargins(18, 14, 18, 14)
        layout_card_item.setSpacing(10)

        # ردیف بارکد
        row_barcode = QHBoxLayout()
        lbl_barcode = QLabel("📱 بارکد:")
        lbl_barcode.setObjectName("pastelLabel")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("🔍 اسکن بارکد/QR یا تایپ دستی شمارهٔ بارکد...")
        self.barcode_input.setObjectName("pastelInput")
        self.barcode_input.installEventFilter(self)
        row_barcode.addWidget(lbl_barcode)
        row_barcode.addWidget(self.barcode_input, 1)
        layout_card_item.addLayout(row_barcode)

        # ردیف نام کالا
        row_name = QHBoxLayout()
        lbl_name = QLabel("📦 نام کالا:")
        lbl_name.setObjectName("pastelLabel")
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("برای کالای جدید، نام را وارد کن ✏️")
        self.product_name_input.setObjectName("pastelInput")
        self.product_name_input.setEnabled(True)
        self.product_name_input.installEventFilter(self)
        row_name.addWidget(lbl_name)
        row_name.addWidget(self.product_name_input, 1)
        layout_card_item.addLayout(row_name)

        # ============================================================
        # ردیف اول جزئیات: نوع بارکد + تعداد + قیمت خرید
        # ============================================================
        row_details_1 = QHBoxLayout()
        row_details_1.setSpacing(10)

        # نوع بارکد
        lbl_type = QLabel("🔖 نوع بارکد:")
        lbl_type.setObjectName("pastelLabel")
        self.barcode_type_combo = QComboBox()
        self.barcode_type_combo.addItems(["(1D) بارکد معمولی", "(QR) کیوآرکد"])
        self.barcode_type_combo.setObjectName("pastelCombo")
        self.barcode_type_combo.setEnabled(True)
        self.barcode_type_combo.installEventFilter(self)
        row_details_1.addWidget(lbl_type)
        row_details_1.addWidget(self.barcode_type_combo)

        # تعداد
        lbl_qty = QLabel("🔢 تعداد:")
        lbl_qty.setObjectName("pastelLabel")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setObjectName("pastelSpin")
        self.quantity_spin.installEventFilter(self)
        row_details_1.addWidget(lbl_qty)
        row_details_1.addWidget(self.quantity_spin)

        # قیمت خرید
        lbl_unit = QLabel("💰 قیمت خرید واحد:")
        lbl_unit.setObjectName("pastelLabel")
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0, 999_999_999_999)
        self.unit_price_spin.setDecimals(0)
        self.unit_price_spin.setSingleStep(10000)
        self.unit_price_spin.setObjectName("pastelSpin")
        self.unit_price_spin.installEventFilter(self)
        row_details_1.addWidget(lbl_unit)
        row_details_1.addWidget(self.unit_price_spin, 1)

        layout_card_item.addLayout(row_details_1)

        # ============================================================
        # ردیف دوم جزئیات: قیمت مصرف‌کننده + دکمه افزودن
        # ============================================================
        row_details_2 = QHBoxLayout()
        row_details_2.setSpacing(10)

        # قیمت مصرف‌کننده
        lbl_retail = QLabel("🏷️ قیمت مصرف‌کننده:")
        lbl_retail.setObjectName("pastelLabel")
        self.retail_price_spin = QDoubleSpinBox()
        self.retail_price_spin.setRange(0, 999_999_999_999)
        self.retail_price_spin.setDecimals(0)
        self.retail_price_spin.setSingleStep(10000)
        self.retail_price_spin.setObjectName("pastelSpin")
        self.retail_price_spin.installEventFilter(self)
        row_details_2.addWidget(lbl_retail)
        row_details_2.addWidget(self.retail_price_spin, 1)

        # دکمه افزودن
        self.btn_add_item = QPushButton("➕ افزودن قلم")
        self.btn_add_item.setObjectName("btnAddItem")
        self.btn_add_item.clicked.connect(self._add_item_to_table)
        self.btn_add_item.installEventFilter(self)
        row_details_2.addWidget(self.btn_add_item)

        layout_card_item.addLayout(row_details_2)

        # برچسب راهنما / وضعیت کالا
        self.status_hint = QLabel("💡 منتظر اسکن بارکد یا ورود اطلاعات...")
        self.status_hint.setObjectName("statusHint")
        self.status_hint.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout_card_item.addWidget(self.status_hint)

        main_layout.addWidget(card_item)

        # جدول اقلام فاکتور
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "💰 جمع",
            "🏷️ مصرف‌کننده",
            "💰 خرید",
            "🔢 تعداد",
            "🔖 نوع",
            "📱 بارکد",
            "📦 نام کالا"
        ])
        self.items_table.setObjectName("pastelTable")
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setLayoutDirection(Qt.RightToLeft)
        self.items_table.installEventFilter(self)
        main_layout.addWidget(self.items_table, 1)

        # نوار پایین: جمع کل و دکمه‌های عملیات
        footer_layout = QHBoxLayout()

        self.total_label = QLabel("🧮 جمع کل: ۰ ریال")
        self.total_label.setObjectName("totalLabel")
        footer_layout.addWidget(self.total_label)

        footer_layout.addStretch()

        self.btn_delete_row = QPushButton("🗑️ حذف قلم")
        self.btn_delete_row.setObjectName("btnDelete")
        self.btn_delete_row.clicked.connect(self._delete_selected_item)
        self.btn_delete_row.installEventFilter(self)

        self.btn_submit = QPushButton("✅ ثبت فاکتور و انتقال به انبار")
        self.btn_submit.setObjectName("btnSubmit")
        self.btn_submit.clicked.connect(self._submit_purchase)
        self.btn_submit.installEventFilter(self)

        footer_layout.addWidget(self.btn_delete_row)
        footer_layout.addWidget(self.btn_submit)

        main_layout.addLayout(footer_layout)

        # لیست ویجت‌ها برای حرکت با Enter
        self._widget_list = [
            self.invoice_input,
            self.company_input,
            self.barcode_input,
            self.product_name_input,
            self.barcode_type_combo,
            self.quantity_spin,
            self.unit_price_spin,
            self.retail_price_spin,
            self.btn_add_item,
            self.btn_delete_row,
            self.btn_submit,
        ]

        self._apply_styles()
        self.barcode_input.setFocus()

    def eventFilter(self, obj, event):
        """فیلتر رویدادها برای مدیریت کلید Enter و Shift+Enter"""
        if event.type() == event.Type.KeyPress:
            # بررسی کلید Enter
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # اگر Shift هم فشار داده شده باشد => حرکت به عقب
                if event.modifiers() & Qt.ShiftModifier:
                    self._focus_previous(obj)
                else:
                    # حرکت به جلو
                    self._focus_next(obj)
                return True
        return super().eventFilter(obj, event)

    def _focus_next(self, current_widget):
        """حرکت به ویجت بعدی"""
        try:
            current_index = self._widget_list.index(current_widget)
            next_index = (current_index + 1) % len(self._widget_list)
            self._widget_list[next_index].setFocus()
            
            # اگر ویجت بعدی QComboBox باشد، منوی آن را باز کن
            if isinstance(self._widget_list[next_index], QComboBox):
                self._widget_list[next_index].showPopup()
        except ValueError:
            pass

    def _focus_previous(self, current_widget):
        """حرکت به ویجت قبلی"""
        try:
            current_index = self._widget_list.index(current_widget)
            prev_index = (current_index - 1) % len(self._widget_list)
            self._widget_list[prev_index].setFocus()
            
            # اگر ویجت قبلی QComboBox باشد، منوی آن را باز کن
            if isinstance(self._widget_list[prev_index], QComboBox):
                self._widget_list[prev_index].showPopup()
        except ValueError:
            pass

    def _apply_styles(self):
        """اعمال استایل‌های پاستیلی و گرد صفحه"""
        self.setStyleSheet("""
            /* استایل کلی صفحه */
            #pageTitle {
                color: #5B4A8A;
                font-size: 20px;
                font-weight: bold;
                padding: 8px 0;
            }
            
            /* کارت‌های گرد با سایه ملایم */
            #cardFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f6ff);
                border: 1px solid #e8e0f5;
                border-radius: 20px;
                padding: 10px;
            }
            #cardFrame:hover {
                border-color: #d5c8ed;
            }
            
            /* لیبل‌های پاستیلی با فونت کوچکتر */
            #pastelLabel {
                color: #6B5A8A;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 10px;
                background: rgba(235, 225, 250, 0.3);
                border-radius: 12px;
                min-width: 80px;
            }
            
            /* ورودی‌های گرد و پاستیلی با فونت کوچکتر */
            #pastelInput {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 8px 14px;
                font-size: 12px;
                color: #4a3a6a;
                transition: all 0.3s ease;
                min-height: 30px;
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
                font-size: 11px;
            }
            
            /* کامبو باکس پاستیلی */
            #pastelCombo {
                background: #faf8ff;
                border: 2px solid #e8e0f5;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 12px;
                color: #4a3a6a;
                min-height: 30px;
                min-width: 120px;
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
                font-size: 12px;
                color: #4a3a6a;
                min-height: 30px;
                min-width: 100px;
            }
            #pastelSpin:hover {
                border-color: #d5c8ed;
            }
            #pastelSpin:focus {
                border-color: #a48ad6;
                box-shadow: 0 0 0 4px rgba(164, 138, 214, 0.15);
            }
            
            /* دکمه‌های تب */
            #btnTabActive {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8a6ed6, stop:1 #6a4c9c);
                color: #ffffff;
                font-weight: bold;
                border-radius: 16px;
                border: none;
                padding: 8px 18px;
                font-size: 12px;
                transition: all 0.3s ease;
            }
            #btnTabActive:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(106, 76, 156, 0.35);
            }
            
            #btnTab {
                background: #f0ecf8;
                color: #6a5a8a;
                font-weight: 600;
                border-radius: 16px;
                border: none;
                padding: 8px 18px;
                font-size: 12px;
                transition: all 0.3s ease;
            }
            #btnTab:hover {
                background: #e5def5;
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(106, 76, 156, 0.2);
            }
            
            /* دکمه افزودن قلم - بزرگتر */
            #btnAddItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a48ad6, stop:1 #8a6ed6);
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 16px;
                padding: 10px 28px;
                font-size: 13px;
                min-width: 140px;
                transition: all 0.3s ease;
            }
            #btnAddItem:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(138, 110, 214, 0.4);
            }
            #btnAddItem:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 8px rgba(138, 110, 214, 0.3);
            }
            
            /* دکمه حذف */
            #btnDelete {
                background: #fff0f5;
                color: #e8739a;
                border: 2px solid #fce0e8;
                border-radius: 16px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 12px;
                transition: all 0.3s ease;
            }
            #btnDelete:hover {
                background: #ffe8ef;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(232, 115, 154, 0.25);
                border-color: #f8c8d8;
            }
            #btnDelete:pressed {
                transform: translateY(0px);
            }
            
            /* دکمه ثبت فاکتور */
            #btnSubmit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7bc8a4, stop:1 #5ab88a);
                color: white;
                border: none;
                border-radius: 16px;
                padding: 8px 22px;
                font-weight: bold;
                font-size: 12px;
                transition: all 0.3s ease;
            }
            #btnSubmit:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(90, 184, 138, 0.4);
            }
            #btnSubmit:pressed {
                transform: translateY(0px);
                box-shadow: 0 2px 8px rgba(90, 184, 138, 0.3);
            }
            
            /* جمع کل */
            #totalLabel {
                font-size: 16px;
                font-weight: bold;
                color: #5B4A8A;
                background: rgba(235, 225, 250, 0.3);
                padding: 6px 18px;
                border-radius: 16px;
                border: 2px solid #e8e0f5;
            }
            
            /* وضعیت راهنما */
            #statusHint {
                font-size: 12px;
                color: #8a7aaa;
                padding: 6px 14px;
                background: rgba(245, 240, 255, 0.5);
                border-radius: 14px;
                font-style: italic;
                min-height: 30px;
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
                font-size: 12px;
            }
            #pastelTable::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d5c8ed, stop:1 #e8e0f5);
                color: #3a2a5a;
                border-radius: 10px;
            }
            #pastelTable::item:hover {
                background: rgba(213, 200, 237, 0.3);
                border-radius: 10px;
            }
            
            /* هدر جدول */
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8e0f5, stop:1 #d5c8ed);
                color: #4a3a6a;
                font-weight: bold;
                border: none;
                border-right: 1px solid #f0ecf8;
                padding: 10px 6px;
                font-size: 11px;
            }
            QHeaderView::section:last {
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
            QTableWidget::item {
                padding: 8px 6px;
                border-radius: 8px;
                font-size: 12px;
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

    def _on_barcode_entered(self) -> None:
        """بررسی بارکد اسکن‌شده و یافتن کالا در دیتابیس"""
        barcode = self.barcode_input.text().strip()

        if not barcode:
            return

        product = find_for_scan(barcode)

        if product:
            self.product_name_input.setText(product.name)
            self.barcode_type_combo.setCurrentText(product.barcode_type)
            self.unit_price_spin.setValue(float(product.unit_price or 0))
            self.retail_price_spin.setValue(float(product.retail_price or 0))
            self.status_hint.setText(
                f"✅ کالا یافت شد: {product.name} (موجودی فعلی: {product.quantity})"
            )
            self.status_hint.setStyleSheet("color: #5ab88a; font-weight: bold;")
            # حرکت به ویجت بعدی (نام کالا)
            self._focus_next(self.barcode_input)
        else:
            self.product_name_input.clear()
            self.unit_price_spin.setValue(0.0)
            self.retail_price_spin.setValue(0.0)
            self.status_hint.setText(
                "⚠️ کالا در دیتابیس یافت نشد. می‌توانید نام و مشخصات جدید را وارد کنید."
            )
            self.status_hint.setStyleSheet("color: #e8739a; font-weight: bold;")
            self.quantity_spin.setValue(1)
            # حرکت به ویجت نام کالا
            self.product_name_input.setFocus()

    def _add_item_to_table(self) -> None:
        """افزودن کالا به جدول فاکتور جاری"""
        barcode = self.barcode_input.text().strip()
        name = self.product_name_input.text().strip()
        qty = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        retail_price = self.retail_price_spin.value()
        barcode_type = self.barcode_type_combo.currentText()

        if not barcode:
            QMessageBox.warning(self, "⚠️ خطا", "لطفاً ابتدا بارکد کالا را وارد کنید.")
            self.barcode_input.setFocus()
            return

        if not name:
            QMessageBox.warning(self, "⚠️ خطا", "لطفاً نام کالا را وارد کنید.")
            self.product_name_input.setFocus()
            return

        total_price = qty * unit_price

        # بررسی تکراری نبودن بارکد در جدول
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 5).text() == barcode:
                old_qty = int(self.items_table.item(row, 3).text())
                new_qty = old_qty + qty
                new_total = new_qty * unit_price

                self.items_table.setItem(row, 3, QTableWidgetItem(str(new_qty)))
                self.items_table.setItem(row, 2, QTableWidgetItem(f"{unit_price:,.0f}"))
                self.items_table.setItem(row, 1, QTableWidgetItem(f"{retail_price:,.0f}"))
                self.items_table.setItem(row, 0, QTableWidgetItem(f"{new_total:,.0f}"))

                self._update_total_sum()
                self._clear_item_inputs()
                return

        # افزودن ردیف جدید
        row_idx = self.items_table.rowCount()
        self.items_table.insertRow(row_idx)

        self.items_table.setItem(row_idx, 0, QTableWidgetItem(f"{total_price:,.0f}"))
        self.items_table.setItem(row_idx, 1, QTableWidgetItem(f"{retail_price:,.0f}"))
        self.items_table.setItem(row_idx, 2, QTableWidgetItem(f"{unit_price:,.0f}"))
        self.items_table.setItem(row_idx, 3, QTableWidgetItem(str(qty)))
        self.items_table.setItem(row_idx, 4, QTableWidgetItem(barcode_type))
        self.items_table.setItem(row_idx, 5, QTableWidgetItem(barcode))
        self.items_table.setItem(row_idx, 6, QTableWidgetItem(name))

        self._update_total_sum()
        self._clear_item_inputs()

    def _delete_selected_item(self) -> None:
        """حذف ردیف‌های انتخاب‌شده از جدول"""
        selected_ranges = self.items_table.selectedRanges()

        if not selected_ranges:
            QMessageBox.information(self, "💡 راهنما", "ردیفی را برای حذف انتخاب کنید.")
            return

        rows_to_delete = sorted(
            {r for sr in selected_ranges for r in range(sr.topRow(), sr.bottomRow() + 1)},
            reverse=True
        )

        for row in rows_to_delete:
            self.items_table.removeRow(row)

        self._update_total_sum()

    def _update_total_sum(self) -> None:
        """محاسبه و به‌روزرسانی جمع کل فاکتور"""
        total = 0.0

        for row in range(self.items_table.rowCount()):
            raw_text = self.items_table.item(row, 0).text().replace(",", "")
            try:
                total += float(raw_text)
            except ValueError:
                pass

        self.total_label.setText(f"🧮 جمع کل: {total:,.0f} ریال")

    def _clear_item_inputs(self) -> None:
        """پاکسازی فیلدهای ورود اطلاعات کالا"""
        self.barcode_input.clear()
        self.product_name_input.clear()
        self.quantity_spin.setValue(1)
        self.unit_price_spin.setValue(0.0)
        self.retail_price_spin.setValue(0.0)
        self.status_hint.setText("💡 منتظر اسکن بارکد یا ورود اطلاعات...")
        self.status_hint.setStyleSheet("color: #8a7aaa; font-weight: normal;")
        self.barcode_input.setFocus()

    def _submit_purchase(self) -> None:
        """ثبت نهایی فاکتور خرید و انتقال موجودی به انبار در دیتابیس"""
        row_count = self.items_table.rowCount()

        if row_count == 0:
            QMessageBox.warning(self, "⚠️ خطا", "فاکتور خالی است! حداقل یک قلم کالا اضافه کنید.")
            return

        invoice_no = self.invoice_input.text().strip()
        seller = self.company_input.text().strip()

        # ثبت یا آپدیت تک‌تک اقلام در دیتابیس
        for row in range(row_count):
            name = self.items_table.item(row, 6).text()
            barcode = self.items_table.item(row, 5).text()
            barcode_type = self.items_table.item(row, 4).text()
            qty = int(self.items_table.item(row, 3).text())
            unit_price = float(self.items_table.item(row, 2).text().replace(",", ""))
            retail_price = float(self.items_table.item(row, 1).text().replace(",", ""))

            # بررسی وجود کالا در بانک اطلاعاتی
            product = find_for_scan(barcode)

            if product:
                # کالا وجود دارد، اطلاعات قیمت را بروزرسانی کرده و موجودی را اضافه می‌کنیم
                product.name = name
                product.unit_price = unit_price
                product.retail_price = retail_price
                product.barcode_type = barcode_type
                update_product(product)
                adjust_stock(product.id, qty)
            else:
                # کالای جدید ثبت می‌شود
                new_product = Product(
                    id=None,
                    name=name,
                    barcode=barcode,
                    barcode_type=barcode_type,
                    quantity=qty,
                    unit_price=unit_price,
                    retail_price=retail_price,
                    description=None
                )
                create_product(new_product)

        # ارسال سیگنال رفرش به صفحه انبار
        self.inventory_updated.emit()

        QMessageBox.information(
            self,
            "✅ ثبت موفق",
            f"🎉 فاکتور خرید با تعداد {row_count} قلم کالا ثبت شد و موجودی انبار به‌روزرسانی گردید."
        )

        # ریست فاکتور
        self.items_table.setRowCount(0)
        self.invoice_input.clear()
        self.company_input.clear()
        self.total_label.setText("🧮 جمع کل: ۰ ریال")
        self._clear_item_inputs()