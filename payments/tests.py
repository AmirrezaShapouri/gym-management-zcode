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
		manager = User.objects.create_user(username='finance-manager', password='test-password')
		manager.profile.role = 'manager'
		manager.profile.save(update_fields=['role'])
		self.client.force_login(manager)
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
		self.assertEqual(Expense.objects.get(title='هزینه آزمایشی').operator, 'finance-manager')

	def test_generated_payment_references_are_unique(self):
		first = Payment.objects.create(member=self.member, amount=1000, date='2026-09-26')
		second = Payment.objects.create(member=self.member, amount=1000, date='2026-09-26')
		self.assertNotEqual(first.reference, second.reference)
		self.assertTrue(first.reference.startswith('TRX'))

	def test_reception_cannot_delete_payment_or_manage_expenses(self):
		payment = Payment.objects.create(member=self.member, amount=1000, date='2026-09-26')
		self.assertEqual(self.client.post(f'/payments/payments/{payment.pk}/delete/').status_code, 403)
		self.assertEqual(self.client.get('/payments/expenses/').status_code, 403)
		response = self.client.get('/payments/payments/')
		self.assertNotContains(response, f'/payments/payments/{payment.pk}/delete/')
		coach = User.objects.create_user(username='coach-finance', password='test-password')
		coach.profile.role = 'coach'
		coach.profile.save(update_fields=['role'])
		self.client.force_login(coach)
		self.assertEqual(self.client.post(f'/payments/payments/{payment.pk}/delete/').status_code, 403)
		self.assertEqual(self.client.post('/payments/expenses/1/delete/').status_code, 403)
		self.client.force_login(User.objects.get(username='cashier'))
		delete_member_response = self.client.post(f'/members/{self.member.pk}/delete/')
		self.assertRedirects(delete_member_response, f'/members/{self.member.pk}/')
		self.assertTrue(Payment.objects.filter(pk=payment.pk).exists())
