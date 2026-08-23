from dataclasses import dataclass, field


@dataclass
class User:
    id: int | None = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    is_active: bool = True
    permissions: list[str] = field(default_factory=list)


@dataclass
class Product:
    id: int | None = None
    name: str = ""
    category_id: int | None = None
    price: float = 0.0
    stock: int = 0


@dataclass
class Customer:
    id: int | None = None
    full_name: str = ""
    phone: str | None = None
