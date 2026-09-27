from django.contrib import admin

from .models import (Announcement, MemberNotificationSetting, SMSMessage, SMSSettings)


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ('member', 'message_type', 'status', 'created_at')
    list_filter = ('message_type', 'status')
    search_fields = ('member__first_name', 'member__last_name', 'body')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'sent_at', 'created_by')
    filter_horizontal = ('classes',)


@admin.register(MemberNotificationSetting)
class MemberNotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('member', 'class_reminder', 'subscription_expiry', 'payment', 'registration')


@admin.register(SMSSettings)
class SMSSettingsAdmin(admin.ModelAdmin):
    list_display = ('enabled', 'expiry_sms', 'payment_sms', 'registration_sms', 'reminder_sms')
