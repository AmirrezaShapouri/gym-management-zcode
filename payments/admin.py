from django.contrib import admin

from .models import Expense, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'plan_label', 'method', 'status', 'reference', 'date')
    list_filter = ('status', 'method')
    search_fields = ('member__first_name', 'member__last_name', 'reference')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'vendor', 'amount', 'date', 'status')
    list_filter = ('category', 'status')
    search_fields = ('title', 'vendor')
