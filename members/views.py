from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from core.mixins import role_required
from .forms import MemberForm
from .models import Member


@role_required('manager', 'reception')
def member_list(request):
	members = Member.objects.select_related('gym_class', 'coach').prefetch_related(
		'subscriptions__plan'
	).order_by('last_name', 'first_name', 'pk')
	query = request.GET.get('q', '').strip()
	if query:
		members = members.filter(
			Q(first_name__icontains=query)
			| Q(last_name__icontains=query)
			| Q(phone__icontains=query)
		)
	status = request.GET.get('status', '')
	if status in ('active', 'expired', 'pending'):
		members = members.filter(subscriptions__status=status).distinct()
	plan = request.GET.get('plan', '')
	if plan in ('12', '36', '120'):
		members = members.filter(subscriptions__sessions=plan).distinct()
	page_obj = Paginator(members, 25).get_page(request.GET.get('page'))
	return render(request, 'members/member_list.html', {
		'members': page_obj,
		'page_obj': page_obj,
		'query': query,
		'status': status,
		'plan': plan,
	})


@role_required('manager', 'reception')
@require_http_methods(['GET', 'POST'])
def member_create(request):
	form = MemberForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		member = form.save()
		messages.success(request, 'عضو با موفقیت ثبت شد.')
		return redirect('member_detail', pk=member.pk)
	return render(request, 'members/member_form.html', {'form': form, 'is_create': True})


@role_required('manager', 'reception')
def member_detail(request, pk):
	member = get_object_or_404(
		Member.objects.select_related('gym_class', 'coach').prefetch_related(
			'subscriptions__plan', 'attendances__gym_class', 'payments'
		),
		pk=pk,
	)
	return render(request, 'members/member_detail.html', {'member': member})


@role_required('manager', 'reception')
@require_http_methods(['GET', 'POST'])
def member_update(request, pk):
	member = get_object_or_404(Member, pk=pk)
	form = MemberForm(request.POST or None, instance=member)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'اطلاعات عضو به‌روزرسانی شد.')
		return redirect('member_detail', pk=member.pk)
	return render(request, 'members/member_form.html', {
		'form': form,
		'member': member,
		'is_create': False,
	})


@role_required('manager', 'reception')
@require_http_methods(['GET', 'POST'])
def member_delete(request, pk):
	member = get_object_or_404(Member, pk=pk)
	if request.method == 'POST':
		try:
			member.delete()
		except ProtectedError:
			messages.error(request, 'عضو دارای سابقهٔ مالی یا حضور و غیاب است و قابل حذف نیست.')
			return redirect('member_detail', pk=member.pk)
		messages.success(request, 'عضو حذف شد.')
		return redirect('member_list')
	return render(request, 'members/member_confirm_delete.html', {'member': member})
