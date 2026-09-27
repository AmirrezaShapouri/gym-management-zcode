"""فیلد و ویجت تاریخ شمسی برای فرم‌های جنگو."""

from django import forms

from core import jalali


class JalaliDateWidget(forms.TextInput):
    """ورودی متنی که تاریخ شمسی می‌گیرد (مثل ۱۴۰۳/۰۶/۳۱)."""

    def format_value(self, value):
        return jalali.date_to_jalali_str(value)


class JalaliDateField(forms.DateField):
    """فیلد تاریخ که رشته شمسی را به date میلادی تبدیل می‌کند."""

    widget = JalaliDateWidget

    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, str):
            parsed = jalali.jalali_str_to_date(value)
            if parsed is None:
                raise forms.ValidationError(
                    'تاریخ را به شکل صحیح شمسی وارد کنید، مثلاً ۱۴۰۳/۰۶/۳۱.',
                    code='invalid',
                )
            return parsed
        return super().to_python(value)
