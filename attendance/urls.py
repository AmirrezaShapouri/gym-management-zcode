from django.urls import path

from . import views

urlpatterns = [
    path('', views.attendance, name='attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
]