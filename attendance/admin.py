from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('member', 'gym_class', 'date', 'status', 'recorded_by')
    list_filter = ('status', 'gym_class', 'date')
    search_fields = ('member__first_name', 'member__last_name')
