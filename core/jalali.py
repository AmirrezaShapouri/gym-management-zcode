"""تبدیل تاریخ میلادی ↔ شمسی بدون وابستگی خارجی."""

from datetime import date

PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
ENGLISH_DIGITS = '0123456789'

MONTH_NAMES = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند',
]

WEEKDAY_KEYS = [
    ('saturday', 'شنبه'),
    ('sunday', 'یکشنبه'),
    ('monday', 'دوشنبه'),
    ('tuesday', 'سه‌شنبه'),
    ('wednesday', 'چهارشنبه'),
    ('thursday', 'پنج‌شنبه'),
    ('friday', 'جمعه'),
]
WEEKDAY_LABELS = dict(WEEKDAY_KEYS)

_TRANSLATION = str.maketrans(PERSIAN_DIGITS + '٫', ENGLISH_DIGITS + '.')
_FA_TRANSLATION = str.maketrans(ENGLISH_DIGITS, PERSIAN_DIGITS)


def normalize_digits(value):
    """تبدیل ارقام فارسی به لاتین."""
    return str(value).translate(_TRANSLATION)


def fa_digits(value):
    """تبدیل ارقام لاتین به فارسی."""
    return str(value).translate(_FA_TRANSLATION)


def gregorian_to_jalali(gy, gm, gd):
    g_days_in_month = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    jy = 0 if gy <= 1600 else 979
    gy -= 621 if gy <= 1600 else 1600
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 - 80 + gd + g_days_in_month[gm - 1])
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += (jm - 7) * 30 + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    month_lengths = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for length in month_lengths:
        if gd <= length:
            break
        gd -= length
        gm += 1
    return gy, gm, gd


def date_to_jalali_str(value):
    """date → '۱۴۰۳/۰۶/۳۱' با ارقام فارسی."""
    if value is None:
        return ''
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return fa_digits(f'{jy}/{jm:02d}/{jd:02d}')


def jalali_str_to_date(value):
    """'۱۴۰۳/۶/۳۱' یا '1403-06-31' → date؛ در صورت نامعتبر بودن None."""
    if value is None:
        return None
    text = normalize_digits(value).strip().replace('-', '/').replace('.', '/')
    parts = [p for p in text.split('/') if p != '']
    if len(parts) != 3:
        return None
    try:
        jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
        if not 1 <= jm <= 12 or jd < 1:
            return None
        gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
        converted = date(gy, gm, gd)
        return converted if gregorian_to_jalali(gy, gm, gd) == (jy, jm, jd) else None
    except (ValueError, OverflowError):
        return None


def jalali_month_name(month):
    if 1 <= int(month) <= 12:
        return MONTH_NAMES[int(month) - 1]
    return ''


def weekday_label(key):
    return WEEKDAY_LABELS.get(key, key)


def today_jalali_str(today=None):
    return date_to_jalali_str(today or date.today())
