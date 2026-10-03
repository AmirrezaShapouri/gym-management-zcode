from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_RECEPTION = 'reception'
    ROLE_COACH = 'coach'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'ادمین'),
        (ROLE_MANAGER, 'مدیر'),
        (ROLE_RECEPTION, 'پذیرش'),
        (ROLE_COACH, 'مربی'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile',
                                verbose_name='کاربر')
    gym = models.ForeignKey('gyms.Gym', on_delete=models.PROTECT, null=True, blank=True,
                            related_name='profiles', verbose_name='باشگاه')
    role = models.CharField('نقش', max_length=20, choices=ROLE_CHOICES, default=ROLE_RECEPTION)
    phone = models.CharField('شماره همراه', max_length=20, blank=True)

    class Meta:
        verbose_name = 'نقش کاربر'
        verbose_name_plural = 'نقش کاربران'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    @property
    def is_active_user(self):
        return self.user.is_active
