from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import Gym, GymSettings, GymSubscription, GymSubscriptionRequest


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GymSettings)
class GymSettingsAdmin(admin.ModelAdmin):
    list_display = ('gym', 'name', 'phone')

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GymSubscription)
class GymSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('gym', 'sessions', 'price', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'sessions')
    readonly_fields = ('created_at',)


@admin.register(GymSubscriptionRequest)
class GymSubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'gym', 'sessions', 'price', 'submitted_at', 'status', 'invoice_link', 'reviewed_at', 'reviewed_by',
    )
    list_filter = ('status', 'sessions', 'gym')
    search_fields = ('gym__name', 'rejection_reason')
    readonly_fields = ('price', 'submitted_at', 'status', 'reviewed_at', 'reviewed_by', 'invoice_preview')
    fields = (
        'gym', 'sessions', 'price', 'invoice_preview', 'invoice_image', 'status', 'submitted_at',
        'reviewed_at', 'reviewed_by', 'rejection_reason', 'subscription',
    )
    actions = ('approve_requests', 'reject_requests')

    @admin.display(description='رسید')
    def invoice_link(self, obj):
        if not obj.invoice_image:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">مشاهده رسید</a>', obj.invoice_image.url)

    @admin.display(description='پیش‌نمایش رسید')
    def invoice_preview(self, obj):
        if not obj.invoice_image:
            return '-'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener"><img src="{}" alt="رسید" style="max-height:240px;max-width:100%"></a>',
            obj.invoice_image.url,
            obj.invoice_image.url,
        )

    @admin.action(description='تأیید درخواست‌های انتخاب‌شده')
    def approve_requests(self, request, queryset):
        approved = 0
        for subscription in queryset.filter(status=GymSubscription.STATUS_PENDING):
            try:
                subscription.approve(request.user)
            except ValidationError:
                continue
            approved += 1
        self.message_user(request, f'{approved} درخواست تأیید شد.')

    @admin.action(description='رد درخواست‌های انتخاب‌شده (ابتدا دلیل را ثبت کنید)')
    def reject_requests(self, request, queryset):
        rejected = 0
        for subscription in queryset.filter(status=GymSubscription.STATUS_PENDING):
            if not subscription.rejection_reason.strip():
                continue
            try:
                subscription.reject(request.user, subscription.rejection_reason)
            except ValidationError:
                continue
            rejected += 1
        self.message_user(request, f'{rejected} درخواست رد شد؛ برای موارد باقی‌مانده دلیل رد را ثبت کنید.')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
