from django.db import models
from django.core.exceptions import ValidationError


class SMSMessage(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='sms_messages', verbose_name='باشگاه')
    TYPE_CLASS_REMINDER = 'یادآوری کلاس'
    TYPE_SUBSCRIPTION_EXPIRY = 'انقضای اشتراک'
    TYPE_PAYMENT = 'پرداخت'
    TYPE_REGISTRATION = 'ثبت‌نام'
    TYPE_ANNOUNCEMENT = 'اعلانیه'
    TYPE_CHOICES = [
        (TYPE_CLASS_REMINDER, TYPE_CLASS_REMINDER),
        (TYPE_SUBSCRIPTION_EXPIRY, TYPE_SUBSCRIPTION_EXPIRY),
        (TYPE_PAYMENT, TYPE_PAYMENT),
        (TYPE_REGISTRATION, TYPE_REGISTRATION),
        (TYPE_ANNOUNCEMENT, TYPE_ANNOUNCEMENT),
    ]

    STATUS_SENT = 'ارسال شد'
    STATUS_PENDING = 'در انتظار'
    STATUS_FAILED = 'ناموفق'
    STATUS_CHOICES = [
        (STATUS_SENT, STATUS_SENT),
        (STATUS_PENDING, STATUS_PENDING),
        (STATUS_FAILED, STATUS_FAILED),
    ]

    member = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='sms_messages',
                               verbose_name='عضو')
    message_type = models.CharField('نوع پیام', max_length=30, choices=TYPE_CHOICES)
    body = models.TextField('متن')
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT)
    created_at = models.DateTimeField('تاریخ ارسال', auto_now_add=True)

    class Meta:
        verbose_name = 'پیامک'
        verbose_name_plural = 'پیامک‌ها'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.member or "عضو حذف‌شده"} - {self.message_type}'


class Announcement(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='announcements', verbose_name='باشگاه')
    message_type = models.CharField('نوع پیام', max_length=120)
    body = models.TextField('متن اعلانیه')
    classes = models.ManyToManyField('classes.GymClass', related_name='announcements',
                                     verbose_name='کلاس‌های هدف')
    sent_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='announcements', verbose_name='ثبت‌کننده')

    class Meta:
        verbose_name = 'اعلانیه'
        verbose_name_plural = 'اعلانیه‌ها'
        ordering = ('-sent_at',)

    def __str__(self):
        return f'{self.message_type} - {self.sent_at:%Y/%m/%d}'


class MemberNotificationSetting(models.Model):
    member = models.OneToOneField('members.Member', on_delete=models.CASCADE,
                                  related_name='notification_setting', verbose_name='عضو')
    class_reminder = models.BooleanField('یادآوری کلاس', default=True)
    subscription_expiry = models.BooleanField('انقضای اشتراک', default=True)
    payment = models.BooleanField('پرداخت', default=True)
    registration = models.BooleanField('ثبت‌نام', default=True)

    class Meta:
        verbose_name = 'تنظیمات پیامک عضو'
        verbose_name_plural = 'تنظیمات پیامک اعضا'

    def __str__(self):
        return f'تنظیمات پیامک - {self.member}'


class SMSSettings(models.Model):
    gym = models.OneToOneField('gyms.Gym', on_delete=models.CASCADE,
                               related_name='sms_settings', verbose_name='باشگاه')
    """تنظیمات سراسری پیامک (تک‌نمونه‌ای)."""
    enabled = models.BooleanField('فعال‌سازی ارسال پیامک', default=True)
    expiry_sms = models.BooleanField('پیامک انقضای اشتراک', default=True)
    payment_sms = models.BooleanField('پیامک پرداخت', default=True)
    registration_sms = models.BooleanField('پیامک ثبت‌نام', default=True)
    reminder_sms = models.BooleanField('پیامک یادآوری کلاس', default=True)

    class Meta:
        verbose_name = 'تنظیمات پیامک'
        verbose_name_plural = 'تنظیمات پیامک'

    def __str__(self):
        return 'تنظیمات پیامک'

    @classmethod
    def load(cls, gym):
        return cls.objects.get_or_create(gym=gym)[0]
