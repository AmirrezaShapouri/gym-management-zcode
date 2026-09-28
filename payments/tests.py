from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import ClassPlan, Coach, GymClass
from members.models import Member, Subscription
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

	def test_payment_status_filter_and_search_can_be_combined(self):
		matching = Payment.objects.create(
			member=self.member, amount=1000, status=Payment.STATUS_PENDING, date='2026-09-26',
			reference='FILTER-MATCH',
		)
		Payment.objects.create(
			member=self.member, amount=1000, status=Payment.STATUS_SUCCESS, date='2026-09-26',
			reference='FILTER-OTHER',
		)
		response = self.client.get('/payments/payments/', {'q': 'FILTER', 'status': Payment.STATUS_PENDING})
		self.assertEqual(list(response.context['payments']), [matching])
		self.assertContains(response, 'name="status"')
		self.assertContains(response, f'<option value="{Payment.STATUS_PENDING}" selected>')

	def test_payment_pagination_preserves_search_and_status(self):
		for index in range(26):
			Payment.objects.create(
				member=self.member,
				amount=1000,
				status=Payment.STATUS_PENDING,
				reference=f'BULK-PAGE-{index}',
				date='2026-09-26',
			)
		response = self.client.get('/payments/payments/', {
			'q': 'BULK-PAGE', 'status': Payment.STATUS_PENDING, 'page': '2',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['page_obj'].number, 2)
		self.assertEqual(len(response.context['payments']), 1)
		self.assertContains(response, 'q=BULK-PAGE')
		self.assertContains(response, 'status=%D8%AF%D8%B1+%D8%A7%D9%86%D8%AA%D8%B8%D8%A7%D8%B1')

	def test_expense_pagination_preserves_search_and_category(self):
		manager = User.objects.create_user(username='expense-manager', password='test-password')
		manager.profile.role = 'manager'
		manager.profile.save(update_fields=['role'])
		self.client.force_login(manager)
		for index in range(26):
			Expense.objects.create(
				title=f'Batch rent {index}', category=Expense.CATEGORY_OTHER,
				amount=1000, date='2026-09-26',
			)
		response = self.client.get('/payments/expenses/', {
			'q': 'Batch', 'category': Expense.CATEGORY_OTHER, 'page': '2',
		})
		self.assertEqual(response.context['page_obj'].number, 2)
		self.assertEqual(len(response.context['expenses']), 1)
		self.assertContains(response, 'q=Batch')

	def test_subscription_list_paginates(self):
		manager = User.objects.create_user(username='subscription-manager', password='test-password')
		manager.profile.role = 'manager'
		manager.profile.save(update_fields=['role'])
		coach = Coach.objects.create(full_name='Pagination coach')
		gym_class = GymClass.objects.create(
			name='Pagination class', coach=coach, start_time='10:00', capacity=40,
		)
		plan = ClassPlan.objects.create(gym_class=gym_class, sessions=12, price=250000)
		for index in range(26):
			member = Member.objects.create(
				first_name='Page', last_name=str(index), phone=f'0912555{index:04d}',
			)
			Subscription.objects.create(member=member, plan=plan, sessions=12)
		self.client.force_login(manager)
		response = self.client.get('/payments/subscriptions/?page=2')
		self.assertEqual(response.context['page_obj'].number, 2)
		self.assertEqual(len(response.context['subscriptions']), 1)
