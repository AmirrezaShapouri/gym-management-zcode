from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from classes.models import ClassPlan, Coach, GymClass
from core import jalali
from core.fields import JalaliDateField


class Member(models.Model):
    first_name = models.CharField('نام', max_length=80)
    last_name = models.CharField('نام خانوادگی', max_length=80)
    phone = models.CharField('شماره موبایل', max_length=20)
    gender = models.CharField('جنسیت', max_length=10, choices=[('male', 'مرد'), ('female', 'زن')],
                              default='male')
    gym_class = models.ForeignKey(GymClass, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='members', verbose_name='کلاس')
    coach = models.ForeignKey(Coach, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='members', verbose_name='مربی')
    created_at = models.DateTimeField('تاریخ ثبت‌نام', auto_now_add=True)

    class Meta:
        verbose_name = 'عضو'
        verbose_name_plural = 'اعضا'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def active_subscription(self):
        return self.subscriptions.filter(status=Subscription.STATUS_ACTIVE).order_by('-start_date').first()

    @property
    def latest_subscription(self):
        return self.subscriptions.order_by('-start_date').first()


class Subscription(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_PENDING = 'pending'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'فعال'),
        (STATUS_EXPIRED, 'منقضی'),
        (STATUS_PENDING, 'در انتظار'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='subscriptions',
                               verbose_name='عضو')
    plan = models.ForeignKey(ClassPlan, on_delete=models.PROTECT, related_name='subscriptions',
                             verbose_name='پلن')
    sessions = models.PositiveIntegerField('تعداد جلسات', default=12,
                                           validators=[MinValueValidator(1)])
    remaining_sessions = models.PositiveIntegerField('جلسات باقی‌مانده', default=0)
    price = models.DecimalField('مبلغ (تومان)', max_digits=12, decimal_places=0, default=0)
    start_date = models.DateField('تاریخ شروع', default=timezone.localdate)
    end_date = models.DateField('تاریخ پایان', null=True, blank=True)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta:
        verbose_name = 'اشتراک'
        verbose_name_plural = 'اشتراک‌ها'
        ordering = ('-start_date',)

    def __str__(self):
        return f'{self.member} - {self.plan}'

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.')

    def save(self, *args, **kwargs):
        if not self.pk and self.sessions:
            self.remaining_sessions = self.sessions
        if not self.price and self.plan:
            self.price = self.plan.price
        super().save(*args, **kwargs)

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def plan_sessions_label(self):
        return jalali.fa_digits(f'{self.sessions} جلسه')
