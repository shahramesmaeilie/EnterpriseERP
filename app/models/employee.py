from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    """مدل کارمند. نگاشت ستون دیتابیس full_name به فیلد name."""

    id: Optional[int]
    name: str                       # ستون دیتابیس: full_name
    national_id: str = ""
    phone: str = ""
    job_title: str = ""
    salary: float = 0.0
    hire_date: str = ""
    is_active: bool = True
    created_at: Optional[str] = None

    @staticmethod
    def from_row(row) -> "Employee":
        """ساخت مدل از sqlite3.Row (نیازمند conn.row_factory = sqlite3.Row)."""
        keys = row.keys()
        return Employee(
            id=row["id"],
            name=row["full_name"] or "",
            national_id=(row["national_id"] or "") if "national_id" in keys else "",
            phone=(row["phone"] or "") if "phone" in keys else "",
            job_title=(row["job_title"] or "") if "job_title" in keys else "",
            salary=float(row["salary"] or 0) if "salary" in keys else 0.0,
            hire_date=(row["hire_date"] or "") if "hire_date" in keys else "",
            is_active=bool(row["is_active"]) if "is_active" in keys else True,
            created_at=row["created_at"] if "created_at" in keys else None,
        )

    def to_params(self) -> dict:
        """پارامترهای نام‌دار برای INSERT/UPDATE با نام ستون‌های واقعی."""
        return {
            "full_name": self.name,
            "national_id": self.national_id,
            "phone": self.phone,
            "job_title": self.job_title,
            "salary": float(self.salary or 0),
            "hire_date": self.hire_date,
            "is_active": 1 if self.is_active else 0,
        }
