"""زمینه مشترک همه قالب‌ها: اطلاعات باشگاه."""

from gyms.models import GymSettings


def gym_context(request):
    profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    tenant = profile.gym if profile else None
    if not tenant:
        return {'gym': None}
    gym_settings = GymSettings.objects.filter(gym=tenant).first()
    if not gym_settings:
        return {'gym': None}
    return {'gym': gym_settings}
