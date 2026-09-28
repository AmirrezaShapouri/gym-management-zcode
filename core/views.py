from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import timedelta

from attendance.models import Attendance
from classes.models import GymClass
from core.mixins import role_required
from members.models import Member, Subscription
from payments.models import Expense, Payment


def home(request):
	if request.user.is_authenticated:
		if request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', None) == 'admin':
			return redirect('admin:index')
		return redirect('dashboard')
	return render(request, 'index.html')


@login_required
@role_required('manager', 'reception')
def dashboard(request):
	today = timezone.localdate()
	month_start = today.replace(day=1)
	payments = Payment.objects.filter(date__gte=month_start, date__lte=today)
	expenses = Expense.objects.filter(date__gte=month_start, date__lte=today)
	attendance_today = Attendance.objects.filter(date=today)
	context = {
		'member_count': Member.objects.count(),
		'active_subscription_count': Subscription.objects.filter(
			status=Subscription.STATUS_ACTIVE,
		).count(),
		'expired_subscription_count': Subscription.objects.filter(
			status=Subscription.STATUS_EXPIRED,
		).count(),
		'class_count': GymClass.objects.filter(is_active=True).count(),
		'attendance_count': attendance_today.filter(status=Attendance.STATUS_PRESENT).count(),
		'absence_count': attendance_today.filter(status=Attendance.STATUS_ABSENT).count(),
		'monthly_income': payments.filter(status=Payment.STATUS_SUCCESS).aggregate(total=Sum('amount'))['total'] or 0,
		'monthly_expenses': expenses.filter(status=Expense.STATUS_PAID).aggregate(total=Sum('amount'))['total'] or 0,
		'monthly_profit': (
			(payments.filter(status=Payment.STATUS_SUCCESS).aggregate(total=Sum('amount'))['total'] or 0)
			- (expenses.filter(status=Expense.STATUS_PAID).aggregate(total=Sum('amount'))['total'] or 0)
		),
		'recent_payments': Payment.objects.select_related('member').all()[:8],
		'recent_members': Member.objects.order_by('-created_at')[:5],
		'active_classes': GymClass.objects.filter(is_active=True).select_related('coach')[:8],
		'expiring_subscriptions': Subscription.objects.filter(
			status=Subscription.STATUS_ACTIVE,
			end_date__range=(today, today + timedelta(days=7)),
		).select_related('member', 'plan')[:8],
		'today': today,
	}
	return render(request, 'dashboard.html', context)
