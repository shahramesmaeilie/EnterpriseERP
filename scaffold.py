import os

ROOT = "EnterpriseERP"

DIRS = [
    "app/database", "app/core", "app/models", "app/services",
    "app/ui/users", "app/ui/inventory", "app/ui/sales",
    "app/ui/purchases", "app/ui/employees", "app/ui/accounting",
    "app/ui/reports",
    "app/assets/icons", "app/assets/images", "app/assets/styles",
    "app/utils", "data", "tests",
]

FILES = [
    "app/__init__.py",
    "app/database/__init__.py", "app/database/connection.py",
    "app/database/models.py", "app/database/schema.py", "app/database/seed.py",
    "app/core/__init__.py", "app/core/config.py", "app/core/constants.py",
    "app/core/security.py", "app/core/session.py",
    "app/models/__init__.py", "app/models/user.py", "app/models/product.py",
    "app/models/customer.py", "app/models/supplier.py", "app/models/employee.py",
    "app/models/invoice.py", "app/models/payment.py",
    "app/services/__init__.py", "app/services/auth_service.py",
    "app/services/user_service.py", "app/services/product_service.py",
    "app/services/customer_service.py", "app/services/supplier_service.py",
    "app/services/employee_service.py", "app/services/invoice_service.py",
    "app/services/report_service.py",
    "app/ui/__init__.py", "app/ui/login.py", "app/ui/dashboard.py",
    "app/ui/users/__init__.py", "app/ui/users/users_page.py",
    "app/ui/inventory/__init__.py", "app/ui/inventory/products_page.py",
    "app/ui/inventory/inventory_page.py",
    "app/ui/sales/__init__.py", "app/ui/sales/sales_page.py",
    "app/ui/purchases/__init__.py", "app/ui/purchases/purchases_page.py",
    "app/ui/employees/__init__.py", "app/ui/employees/employees_page.py",
    "app/ui/accounting/__init__.py", "app/ui/accounting/accounting_page.py",
    "app/ui/reports/__init__.py", "app/ui/reports/reports_page.py",
    "app/assets/styles/main.qss",
    "app/utils/__init__.py", "app/utils/validators.py",
    "app/utils/helpers.py", "app/utils/logger.py",
    "tests/__init__.py", "tests/test_database.py", "tests/test_auth.py",
    "main.py", "requirements.txt", "README.md", ".gitignore",
]

for d in DIRS:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)
for f in FILES:
    open(os.path.join(ROOT, f), "a", encoding="utf-8").close()

print("✔ ساختار EnterpriseERP ساخته شد.")
