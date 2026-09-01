# -*- coding: utf-8 -*-
"""ماژول UI برنامه"""

# importها را به صورت try/except انجام دهید تا در صورت نبود ماژول خطا ندهد
try:
    from app.ui.utils.invoice_printer import InvoicePrinter
except ImportError:
    InvoicePrinter = None

__all__ = ['InvoicePrinter']
# -*- coding: utf-8 -*-
"""ماژول UI برنامه"""

from app.ui.login import LoginWindow
from app.ui.dashboard import Dashboard

__all__ = ['LoginWindow', 'Dashboard']