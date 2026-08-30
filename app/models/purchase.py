# -*- coding: utf-8 -*-
"""مدل فاکتور خرید (ورود کالا به انبار از شرکت فروشنده)"""

from dataclasses import dataclass, field


@dataclass
class PurchaseItem:
    id: int | None
    product_name: str      # snapshot نام کالا در لحظهٔ خرید
    barcode: str
    barcode_type: str      # "1D" یا "QR"
    quantity: int
    unit_price: float      # قیمت خرید هر واحد

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class PurchaseInvoice:
    id: int | None
    supplier: str          # نام شرکت فروشنده
    invoice_no: str        # شمارهٔ فاکتور خرید (روی برگهٔ شرکت)
    date: str
    items: list[PurchaseItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(i.total for i in self.items)
