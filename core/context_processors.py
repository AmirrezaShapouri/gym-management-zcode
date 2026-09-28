"""زمینه مشترک همه قالب‌ها: اطلاعات باشگاه."""

from gyms.models import GymSettings


def gym_context(request):
    profile = getattr(request.user, 'profile', None) if request.user.is_authenticated else None
    tenant = profile.gym if profile else None
    if not tenant:
        return {'gym': None}
    try:
        gym = GymSettings.load(tenant)
    except Exception:
        # قبل از اجرای migrate جدول هنوز وجود ندارد
        gym = None
    return {'gym': gym}
