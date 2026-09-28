from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.mixins import coach_class_ids, role_required, user_role
from classes.models import GymClass
from members.models import Member
from .models import Attendance


class AttendanceSelectionForm(forms.Form):
	gym_class = forms.ModelChoiceField(
		label='کلاس',
		queryset=GymClass.objects.none(),
		widget=forms.Select(attrs={'class': 'form-select'}),
	)
	date = forms.DateField(
		label='تاریخ',
		widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
	)

	def __init__(self, *args, class_ids=None, **kwargs):
		super().__init__(*args, **kwargs)
		classes = GymClass.objects.filter(is_active=True)
		if class_ids is not None:
			classes = classes.filter(pk__in=class_ids)
		self.fields['gym_class'].queryset = classes.order_by('name')
		self.fields['date'].input_formats = ['%Y-%m-%d']


@role_required('manager', 'reception', 'coach')
@require_http_methods(['GET', 'POST'])
def attendance(request):
	class_ids = coach_class_ids(request.user) if user_role(request.user) == 'coach' else None
	form = AttendanceSelectionForm(request.POST or request.GET or None, class_ids=class_ids, initial={
		'date': timezone.localdate(),
	})
	members = Member.objects.none()
	existing = {}
	if request.method == 'POST' and form.is_valid():
		gym_class = form.cleaned_data['gym_class']
		attendance_date = form.cleaned_data['date']
		members = Member.objects.filter(gym_class=gym_class).select_related('coach').prefetch_related(
			'subscriptions__plan'
		).order_by('last_name', 'first_name')
		valid_statuses = {value for value, _ in Attendance.STATUS_CHOICES}
		try:
			with transaction.atomic():
				for member in members:
					status = request.POST.get(f'status_{member.pk}')
					if status not in valid_statuses:
						continue
					Attendance.objects.update_or_create(
						member=member,
						gym_class=gym_class,
						date=attendance_date,
						defaults={'status': status, 'recorded_by': request.user},
					)
		except ValidationError as error:
			form.add_error(None, error)
		else:
			messages.success(request, 'حضور و غیاب ثبت شد.')
		existing = {
			row.member_id: row.status
			for row in Attendance.objects.filter(gym_class=gym_class, date=attendance_date)
		}
	elif request.method == 'GET' and form.is_valid():
		gym_class = form.cleaned_data['gym_class']
		attendance_date = form.cleaned_data['date']
		members = Member.objects.filter(gym_class=gym_class).select_related('coach').prefetch_related(
			'subscriptions__plan'
		).order_by('last_name', 'first_name')
		existing = {
			row.member_id: row.status
			for row in Attendance.objects.filter(gym_class=gym_class, date=attendance_date)
		}
	member_rows = [
		{'member': member, 'status': existing.get(member.pk, '')}
		for member in members
	]
	return render(request, 'attendance/attendance.html', {
		'form': form,
		'member_rows': member_rows,
		'statuses': Attendance.STATUS_CHOICES,
	})


@role_required('manager', 'reception', 'coach')
def attendance_history(request):
	records = Attendance.objects.select_related('member', 'gym_class').prefetch_related(
		'member__subscriptions__plan'
	)
	if user_role(request.user) == 'coach':
		records = records.filter(gym_class_id__in=coach_class_ids(request.user))
	query = request.GET.get('q', '').strip()
	if query:
		records = records.filter(member__first_name__icontains=query) | records.filter(
			member__last_name__icontains=query
		)
	from_date = request.GET.get('from', '')
	to_date = request.GET.get('to', '')
	if from_date:
		records = records.filter(date__gte=from_date)
	if to_date:
		records = records.filter(date__lte=to_date)
	page_obj = Paginator(records, 25).get_page(request.GET.get('page'))
	return render(request, 'attendance/attendance_history.html', {
		'records': page_obj,
		'page_obj': page_obj,
		'query': query,
		'from_date': from_date,
		'to_date': to_date,
	})
