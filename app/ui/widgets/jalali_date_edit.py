# -*- coding: utf-8 -*-
"""ویجت انتخاب تاریخ شمسی"""

from PySide6.QtCore import Qt, QDate, Signal, QDateTime, QPoint
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout,
    QFrame, QGridLayout, QSpacerItem, QSizePolicy, QApplication
)

import jdatetime


class JalaliDateEdit(QWidget):
    """ویجت انتخاب تاریخ شمسی با تقویم بازشونده"""

    dateChanged = Signal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date = jdatetime.date.today()
        self._calendar_visible = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # نمایش تاریخ
        self.date_label = QPushButton()
        self.date_label.setObjectName("jalaliDateLabel")
        self.date_label.clicked.connect(self._toggle_calendar)
        self._update_label()
        layout.addWidget(self.date_label)

        # دکمه پاک کردن
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setObjectName("clearDateBtn")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.clicked.connect(self._clear_date)
        layout.addWidget(self.clear_btn)

        # تقویم (در ابتدا مخفی)
        self.calendar_frame = QFrame()
        self.calendar_frame.setObjectName("calendarFrame")
        self.calendar_frame.setVisible(False)
        self.calendar_frame.setWindowFlags(Qt.Popup)
        self._build_calendar()

    def _build_calendar(self):
        """ساخت تقویم شمسی"""
        layout = QVBoxLayout(self.calendar_frame)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # هدر ماه/سال
        header = QHBoxLayout()
        header.setSpacing(4)

        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.setObjectName("calendarNavBtn")
        self.prev_month_btn.clicked.connect(self._prev_month)
        header.addWidget(self.prev_month_btn)

        self.month_year_label = QLabel()
        self.month_year_label.setObjectName("calendarMonthYear")
        self.month_year_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.month_year_label, 1)

        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.setObjectName("calendarNavBtn")
        self.next_month_btn.clicked.connect(self._next_month)
        header.addWidget(self.next_month_btn)

        layout.addLayout(header)

        # روزهای هفته
        weekdays_layout = QHBoxLayout()
        weekdays = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
        for day in weekdays:
            lbl = QLabel(day)
            lbl.setObjectName("weekdayLabel")
            lbl.setAlignment(Qt.AlignCenter)
            weekdays_layout.addWidget(lbl)
        layout.addLayout(weekdays_layout)

        # شبکه روزها
        self.days_grid = QGridLayout()
        self.days_grid.setSpacing(2)
        
        # ایجاد دکمه‌های روزها
        self.day_buttons = []
        for i in range(6):
            row_btns = []
            for j in range(7):
                btn = QPushButton()
                btn.setObjectName("dayBtn")
                btn.setFixedSize(32, 32)
                btn.clicked.connect(self._on_day_clicked)
                self.days_grid.addWidget(btn, i, j)
                row_btns.append(btn)
            self.day_buttons.append(row_btns)
        layout.addLayout(self.days_grid)

        # دکمه امروز
        today_btn = QPushButton("امروز")
        today_btn.setObjectName("todayBtn")
        today_btn.clicked.connect(self._set_today)
        layout.addWidget(today_btn)

    def _update_label(self):
        """به‌روزرسانی نمایش تاریخ"""
        if self._date:
            self.date_label.setText(self._date.strftime("%Y/%m/%d"))
        else:
            self.date_label.setText("انتخاب تاریخ")

    def _update_calendar(self):
        """به‌روزرسانی نمایش تقویم"""
        if not self._date:
            return

        # به‌روزرسانی عنوان ماه/سال
        self.month_year_label.setText(
            f"{self._date.strftime('%B')} {self._date.year}"
        )

        # یافتن روز اول ماه و تعداد روزها
        first_day = jdatetime.date(self._date.year, self._date.month, 1)
        
        # دریافت تعداد روزهای ماه - روش صحیح
        try:
            # روش جدید
            days_in_month = jdatetime.date.days_in_month(self._date.year, self._date.month)
        except:
            try:
                # روش جایگزین
                days_in_month = self._date.days_in_month
            except:
                # روش دستی
                if self._date.month <= 6:
                    days_in_month = 31
                else:
                    days_in_month = 30

        # محاسبه شروع ماه (0=شنبه)
        start_weekday = first_day.weekday()

        # پر کردن روزها
        day = 1
        for i in range(6):
            for j in range(7):
                btn = self.day_buttons[i][j]
                if i == 0 and j < start_weekday:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setProperty("day", 0)
                elif day <= days_in_month:
                    btn.setText(str(day))
                    btn.setEnabled(True)
                    # برجسته کردن روز انتخاب شده
                    if day == self._date.day:
                        btn.setProperty("selected", True)
                    else:
                        btn.setProperty("selected", False)
                    btn.setProperty("day", day)
                    # اطمینان از استایل مجدد
                    btn.style().polish(btn)
                    day += 1
                else:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setProperty("day", 0)

    def _toggle_calendar(self):
        """نمایش/مخفی کردن تقویم"""
        if self._calendar_visible:
            self.calendar_frame.setVisible(False)
            self._calendar_visible = False
        else:
            # موقعیت تقویم را زیر ویجت تنظیم می‌کنیم
            pos = self.mapToGlobal(QPoint(0, self.height()))
            # اطمینان از اینکه تقویم در صفحه نمایش قرار می‌گیرد
            screen = QApplication.primaryScreen().availableGeometry()
            if pos.x() + self.calendar_frame.width() > screen.width():
                pos.setX(screen.width() - self.calendar_frame.width())
            if pos.y() + self.calendar_frame.height() > screen.height():
                pos.setY(screen.height() - self.calendar_frame.height())
            
            self.calendar_frame.move(pos)
            self.calendar_frame.setVisible(True)
            self._calendar_visible = True
            self._update_calendar()

    def _on_day_clicked(self):
        """انتخاب روز از تقویم"""
        btn = self.sender()
        day = btn.property("day")
        if day and day > 0:
            try:
                new_date = jdatetime.date(self._date.year, self._date.month, day)
                self.set_date(new_date)
                self._toggle_calendar()
            except ValueError:
                pass

    def _prev_month(self):
        """ماه قبل"""
        if self._date:
            if self._date.month == 1:
                new_date = jdatetime.date(self._date.year - 1, 12, 1)
            else:
                new_date = jdatetime.date(self._date.year, self._date.month - 1, 1)
            self._date = new_date
            self._update_calendar()

    def _next_month(self):
        """ماه بعد"""
        if self._date:
            if self._date.month == 12:
                new_date = jdatetime.date(self._date.year + 1, 1, 1)
            else:
                new_date = jdatetime.date(self._date.year, self._date.month + 1, 1)
            self._date = new_date
            self._update_calendar()

    def _set_today(self):
        """تنظیم به تاریخ امروز"""
        self.set_date(jdatetime.date.today())
        self._toggle_calendar()

    def _clear_date(self):
        """پاک کردن تاریخ"""
        self._date = None
        self._update_label()
        self.dateChanged.emit(QDate())

    def set_date(self, date: jdatetime.date):
        """تنظیم تاریخ"""
        self._date = date
        self._update_label()
        # ارسال سیگنال با تاریخ میلادی
        try:
            gregorian = self._jalali_to_gregorian(date)
            if gregorian:
                self.dateChanged.emit(QDate(gregorian.year, gregorian.month, gregorian.day))
        except:
            pass

    def _jalali_to_gregorian(self, jalali_date: jdatetime.date):
        """تبدیل تاریخ شمسی به میلادی"""
        if not jalali_date:
            return None
        try:
            return jalali_date.togregorian()
        except AttributeError:
            try:
                return jalali_date.to_gregorian()
            except:
                try:
                    return jdatetime.date.togregorian(jalali_date)
                except:
                    year = jalali_date.year + 621
                    month = jalali_date.month
                    day = jalali_date.day
                    if month > 6:
                        year += 1
                        month = month - 6
                    return jdatetime.date(year, month, day)

    def date(self) -> QDate:
        """دریافت تاریخ به صورت QDate"""
        if self._date:
            gregorian = self._jalali_to_gregorian(self._date)
            if gregorian:
                return QDate(gregorian.year, gregorian.month, gregorian.day)
        return QDate()

    def jalali_date(self) -> jdatetime.date:
        """دریافت تاریخ شمسی"""
        return self._date

    def get_gregorian_string(self) -> str:
        """دریافت تاریخ میلادی به صورت رشته"""
        if self._date:
            gregorian = self._jalali_to_gregorian(self._date)
            if gregorian:
                return f"{gregorian.year}-{gregorian.month:02d}-{gregorian.day:02d}"
        return ""