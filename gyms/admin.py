from django.contrib import admin

from .models import GymSettings, GymSubscription


@admin.register(GymSettings)
class GymSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')


@admin.register(GymSubscription)
class GymSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('sessions', 'price', 'start_date', 'end_date', 'status')
