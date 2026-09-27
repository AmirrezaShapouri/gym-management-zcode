from django.contrib import admin

from .models import ClassPlan, Coach, GymClass


class ClassPlanInline(admin.TabularInline):
    model = ClassPlan
    extra = 1


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone')
    search_fields = ('full_name',)


@admin.register(GymClass)
class GymClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'coach', 'start_time', 'end_time', 'capacity', 'is_active')
    list_filter = ('is_active', 'coach')
    search_fields = ('name',)
    inlines = [ClassPlanInline]
