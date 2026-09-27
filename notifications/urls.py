from django.urls import path

from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('settings/', views.notification_settings, name='notification_settings'),
]