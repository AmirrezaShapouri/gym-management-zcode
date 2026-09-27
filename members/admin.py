from django.contrib import admin

from .models import Member, Subscription


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'gender', 'gym_class', 'coach')
    list_filter = ('gender', 'gym_class')
    search_fields = ('first_name', 'last_name', 'phone')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('member', 'plan', 'sessions', 'remaining_sessions', 'price', 'start_date',
                    'end_date', 'status')
    list_filter = ('status',)
    search_fields = ('member__first_name', 'member__last_name')
