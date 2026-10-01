from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


def validate_invoice_image(file):
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    if Path(file.name).suffix.lower() not in allowed_extensions:
        raise ValidationError('فقط فایل‌های JPG، PNG یا WebP مجاز هستند.')
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('حجم تصویر رسید نباید بیشتر از ۵ مگابایت باشد.')


def get_default_gym():
    from .models import Gym
    gym = Gym.objects.order_by('pk').first()
    if gym is None:
        gym = Gym.objects.create(name='Default Gym', slug='default-gym')
    return gym


class GymSettings(models.Model):
    """تنظیمات باشگاه (تک‌نمونه‌ای)."""
    gym = models.OneToOneField('gyms.Gym', on_delete=models.CASCADE,
                               related_name='settings', verbose_name='باشگاه')
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
        if not self.gym_id:
            self.gym = get_default_gym()
        if self.pk is None and GymSettings.objects.filter(gym=self.gym).exists():
            raise ValidationError({'gym': 'برای این باشگاه قبلاً تنظیمات ثبت شده است.'})
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls, gym=None):
        if gym is None:
            gym = get_default_gym()
        return cls.objects.get_or_create(gym=gym, defaults={'name': gym.name})[0]


class Gym(models.Model):
    name = models.CharField('نام باشگاه', max_length=120)
    slug = models.SlugField('شناسه', max_length=150, unique=True)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'باشگاه'
        verbose_name_plural = 'باشگاه‌ها'
        ordering = ('name',)

    def __str__(self):
        return self.name


class GymSubscription(models.Model):
    """An active or expired SaaS entitlement for one gym."""
    SESSION_CHOICES = [(12, '۱۲ جلسه'), (36, '۳۶ جلسه'), (120, '۱۲۰ جلسه')]
    STATUS_ACTIVE = 'فعال'
    STATUS_EXPIRED = 'منقضی'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, STATUS_ACTIVE),
        (STATUS_EXPIRED, STATUS_EXPIRED),
    ]
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='subscriptions', verbose_name='باشگاه')
    PLAN_PRICES = {12: 2500000, 36: 6000000, 120: 25000000}
    PLAN_DURATIONS = {12: 30, 36: 90, 120: 365}

    sessions = models.PositiveIntegerField('دوره', choices=SESSION_CHOICES, default=12)
    price = models.DecimalField('مبلغ دوره (تومان)', max_digits=12, decimal_places=0, default=2500000,
                                validators=[MinValueValidator(0)])
    start_date = models.DateField('تاریخ شروع', null=True, blank=True)
    end_date = models.DateField('تاریخ پایان', null=True, blank=True)
    status = models.CharField('وضعیت', max_length=30, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField('تاریخ ایجاد', default=timezone.now, editable=False)

    class Meta:
        verbose_name = 'اشتراک باشگاه'
        verbose_name_plural = 'اشتراک‌های باشگاه'
        ordering = ('-end_date', '-pk')

    def __str__(self):
        return f'{self.gym} - {self.get_sessions_display()} - {self.end_date}'

    def save(self, *args, **kwargs):
        if not self.gym_id:
            self.gym = get_default_gym()
        return super().save(*args, **kwargs)

    @classmethod
    def expire_due(cls, gym=None):
        subscriptions = cls.objects.filter(
            status=cls.STATUS_ACTIVE,
            end_date__lt=timezone.localdate(),
        )
        if gym is not None:
            subscriptions = subscriptions.filter(gym=gym)
        return subscriptions.update(status=cls.STATUS_EXPIRED)



class GymSubscriptionRequest(models.Model):
    STATUS_PENDING = 'در انتظار بررسی'
    STATUS_APPROVED = 'تأیید شده'
    STATUS_REJECTED = 'رد شده'
    STATUS_CHOICES = [
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_APPROVED, STATUS_APPROVED),
        (STATUS_REJECTED, STATUS_REJECTED),
    ]

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE,
                            related_name='subscription_requests', verbose_name='باشگاه')
    sessions = models.PositiveIntegerField('دوره', choices=GymSubscription.SESSION_CHOICES)
    price = models.DecimalField('مبلغ دوره (تومان)', max_digits=12, decimal_places=0,
                                validators=[MinValueValidator(0)])
    invoice_image = models.ImageField(
        'تصویر رسید پرداخت', upload_to='gym_subscriptions/invoices/', blank=True,
        validators=[validate_invoice_image],
    )
    status = models.CharField('وضعیت', max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField('تاریخ درخواست', default=timezone.now, editable=False)
    reviewed_at = models.DateTimeField('تاریخ بررسی', null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gym_subscription_reviews', verbose_name='بررسی‌کننده',
    )
    rejection_reason = models.TextField('دلیل رد', blank=True)
    subscription = models.ForeignKey(
        GymSubscription, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='requests', verbose_name='اشتراک ایجادشده',
    )

    class Meta:
        verbose_name = 'درخواست اشتراک SaaS'
        verbose_name_plural = 'درخواست‌های اشتراک SaaS'
        ordering = ('-submitted_at', '-pk')
        constraints = [
            models.UniqueConstraint(
                fields=('gym',),
                condition=Q(status='در انتظار بررسی'),
                name='one_pending_subscription_request_per_gym',
            ),
        ]

    def __str__(self):
        return f'{self.gym} - {self.get_sessions_display()} - {self.get_status_display()}'

    def clean(self):
        if self.sessions not in GymSubscription.PLAN_PRICES:
            raise ValidationError({'sessions': 'پلن انتخاب‌شده معتبر نیست.'})
        if self.price is not None and self.price != GymSubscription.PLAN_PRICES[self.sessions]:
            raise ValidationError({'price': 'مبلغ پلن معتبر نیست.'})
        if self.subscription_id and self.subscription.gym_id != self.gym_id:
            raise ValidationError({'subscription': 'اشتراک باید متعلق به همین باشگاه باشد.'})

    def save(self, *args, **kwargs):
        if not self.gym_id:
            self.gym = get_default_gym()
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self, reviewer):
        with transaction.atomic():
            request = type(self).objects.select_for_update().get(pk=self.pk)
            if request.status != self.STATUS_PENDING:
                raise ValidationError('فقط درخواست‌های در انتظار بررسی قابل تأیید هستند.')
            if not request.invoice_image:
                raise ValidationError('پیش از تأیید باید تصویر رسید ثبت شده باشد.')
            GymSubscription.expire_due(request.gym)
            latest_active_end = GymSubscription.objects.filter(
                gym=request.gym,
                status=GymSubscription.STATUS_ACTIVE,
            ).order_by('-end_date').values_list('end_date', flat=True).first()
            today = timezone.localdate()
            start_date = max(today, latest_active_end + timedelta(days=1)) if latest_active_end else today
            subscription = GymSubscription.objects.create(
                gym=request.gym,
                sessions=request.sessions,
                price=request.price,
                start_date=start_date,
                end_date=start_date + timedelta(days=GymSubscription.PLAN_DURATIONS[request.sessions] - 1),
                status=GymSubscription.STATUS_ACTIVE,
            )
            request.status = self.STATUS_APPROVED
            request.reviewed_at = timezone.now()
            request.reviewed_by = reviewer
            request.subscription = subscription
            request.rejection_reason = ''
            request.save(update_fields=('status', 'reviewed_at', 'reviewed_by', 'subscription', 'rejection_reason'))
            self.refresh_from_db()
            return subscription

    def reject(self, reviewer, reason):
        if not reason.strip():
            raise ValidationError({'rejection_reason': 'برای رد درخواست، ذکر دلیل الزامی است.'})
        with transaction.atomic():
            request = type(self).objects.select_for_update().get(pk=self.pk)
            if request.status != self.STATUS_PENDING:
                raise ValidationError('فقط درخواست‌های در انتظار بررسی قابل رد هستند.')
            request.status = self.STATUS_REJECTED
            request.reviewed_at = timezone.now()
            request.reviewed_by = reviewer
            request.rejection_reason = reason.strip()
            request.save(update_fields=('status', 'reviewed_at', 'reviewed_by', 'rejection_reason'))
            self.refresh_from_db()
