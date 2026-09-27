from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST

from core.mixins import portal_user_required, user_role
from .forms import ProfileForm, StaffUserForm
from .models import Profile
from gyms.models import GymSubscription


class RoleAwareLoginView(LoginView):
	template_name = 'registration/login.html'
	redirect_authenticated_user = True

	def get_success_url(self):
		if user_role(self.request.user) == Profile.ROLE_ADMIN:
			return reverse_lazy('admin:index')
		return super().get_success_url()


@portal_user_required
@require_http_methods(['GET', 'POST'])
def profile(request):
	profile, _ = Profile.objects.get_or_create(user=request.user)
	profile_form = ProfileForm(request.POST if request.method == 'POST' and 'save_profile' in request.POST else None,
							   instance=request.user, profile=profile)
	staff_form = StaffUserForm(request.POST if request.method == 'POST' and 'create_staff' in request.POST else None)

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
		role__in=(Profile.ROLE_RECEPTION, Profile.ROLE_COACH, Profile.ROLE_MANAGER),
	).order_by('user__username')
	return render(request, 'accounts/profile.html', {
		'profile_form': profile_form,
		'staff_form': staff_form,
		'staff_users': staff_users,
		'profile': profile,
		'can_manage_users': user_role(request.user) == Profile.ROLE_MANAGER,
		'gym_subscription': GymSubscription.objects.order_by('-end_date').first(),
	})


@portal_user_required
@require_POST
def renew_gym_subscription(request):
	if user_role(request.user) != Profile.ROLE_MANAGER:
		raise PermissionDenied
	subscription = GymSubscription.objects.order_by('-end_date').first()
	if subscription is None:
		messages.error(request, 'برای ثبت تمدید، ابتدا اشتراک فعلی باید ثبت شود.')
		return redirect('profile')
	try:
		sessions = int(request.POST.get('sessions', ''))
	except ValueError:
		sessions = None
	prices = {12: 2500000, 36: 6000000, 120: 25000000}
	if sessions not in prices:
		messages.error(request, 'دورهٔ انتخاب‌شده معتبر نیست.')
		return redirect('profile')
	subscription.apply_renewal(sessions, prices[sessions])
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
