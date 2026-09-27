from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.mixins import portal_user_required
from .forms import ClassPlanFormSet, GymClassForm
from .models import GymClass


@portal_user_required
def class_list(request):
	classes = GymClass.objects.select_related('coach').prefetch_related('plans')
	day = request.GET.get('day', '')
	if day:
		classes = [gym_class for gym_class in classes if day in gym_class.days_list]
	return render(request, 'classes/class_list.html', {
		'classes': classes,
		'selected_day': day,
		'weekdays': GymClass.WEEKDAY_CHOICES,
	})


@portal_user_required
@require_http_methods(['GET', 'POST'])
def class_create(request):
	form = GymClassForm(request.POST or None)
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


@portal_user_required
def class_detail(request, pk):
	gym_class = get_object_or_404(
		GymClass.objects.select_related('coach').prefetch_related(
			'plans', 'members__subscriptions__plan', 'attendances__member'
		),
		pk=pk,
	)
	return render(request, 'classes/class_detail.html', {'gym_class': gym_class})


@portal_user_required
@require_http_methods(['GET', 'POST'])
def class_update(request, pk):
	gym_class = get_object_or_404(GymClass, pk=pk)
	form = GymClassForm(request.POST or None, instance=gym_class)
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


@portal_user_required
@require_http_methods(['GET', 'POST'])
def class_delete(request, pk):
	gym_class = get_object_or_404(GymClass, pk=pk)
	if request.method == 'POST':
		gym_class.delete()
		messages.success(request, 'کلاس حذف شد.')
		return redirect('class_list')
	return render(request, 'classes/class_confirm_delete.html', {'gym_class': gym_class})
