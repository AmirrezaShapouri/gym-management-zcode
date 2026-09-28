"""زمینه مشترک همه قالب‌ها: اطلاعات باشگاه."""

from gyms.models import GymSettings


def gym_context(request):
    try:
        gym = GymSettings.load()
    except Exception:
        # قبل از اجرای migrate جدول هنوز وجود ندارد
        gym = None
    return {'gym': gym}
