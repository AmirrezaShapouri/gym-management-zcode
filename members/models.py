from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from classes.models import ClassPlan, Coach, GymClass
from core import jalali
from core.fields import JalaliDateField


class Member(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE, null=True, blank=True,
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='members', verbose_name='باشگاه')
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

    def clean(self):
        for related in (self.gym_class, self.coach):
            if related and self.gym_id and related.gym_id != self.gym_id:
                raise ValidationError('کلاس و مربی باید متعلق به همین باشگاه باشند.')

    def save(self, *args, **kwargs):
        related_gym_ids = {
            related.gym_id for related in (self.gym_class, self.coach) if related is not None
        }
        if not self.gym_id and len(related_gym_ids) == 1:
            self.gym_id = related_gym_ids.pop()
        self.clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def active_subscription(self):
        subscriptions = self._prefetched_subscriptions()
        if subscriptions is not None:
            return max(
                (item for item in subscriptions if item.status == Subscription.STATUS_ACTIVE),
                key=lambda item: (item.start_date, item.pk),
                default=None,
            )
        return self.subscriptions.filter(status=Subscription.STATUS_ACTIVE).order_by('-start_date').first()

    @property
    def latest_subscription(self):
        subscriptions = self._prefetched_subscriptions()
        if subscriptions is not None:
            return max(subscriptions, key=lambda item: (item.start_date, item.pk), default=None)
        return self.subscriptions.order_by('-start_date', '-pk').first()

    def _prefetched_subscriptions(self):
        return getattr(self, '_prefetched_objects_cache', {}).get('subscriptions')


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
        if self.pk:
            previous = Subscription.objects.filter(pk=self.pk).values(
                'plan_id', 'sessions', 'price'
            ).first()
        else:
            previous = None
        plan_details_changed = previous is None or any(
            getattr(self, field_name) != previous[field_name]
            for field_name in ('plan_id', 'sessions', 'price')
        )
        if plan_details_changed and self.plan_id and self.sessions != self.plan.sessions:
            raise ValidationError({'sessions': 'تعداد جلسات باید با پلن انتخاب‌شده یکسان باشد.'})
        if plan_details_changed and self.plan_id and self.price not in (0, self.plan.price):
            raise ValidationError({'price': 'قیمت باید با قیمت پلن انتخاب‌شده یکسان باشد.'})
        if self.member_id and self.plan_id and self.member.gym_class_id and (
            self.member.gym_class_id != self.plan.gym_class_id
        ):
            raise ValidationError({'plan': 'پلن باید متعلق به کلاس عضو باشد.'})
        if self.member_id and self.plan_id and self.member.gym_id != self.plan.gym_class.gym_id:
            raise ValidationError({'plan': 'پلن باید متعلق به باشگاه عضو باشد.'})
        if self.remaining_sessions < 0:
            raise ValidationError({'remaining_sessions': 'جلسات باقی‌مانده نمی‌تواند منفی باشد.'})
        if self.remaining_sessions > self.sessions:
            raise ValidationError({'remaining_sessions': 'جلسات باقی‌مانده نمی‌تواند از کل جلسات بیشتر باشد.'})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            previous = None
            if self.pk:
                previous = Subscription.objects.select_for_update().filter(pk=self.pk).first()
            if self.plan_id and not self.price:
                self.price = self.plan.price
            if previous is None:
                self.remaining_sessions = self.sessions
            elif self.sessions != previous.sessions:
                consumed_sessions = max(previous.sessions - previous.remaining_sessions, 0)
                self.remaining_sessions = max(self.sessions - consumed_sessions, 0)
            self.clean()
            super().save(*args, **kwargs)

    @property
    def status_label(self):
        return self.get_status_display()

    @property
    def plan_sessions_label(self):
        return jalali.fa_digits(f'{self.sessions} جلسه')
