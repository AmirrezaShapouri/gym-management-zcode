from django.contrib.admin.apps import AdminConfig


class RoleRestrictedAdminConfig(AdminConfig):
    default_site = 'accounts.admin_site.RoleRestrictedAdminSite'