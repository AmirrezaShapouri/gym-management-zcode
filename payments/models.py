from django.core.validators import MinValueValidator
from django.db import models
import uuid


class Payment(models.Model):
    STATUS_SUCCESS = 'موفق'
    STATUS_PENDING = 'در انتظار'
    STATUS_FAILED = 'ناموفق'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'موفق'),
        (STATUS_PENDING, 'در انتظار'),
        (STATUS_FAILED, 'ناموفق'),
    ]

    METHOD_CARD = 'کارتخوان'
    METHOD_TRANSFER = 'کارت به کارت'
    METHOD_CASH = 'نقدی'
    METHOD_ONLINE = 'درگاه آنلاین'
    METHOD_CHOICES = [
        (METHOD_CARD, METHOD_CARD),
        (METHOD_TRANSFER, METHOD_TRANSFER),
        (METHOD_CASH, METHOD_CASH),
        (METHOD_ONLINE, METHOD_ONLINE),
    ]

    member = models.ForeignKey('members.Member', on_delete=models.PROTECT, related_name='payments',
                               verbose_name='عضو')
    subscription = models.ForeignKey('members.Subscription', on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name='payments', verbose_name='اشتراک')
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0,
                                 validators=[MinValueValidator(0)])
    plan_label = models.CharField('نوع پرداخت', max_length=60, blank=True)
    method = models.CharField('روش پرداخت', max_length=30, choices=METHOD_CHOICES,
                              default=METHOD_CARD)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    reference = models.CharField('شماره پیگیری', max_length=60, blank=True, unique=True)
    operator = models.CharField('ثبت‌کننده', max_length=60, blank=True)
    note = models.TextField('یادداشت', blank=True)
    date = models.DateField('تاریخ پرداخت')
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f'{self.member} - {self.amount:,} تومان'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'TRX{uuid.uuid4().hex}'
        if not self.plan_label and self.subscription:
            self.plan_label = self.subscription.plan_sessions_label
        super().save(*args, **kwargs)


class Expense(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE, null=True, blank=True,
                            related_name='expenses', verbose_name='باشگاه')
    CATEGORY_SALARY = 'حقوق و دستمزد'
    CATEGORY_RENT = 'اجاره و قبوض'
    CATEGORY_EQUIPMENT = 'تجهیزات'
    CATEGORY_MAINTENANCE = 'نگهداری'
    CATEGORY_MARKETING = 'بازاریابی'
    CATEGORY_OTHER = 'سایر'
    CATEGORY_CHOICES = [
        (CATEGORY_SALARY, CATEGORY_SALARY),
        (CATEGORY_RENT, CATEGORY_RENT),
        (CATEGORY_EQUIPMENT, CATEGORY_EQUIPMENT),
        (CATEGORY_MAINTENANCE, CATEGORY_MAINTENANCE),
        (CATEGORY_MARKETING, CATEGORY_MARKETING),
        (CATEGORY_OTHER, CATEGORY_OTHER),
    ]

    STATUS_PAID = 'پرداخت‌شده'
    STATUS_PENDING = 'در انتظار پرداخت'
    STATUS_CHOICES = [
        (STATUS_PAID, STATUS_PAID),
        (STATUS_PENDING, STATUS_PENDING),
    ]

    title = models.CharField('شرح هزینه', max_length=200)
    category = models.CharField('دسته‌بندی', max_length=30, choices=CATEGORY_CHOICES)
    vendor = models.CharField('فروشنده / مسئول', max_length=120, blank=True)
    amount = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0,
                                 validators=[MinValueValidator(0)])
    date = models.DateField('تاریخ هزینه')
    status = models.CharField('وضعیت پرداخت', max_length=20, choices=STATUS_CHOICES,
                              default=STATUS_PAID)
    method = models.CharField('روش پرداخت', max_length=30, blank=True)
    reference = models.CharField('شماره فاکتور', max_length=60, blank=True)
    operator = models.CharField('ثبت‌کننده', max_length=60, blank=True)
    note = models.TextField('یادداشت', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'هزینه'
        verbose_name_plural = 'هزینه‌ها'
        ordering = ('-date', '-created_at')

    def __str__(self):
        return f'{self.title} - {self.amount:,} تومان'
