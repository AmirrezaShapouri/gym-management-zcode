from django.contrib.auth.models import User
from django.test import TestCase

from members.models import Member
from .models import Expense, Payment


class FinanceWorkflowTests(TestCase):
	def setUp(self):
		user = User.objects.create_user(username='cashier', password='test-password')
		self.client.force_login(user)
		self.member = Member.objects.create(first_name='مینا', last_name='تست', phone='09124444444')

	def test_payment_post_persists_and_assigns_operator(self):
		response = self.client.post('/payments/payments/', {
			'member': self.member.pk,
			'subscription': '',
			'amount': '250000',
			'plan_label': 'پرداخت آزمایشی',
			'method': Payment.METHOD_CASH,
			'status': Payment.STATUS_SUCCESS,
			'reference': 'TEST-2501',
			'date': '2026-09-26',
			'note': '',
		})
		self.assertRedirects(response, '/payments/payments/')
		payment = Payment.objects.get(reference='TEST-2501')
		self.assertEqual(payment.operator, 'cashier')

	def test_expense_post_persists(self):
		response = self.client.post('/payments/expenses/', {
			'title': 'هزینه آزمایشی',
			'category': Expense.CATEGORY_OTHER,
			'vendor': '',
			'amount': '10000',
			'date': '2026-09-26',
			'status': Expense.STATUS_PAID,
			'method': 'نقدی',
			'reference': '',
			'note': '',
		})
		self.assertRedirects(response, '/payments/expenses/')
		self.assertEqual(Expense.objects.get(title='هزینه آزمایشی').operator, 'cashier')
