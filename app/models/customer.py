from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """مدل مشتری. نگاشت ستون دیتابیس full_name به فیلد name."""

    id: Optional[int]
    name: str                       # ستون دیتابیس: full_name
    phone: str = ""
    address: str = ""
    email: str = ""
    created_at: Optional[str] = None

    @staticmethod
    def from_row(row) -> "Customer":
        """ساخت مدل از sqlite3.Row (نیازمند conn.row_factory = sqlite3.Row)."""
        keys = row.keys()
        return Customer(
            id=row["id"],
            name=row["full_name"] or "",
            phone=(row["phone"] or "") if "phone" in keys else "",
            address=(row["address"] or "") if "address" in keys else "",
            email=(row["email"] or "") if "email" in keys else "",
            created_at=row["created_at"] if "created_at" in keys else None,
        )

    def to_params(self) -> dict:
        """پارامترهای نام‌دار برای INSERT/UPDATE با نام ستون‌های واقعی."""
        return {
            "full_name": self.name,
            "phone": self.phone,
            "address": self.address,
            "email": self.email,
        }
