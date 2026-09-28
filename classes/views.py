from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.mixins import coach_class_ids, role_required, tenant_required, user_role
from .forms import ClassPlanFormSet, GymClassForm
from .models import GymClass


@tenant_required
@role_required('manager', 'reception', 'coach')
def class_list(request):
	classes = GymClass.objects.filter(gym=request.gym).select_related('coach').prefetch_related('plans').annotate(
		_member_count=Count('members')
	)
	if user_role(request.user) == 'coach':
		classes = classes.filter(pk__in=coach_class_ids(request.user))
	day = request.GET.get('day', '')
	if day in dict(GymClass.WEEKDAY_CHOICES):
		classes = classes.filter(days__contains=day)
	return render(request, 'classes/class_list.html', {
		'classes': classes,
		'selected_day': day,
		'weekdays': GymClass.WEEKDAY_CHOICES,
	})


@tenant_required
@role_required('manager')
@require_http_methods(['GET', 'POST'])
def class_create(request):
	form = GymClassForm(request.POST or None, gym=request.gym)
	plans = ClassPlanFormSet(request.POST or None)
	if request.method == 'POST' and form.is_valid() and plans.is_valid():
		with transaction.atomic():
			gym_class = form.save()
			plans.instance = gym_class
			plans.save()
		messages.success(request, 'کلاس با موفقیت ثبت شد.')
		return redirect('class_detail', pk=gym_class.pk)
	return render(request, 'classes/class_form.html', {
		'form': form,
		'plans': plans,
		'is_create': True,
	})


@tenant_required
@role_required('manager', 'reception', 'coach')
def class_detail(request, pk):
	classes = GymClass.objects.filter(gym=request.gym).select_related('coach').prefetch_related(
		'plans', 'members__subscriptions__plan', 'attendances__member'
	)
	if user_role(request.user) == 'coach':
		classes = classes.filter(pk__in=coach_class_ids(request.user))
	gym_class = get_object_or_404(
		classes,
		pk=pk,
	)
	return render(request, 'classes/class_detail.html', {'gym_class': gym_class})


@tenant_required
@role_required('manager')
@require_http_methods(['GET', 'POST'])
def class_update(request, pk):
	gym_class = get_object_or_404(GymClass, pk=pk, gym=request.gym)
	form = GymClassForm(request.POST or None, instance=gym_class, gym=request.gym)
	plans = ClassPlanFormSet(request.POST or None, instance=gym_class)
	if request.method == 'POST' and form.is_valid() and plans.is_valid():
		with transaction.atomic():
			gym_class = form.save()
			plans.instance = gym_class
			plans.save()
		messages.success(request, 'اطلاعات کلاس به‌روزرسانی شد.')
		return redirect('class_detail', pk=gym_class.pk)
	return render(request, 'classes/class_form.html', {
		'form': form,
		'plans': plans,
		'gym_class': gym_class,
		'is_create': False,
	})


@tenant_required
@role_required('manager')
@require_http_methods(['GET', 'POST'])
def class_delete(request, pk):
	gym_class = get_object_or_404(GymClass, pk=pk, gym=request.gym)
	if request.method == 'POST':
		try:
			gym_class.delete()
		except ProtectedError:
			messages.error(request, 'این کلاس دارای سابقهٔ حضور و غیاب است و قابل حذف نیست.')
			return redirect('class_detail', pk=gym_class.pk)
		messages.success(request, 'کلاس حذف شد.')
		return redirect('class_list')
	return render(request, 'classes/class_confirm_delete.html', {'gym_class': gym_class})
