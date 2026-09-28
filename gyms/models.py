from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def validate_invoice_image(file):
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    if Path(file.name).suffix.lower() not in allowed_extensions:
        raise ValidationError('فقط فایل‌های JPG، PNG یا WebP مجاز هستند.')
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('حجم تصویر رسید نباید بیشتر از ۵ مگابایت باشد.')


class GymSettings(models.Model):
    """تنظیمات باشگاه (تک‌نمونه‌ای)."""
    name = models.CharField('نام باشگاه', max_length=120, default='باشگاه ورزشی المپیک')
    phone = models.CharField('شماره تماس', max_length=30, blank=True)
    address = models.TextField('آدرس', blank=True)
    description = models.TextField('توضیحات', blank=True)
    logo = models.FileField('لوگو', upload_to='gym/', blank=True)
    primary_color = models.CharField('رنگ اصلی', max_length=7, default='#0d6efd')

    class Meta:
        verbose_name = 'تنظیمات باشگاه'
        verbose_name_plural = 'تنظیمات باشگاه'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk not in (None, 1):
            raise ValidationError('فقط یک رکورد تنظیمات باشگاه مجاز است.')
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class GymSubscription(models.Model):
    """اشتراک خود سامانه مدیریت باشگاه (نمایش در صفحه پروفایل)."""
    SESSION_CHOICES = [(12, '۱۲ جلسه'), (36, '۳۶ جلسه'), (120, '۱۲۰ جلسه')]
    STATUS_ACTIVE = 'فعال'
    STATUS_PENDING = 'در انتظار بررسی'
    STATUS_REJECTED = 'رد شده'
    STATUS_EXPIRED = 'منقضی'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, STATUS_ACTIVE),
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_REJECTED, STATUS_REJECTED),
        (STATUS_EXPIRED, STATUS_EXPIRED),
    ]
    PLAN_PRICES = {12: 2500000, 36: 6000000, 120: 25000000}
    PLAN_DURATIONS = {12: 30, 36: 90, 120: 365}

    sessions = models.PositiveIntegerField('دوره', choices=SESSION_CHOICES, default=12)
    price = models.DecimalField('مبلغ دوره (تومان)', max_digits=12, decimal_places=0, default=2500000,
                                validators=[MinValueValidator(0)])
    start_date = models.DateField('تاریخ شروع', null=True, blank=True)
    end_date = models.DateField('تاریخ پایان', null=True, blank=True)
    status = models.CharField('وضعیت', max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    invoice_image = models.ImageField(
        'تصویر رسید پرداخت', upload_to='gym_subscriptions/invoices/', blank=True,
        validators=[validate_invoice_image],
    )
    submitted_at = models.DateTimeField('تاریخ درخواست', default=timezone.now, editable=False)
    reviewed_at = models.DateTimeField('تاریخ بررسی', null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gym_subscription_reviews', verbose_name='بررسی‌کننده',
    )
    rejection_reason = models.TextField('دلیل رد', blank=True)

    class Meta:
        verbose_name = 'اشتراک باشگاه'
        verbose_name_plural = 'اشتراک‌های باشگاه'
        ordering = ('-end_date',)

    def __str__(self):
        return f'{self.get_sessions_display()} - {self.end_date}'

    @classmethod
    def expire_due(cls):
        return cls.objects.filter(
            status=cls.STATUS_ACTIVE,
            end_date__lt=timezone.localdate(),
        ).update(status=cls.STATUS_EXPIRED)

    def approve(self, reviewer):
        if self.status != self.STATUS_PENDING:
            raise ValidationError('فقط درخواست‌های در انتظار بررسی قابل تأیید هستند.')
        if not self.invoice_image:
            raise ValidationError('پیش از تأیید باید تصویر رسید ثبت شده باشد.')
        today = timezone.localdate()
        self.expire_due()
        active = GymSubscription.objects.filter(status=self.STATUS_ACTIVE).exclude(pk=self.pk)
        latest_active_end = active.order_by('-end_date').values_list('end_date', flat=True).first()
        start_date = max(today, latest_active_end + timedelta(days=1)) if latest_active_end else today
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=self.PLAN_DURATIONS[self.sessions] - 1)
        self.status = self.STATUS_ACTIVE
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.rejection_reason = ''
        self.save(update_fields=(
            'start_date', 'end_date', 'status', 'reviewed_at', 'reviewed_by', 'rejection_reason',
        ))

    def reject(self, reviewer, reason):
        if self.status != self.STATUS_PENDING:
            raise ValidationError('فقط درخواست‌های در انتظار بررسی قابل رد هستند.')
        if not reason.strip():
            raise ValidationError({'rejection_reason': 'برای رد درخواست، ذکر دلیل الزامی است.'})
        self.status = self.STATUS_REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.rejection_reason = reason.strip()
        self.save(update_fields=('status', 'reviewed_at', 'reviewed_by', 'rejection_reason'))
