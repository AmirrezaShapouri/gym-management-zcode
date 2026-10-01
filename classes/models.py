from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core import jalali


class Coach(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='coaches', verbose_name='باشگاه')
    full_name = models.CharField('نام و نام خانوادگی', max_length=120)
    phone = models.CharField('شماره موبایل', max_length=20, blank=True)

    class Meta:
        verbose_name = 'مربی'
        verbose_name_plural = 'مربی‌ها'

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.gym_id:
            from gyms.models import get_default_gym
            self.gym = get_default_gym()
        return super().save(*args, **kwargs)


class GymClass(models.Model):
    gym = models.ForeignKey('gyms.Gym', on_delete=models.CASCADE,
                            related_name='classes', verbose_name='باشگاه')
    WEEKDAY_CHOICES = [(key, label) for key, label in jalali.WEEKDAY_KEYS]

    name = models.CharField('نام کلاس', max_length=120)
    coach = models.ForeignKey(Coach, on_delete=models.PROTECT, related_name='classes', verbose_name='مربی')
    days = models.CharField('روزهای برگزاری', max_length=120, blank=True,
                            help_text='کلیدهای روز جدا شده با فاصله، مثل: saturday monday')
    start_time = models.TimeField('ساعت شروع')
    end_time = models.TimeField('ساعت پایان', null=True, blank=True)
    capacity = models.PositiveIntegerField('ظرفیت', validators=[MinValueValidator(1)])
    is_active = models.BooleanField('فعال', default=True)
    description = models.TextField('توضیحات', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'کلاس'
        verbose_name_plural = 'کلاس‌ها'

    def __str__(self):
        return self.name

    def clean(self):
        if self.gym_id and self.coach_id and self.coach.gym_id != self.gym_id:
            raise ValidationError({'coach': 'مربی باید متعلق به همین باشگاه باشد.'})

    def save(self, *args, **kwargs):
        if not self.gym_id and self.coach_id:
            self.gym_id = self.coach.gym_id
        if not self.gym_id:
            from gyms.models import get_default_gym
            self.gym = get_default_gym()
        self.clean()
        super().save(*args, **kwargs)

    @property
    def days_list(self):
        return self.days.split() if self.days else []

    @property
    def days_label(self):
        return '، '.join(jalali.weekday_label(day) for day in self.days_list)

    @property
    def enrolled_count(self):
        return getattr(self, '_member_count', None) if hasattr(self, '_member_count') else self.members.count()

    @property
    def remaining_capacity(self):
        return max(self.capacity - self.enrolled_count, 0)


class ClassPlan(models.Model):
    SESSION_CHOICES = [(12, '۱۲ جلسه'), (36, '۳۶ جلسه'), (120, '۱۲۰ جلسه')]

    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, related_name='plans',
                                  verbose_name='کلاس')
    sessions = models.PositiveIntegerField('تعداد جلسات', choices=SESSION_CHOICES)
    price = models.DecimalField('قیمت (تومان)', max_digits=12, decimal_places=0,
                                validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'پلن کلاس'
        verbose_name_plural = 'پلن‌های کلاس'
        unique_together = ('gym_class', 'sessions')

    def __str__(self):
        return f'{self.gym_class} - {self.get_sessions_display()}'
