from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


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
    STATUS_PENDING = 'در انتظار پرداخت'
    STATUS_CHOICES = [(STATUS_ACTIVE, STATUS_ACTIVE), (STATUS_PENDING, STATUS_PENDING)]

    sessions = models.PositiveIntegerField('دوره', choices=SESSION_CHOICES, default=12)
    price = models.DecimalField('مبلغ دوره (تومان)', max_digits=12, decimal_places=0, default=2500000,
                                validators=[MinValueValidator(0)])
    start_date = models.DateField('تاریخ شروع')
    end_date = models.DateField('تاریخ پایان')
    status = models.CharField('وضعیت', max_length=30, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        verbose_name = 'اشتراک باشگاه'
        verbose_name_plural = 'اشتراک‌های باشگاه'
        ordering = ('-end_date',)

    def __str__(self):
        return f'{self.get_sessions_display()} - {self.end_date}'

    def apply_renewal(self, sessions, price):
        """ثبت درخواست تمدید: وضعیت به «در انتظار پرداخت» تغییر می‌کند."""
        self.sessions = sessions
        self.price = price
        self.status = self.STATUS_PENDING
        self.save(update_fields=['sessions', 'price', 'status'])
