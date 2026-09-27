from django.urls import path

from . import views

urlpatterns = [
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/new/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
]