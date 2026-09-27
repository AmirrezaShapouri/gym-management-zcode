from django import template

from core import jalali

register = template.Library()


@register.filter
def jdate(value):
    """نمایش تاریخ میلادی به شکل شمسی: ۱۴۰۳/۰۶/۳۱"""
    return jalali.date_to_jalali_str(value)


@register.filter
def jmonth_year(value):
    """نمایش تاریخ به شکل «مهر ۱۴۰۳»."""
    if not value:
        return ''
    jy, jm, _ = jalali.gregorian_to_jalali(value.year, value.month, value.day)
    return f'{jalali.jalali_month_name(jm)} {jalali.fa_digits(jy)}'


@register.filter
def day_names(value):
    """تبدیل کلیدهای روز ('saturday monday') به «شنبه، دوشنبه»."""
    if not value:
        return ''
    keys = str(value).replace(',', ' ').split()
    return '، '.join(jalali.weekday_label(key) for key in keys)


@register.filter
def fa(value):
    """نمایش عدد با ارقام فارسی و جداکننده هزارگان."""
    try:
        return jalali.fa_digits(f'{int(value):,}')
    except (TypeError, ValueError):
        return jalali.fa_digits(value)


@register.filter
def en_key(value):
    """برچسب فارسی روز → کلید انگلیسی (برای selected شدن در فرم)."""
    for key, label in jalali.WEEKDAY_KEYS:
        if label == value:
            return key
    return value
