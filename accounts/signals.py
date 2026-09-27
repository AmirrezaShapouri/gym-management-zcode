from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        role = Profile.ROLE_ADMIN if instance.is_superuser else Profile.ROLE_RECEPTION
        Profile.objects.create(user=instance, role=role)
