from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.mixins import role_required
from members.models import Subscription
from .forms import ExpenseForm, PaymentForm, SubscriptionForm
from .models import Expense, Payment


@role_required('manager', 'reception')
def payment_list(request):
	payments = Payment.objects.select_related('member', 'subscription').all()
	query = request.GET.get('q', '').strip()
	status = request.GET.get('status', '')
	if query:
		payments = payments.filter(
			Q(member__first_name__icontains=query)
			| Q(member__last_name__icontains=query)
			| Q(reference__icontains=query)
		)
	if status in dict(Payment.STATUS_CHOICES):
		payments = payments.filter(status=status)
	form = PaymentForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		payment = form.save(commit=False)
		payment.operator = request.user.get_username()
		payment.save()
		messages.success(request, 'پرداخت ثبت شد.')
		return redirect('payment_list')
	today = timezone.localdate()
	monthly = Payment.objects.filter(date__year=today.year, date__month=today.month)
	return render(request, 'payments/payment_list.html', {
		'payments': payments,
		'query': query,
		'status': status,
		'form': form,
		'success_count': payments.filter(status=Payment.STATUS_SUCCESS).count(),
		'pending_count': payments.filter(status=Payment.STATUS_PENDING).count(),
		'failed_count': payments.filter(status=Payment.STATUS_FAILED).count(),
		'monthly_income': monthly.filter(status=Payment.STATUS_SUCCESS).aggregate(total=Sum('amount'))['total'] or 0,
	})


@role_required('manager', 'reception')
def payment_detail(request, pk):
	payment = get_object_or_404(
		Payment.objects.select_related('member', 'subscription__plan'),
		pk=pk,
	)
	return render(request, 'payments/payment_detail.html', {'payment': payment})


@role_required('manager')
@require_POST
def payment_delete(request, pk):
	get_object_or_404(Payment, pk=pk).delete()
	messages.success(request, 'پرداخت حذف شد.')
	return redirect('payment_list')


@role_required('manager')
def subscription_list(request):
	subscriptions = Subscription.objects.select_related('member', 'plan__gym_class').all()
	return render(request, 'payments/subscription_list.html', {'subscriptions': subscriptions})


@role_required('manager')
def subscription_detail(request, pk):
	subscription = get_object_or_404(
		Subscription.objects.select_related('member', 'plan__gym_class').prefetch_related('payments'),
		pk=pk,
	)
	return render(request, 'payments/subscription_detail.html', {'subscription': subscription})


@role_required('manager')
@require_http_methods(['GET', 'POST'])
def subscription_create(request):
	form = SubscriptionForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		subscription = form.save()
		messages.success(request, 'اشتراک ثبت شد.')
		return redirect('subscription_detail', pk=subscription.pk)
	return render(request, 'payments/subscription_form.html', {'form': form})


@role_required('manager')
@require_http_methods(['GET', 'POST'])
def expense_list(request):
	expenses = Expense.objects.all()
	query = request.GET.get('q', '').strip()
	category = request.GET.get('category', '')
	if query:
		expenses = expenses.filter(Q(title__icontains=query) | Q(vendor__icontains=query))
	if category in dict(Expense.CATEGORY_CHOICES):
		expenses = expenses.filter(category=category)
	form = ExpenseForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		expense = form.save(commit=False)
		expense.operator = request.user.get_username()
		expense.save()
		messages.success(request, 'هزینه ثبت شد.')
		return redirect('expense_list')
	today = timezone.localdate()
	month_expenses = Expense.objects.filter(date__year=today.year, date__month=today.month)
	return render(request, 'payments/expense_list.html', {
		'expenses': expenses,
		'form': form,
		'query': query,
		'category': category,
		'category_choices': Expense.CATEGORY_CHOICES,
		'monthly_expenses': month_expenses.aggregate(total=Sum('amount'))['total'] or 0,
		'pending_expenses': month_expenses.filter(status=Expense.STATUS_PENDING).aggregate(total=Sum('amount'))['total'] or 0,
	})


@role_required('manager')
@require_POST
def expense_delete(request, pk):
	get_object_or_404(Expense, pk=pk).delete()
	messages.success(request, 'هزینه حذف شد.')
	return redirect('expense_list')


@role_required('manager')
def finance_dashboard(request):
	today = timezone.localdate()
	month_start = today.replace(day=1)
	payments = Payment.objects.filter(date__gte=month_start, date__lte=today)
	expenses = Expense.objects.filter(date__gte=month_start, date__lte=today)
	income = payments.filter(status=Payment.STATUS_SUCCESS).aggregate(total=Sum('amount'))['total'] or 0
	expense_total = expenses.filter(status=Expense.STATUS_PAID).aggregate(total=Sum('amount'))['total'] or 0
	return render(request, 'payments/finance_dashboard.html', {
		'income': income,
		'expenses': expense_total,
		'profit': income - expense_total,
		'pending_payments': payments.filter(status=Payment.STATUS_PENDING).aggregate(total=Sum('amount'))['total'] or 0,
		'payments': Payment.objects.select_related('member').all()[:10],
	})
