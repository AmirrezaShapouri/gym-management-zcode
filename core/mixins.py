"""کنترل دسترسی بر پایه نقش کاربر (مدیر / پذیرش)."""

from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def user_role(user):
    """Return the user's role, defaulting to the least-privileged role."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    profile = getattr(user, 'profile', None)
    return profile.role if profile else 'reception'


def is_manager(user):
    return user_role(user) == 'manager'


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if user_role(request.user) not in roles:
                if not request.user.is_authenticated:
                    return redirect('login')
                raise PermissionDenied('شما اجازهٔ دسترسی به این بخش را ندارید.')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def coach_class_ids(user):
    profile = getattr(user, 'profile', None)
    phone = getattr(profile, 'phone', '').strip()
    if not phone:
        return []

    from classes.models import Coach, GymClass

    coaches = Coach.objects.filter(phone=phone)
    if coaches.count() != 1:
        return []
    return GymClass.objects.filter(coach_id=coaches.values_list('pk', flat=True)[0]).values_list(
        'pk', flat=True
    )


class ManagerRequiredMixin(UserPassesTestMixin):
    """فقط مدیر به این ویو دسترسی دارد."""

    def test_func(self):
        return is_manager(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        raise PermissionDenied('این بخش فقط برای مدیر سیستم قابل دسترسی است.')


def manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_manager(request.user):
            if not request.user.is_authenticated:
                return redirect('login')
            raise PermissionDenied('این بخش فقط برای مدیر سیستم قابل دسترسی است.')
        return view_func(request, *args, **kwargs)

    return wrapper


def portal_user_required(view_func):
    """Allow signed-in staff roles into the app, but keep admins in Django admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if user_role(request.user) == 'admin':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
