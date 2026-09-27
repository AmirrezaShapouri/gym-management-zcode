from django.contrib.admin import AdminSite


class RoleRestrictedAdminSite(AdminSite):
    def has_permission(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        return bool(
            user.is_active
            and user.is_staff
            and profile
            and profile.role == 'admin'
        )