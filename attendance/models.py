from django.core.exceptions import ValidationError
from django.db import models

from classes.models import GymClass
from members.models import Member


class Attendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_EXCUSED = 'excused'
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'حاضر'),
        (STATUS_ABSENT, 'غایب'),
        (STATUS_EXCUSED, 'غیبت موجه'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances',
                               verbose_name='عضو')
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name='attendances',
                                  verbose_name='کلاس')
    date = models.DateField('تاریخ')
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='attendances_recorded', verbose_name='ثبت‌کننده')
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)

    class Meta:
        verbose_name = 'حضور و غیاب'
        verbose_name_plural = 'حضور و غیاب'
        unique_together = ('member', 'gym_class', 'date')
        ordering = ('-date',)

    def __str__(self):
        return f'{self.member} - {self.gym_class} - {self.date}'

    def clean(self):
        if self.member_id and self.gym_class_id and self.member.gym_class_id != self.gym_class_id:
            raise ValidationError('این عضو در این کلاس ثبت‌نام نکرده است.')
