# app/models/product.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    id: Optional[int]
    name: str
    barcode: Optional[str] = None
    barcode_type: Optional[str] = None
    quantity: int = 0            # ستون اصلی موجودی (purchases.py استفاده می‌کنه)
    stock: int = 0               # ستون موازی — برای backward compat نگه داشته شده
    unit_price: float = 0.0      # قیمت خرید
    retail_price: float = 0.0    # قیمت فروش
    price: float = 0.0           # قیمت عمومی (sales.py خط ۴۸ از retail_price استفاده می‌کنه)
    description: Optional[str] = None
    category_id: Optional[int] = None

    # --- ORM helpers ---

    @classmethod
    def from_row(cls, row) -> "Product":
        """از sqlite3.Row یا dict می‌سازد."""
        d = dict(row)
        return cls(
            id=d.get("id"),
            name=d.get("name", ""),
            barcode=d.get("barcode"),
            barcode_type=d.get("barcode_type"),
            quantity=d.get("quantity") or 0,
            stock=d.get("stock") or 0,
            unit_price=d.get("unit_price") or 0.0,
            retail_price=d.get("retail_price") or 0.0,
            price=d.get("price") or d.get("retail_price") or 0.0,
            description=d.get("description"),
            category_id=d.get("category_id"),
        )

    def to_params(self) -> dict:
        """پارامترهای INSERT/UPDATE بدون id."""
        return {
            "name": self.name,
            "barcode": self.barcode,
            "barcode_type": self.barcode_type,
            "quantity": self.quantity,
            "stock": self.stock,
            "unit_price": self.unit_price,
            "retail_price": self.retail_price,
            "price": self.price,
            "description": self.description,
            "category_id": self.category_id,
        }
