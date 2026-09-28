from django.contrib import admin

from .models import GymSettings, GymSubscription


@admin.register(GymSettings)
class GymSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')

    def has_add_permission(self, request):
        return not GymSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GymSubscription)
class GymSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('sessions', 'price', 'start_date', 'end_date', 'status')
