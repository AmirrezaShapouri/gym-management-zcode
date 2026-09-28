from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST

from core.mixins import portal_user_required, tenant_required, user_role
from gyms.forms import GymSubscriptionRequestForm
from gyms.models import GymSettings, GymSubscription, GymSubscriptionRequest
from notifications.models import SMSSettings
from .forms import ProfileForm, StaffUserForm
from .models import Profile


class RoleAwareLoginView(LoginView):
	template_name = 'registration/login.html'
	redirect_authenticated_user = True

	def get_success_url(self):
		if user_role(self.request.user) == Profile.ROLE_ADMIN:
			return reverse_lazy('admin:index')
		return super().get_success_url()


@portal_user_required
@tenant_required
@require_http_methods(['GET', 'POST'])
def profile(request):
	GymSubscription.expire_due(request.gym)
	profile, _ = Profile.objects.get_or_create(user=request.user)
	profile_form = ProfileForm(request.POST if request.method == 'POST' and 'save_profile' in request.POST else None,
							   instance=request.user, profile=profile)
	staff_form = StaffUserForm(
		request.POST if request.method == 'POST' and 'create_staff' in request.POST else None,
		gym=request.gym,
	)

	if request.method == 'POST' and 'save_profile' in request.POST and profile_form.is_valid():
		profile_form.save()
		messages.success(request, 'اطلاعات پروفایل ذخیره شد.')
		return redirect('profile')

	if request.method == 'POST' and 'create_staff' in request.POST:
		if user_role(request.user) != Profile.ROLE_MANAGER:
			raise PermissionDenied
		if staff_form.is_valid():
			staff_form.save()
			messages.success(request, 'حساب کاربری ساخته شد.')
			return redirect('profile')

	staff_users = Profile.objects.select_related('user').filter(
		gym=request.gym,
		role__in=(Profile.ROLE_RECEPTION, Profile.ROLE_COACH, Profile.ROLE_MANAGER),
	).order_by('user__username')
	active_subscription = GymSubscription.objects.filter(
		gym=request.gym, status=GymSubscription.STATUS_ACTIVE
	).order_by('-end_date', '-created_at').first()
	pending_request = GymSubscriptionRequest.objects.filter(
		gym=request.gym, status=GymSubscriptionRequest.STATUS_PENDING
	).order_by('-submitted_at').first()
	latest_rejected = GymSubscriptionRequest.objects.filter(
		gym=request.gym, status=GymSubscriptionRequest.STATUS_REJECTED
	).order_by('-submitted_at').first()
	return render(request, 'accounts/profile.html', {
		'profile_form': profile_form,
		'staff_form': staff_form,
		'staff_users': staff_users,
		'profile': profile,
		'can_manage_users': user_role(request.user) == Profile.ROLE_MANAGER,
		'gym_subscription': active_subscription,
		'pending_request': pending_request,
		'latest_rejected': latest_rejected,
		'gym_subscription_request_form': GymSubscriptionRequestForm(),
		'gym_settings': GymSettings.load(request.gym),
		'sms_settings': SMSSettings.load(request.gym),
	})


@portal_user_required
@tenant_required
@require_POST
def renew_gym_subscription(request):
	if user_role(request.user) != Profile.ROLE_MANAGER:
		raise PermissionDenied
	if GymSubscriptionRequest.objects.filter(
		gym=request.gym, status=GymSubscriptionRequest.STATUS_PENDING
	).exists():
		messages.error(request, 'یک درخواست تمدید در انتظار بررسی دارید.')
		return redirect('profile')
	form = GymSubscriptionRequestForm(request.POST, request.FILES, gym=request.gym)
	if not form.is_valid():
		messages.error(request, 'درخواست نامعتبر است؛ پلن و تصویر رسید را بررسی کنید.')
		return redirect('profile')
	with transaction.atomic():
		form.save()
	messages.success(request, 'درخواست تمدید برای بررسی ثبت شد.')
	return redirect('profile')


class RoleAwarePasswordChangeView(PasswordChangeView):
	form_class = PasswordChangeForm
	template_name = 'accounts/password_change.html'
	success_url = reverse_lazy('profile')

	def form_valid(self, form):
		response = super().form_valid(form)
		update_session_auth_hash(self.request, form.user)
		messages.success(self.request, 'گذرواژه با موفقیت تغییر کرد.')
		return response
