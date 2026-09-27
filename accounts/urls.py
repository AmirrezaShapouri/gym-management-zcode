from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import RoleAwareLoginView, RoleAwarePasswordChangeView, profile, renew_gym_subscription

urlpatterns = [
    path('login/', RoleAwareLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', profile, name='profile'),
    path('password/', RoleAwarePasswordChangeView.as_view(), name='password_change'),
    path('subscription/renew/', renew_gym_subscription, name='gym_subscription_renew'),
]