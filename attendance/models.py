from django.core.exceptions import ValidationError
from django.db import models, transaction

from classes.models import GymClass
from members.models import Member, Subscription


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_EXCUSED = 'excused'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'حاضر'),
        (STATUS_ABSENT, 'غایب'),
        (STATUS_EXCUSED, 'غیبت موجه'),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='attendances',
                               verbose_name='عضو')
    gym_class = models.ForeignKey(GymClass, on_delete=models.PROTECT, related_name='attendances',
                                  verbose_name='کلاس')
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT, null=True, blank=True,
        related_name='attendances', verbose_name='اشتراک مصرف‌شده',
    )
    date = models.DateField('تاریخ')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='attendances_recorded', verbose_name='ثبت‌کننده')
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب'
        constraints = [
            models.UniqueConstraint(
                fields=('member', 'gym_class', 'date'),
                name='unique_member_class_attendance_date',
            ),
        ]
        ordering = ('-date',)

    def __str__(self):
        return f'{self.member} - {self.gym_class} - {self.date}'

    def clean(self):
        if self.status and self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError({'status': 'وضعیت حضور و غیاب نامعتبر است.'})
        if self.member_id and self.gym_class_id and self.member.gym_class_id != self.gym_class_id:
            raise ValidationError('این عضو در این کلاس ثبت‌نام نکرده است.')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            counted_statuses = {self.STATUS_PRESENT, self.STATUS_ABSENT}
            active_subscription = None
            if self.status in counted_statuses and self.member_id:
                active_subscription = Subscription.objects.select_for_update().filter(
                    member_id=self.member_id,
                    status=Subscription.STATUS_ACTIVE,
                ).order_by('-start_date', '-pk').first()
            previous = None
            if self.pk:
                previous = Attendance.objects.select_for_update().filter(pk=self.pk).first()
            self.clean()

            was_counted = previous is not None and previous.status in counted_statuses
            is_counted = self.status in counted_statuses

            if was_counted and not is_counted and previous.subscription_id:
                subscription = Subscription.objects.select_for_update().get(
                    pk=previous.subscription_id
                )
                subscription.remaining_sessions = min(
                    subscription.sessions, subscription.remaining_sessions + 1
                )
                subscription.save(update_fields=['remaining_sessions'])
                self.subscription_id = subscription.pk
            elif is_counted and not was_counted:
                subscription = None
                if previous and previous.subscription_id:
                    subscription = Subscription.objects.select_for_update().get(
                        pk=previous.subscription_id
                    )
                else:
                    subscription = active_subscription
                if subscription is None:
                    raise ValidationError('عضو اشتراک فعال ندارد.')
                if subscription.remaining_sessions < 1:
                    raise ValidationError('جلسهٔ باقی‌مانده‌ای برای این اشتراک وجود ندارد.')
                subscription.remaining_sessions -= 1
                subscription.save(update_fields=['remaining_sessions'])
                self.subscription_id = subscription.pk

            return super().save(*args, **kwargs)
