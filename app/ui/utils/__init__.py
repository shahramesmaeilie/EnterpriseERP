# -*- coding: utf-8 -*-
"""ابزارهای کمکی برای UI"""

try:
    from app.ui.utils.invoice_printer import InvoicePrinter
except ImportError:
    InvoicePrinter = None

__all__ = ['InvoicePrinter']