from dataclasses import dataclass, field

@dataclass
class InvoiceItem:
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    id: int | None = None
    invoice_id: int | None = None

    @property
    def total(self) -> float:
        """جمع سطر — در دیتابیس ذخیره نمی‌شود، همیشه محاسبه می‌گردد."""
        return round(self.quantity * self.unit_price, 2)
