from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import ClassPlan, Coach, GymClass
from gyms.models import Gym
from members.models import Member, Subscription
from .models import Expense, Payment


class FinanceWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Finance Gym', slug='finance-gym')
        user = User.objects.create_user(username='cashier', password='test-password')
        user.profile.role = 'reception'
        user.profile.gym = self.gym
        user.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(user)
        self.member = Member.objects.create(gym=self.gym, first_name='مینا', last_name='تست', phone='09124444444')

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
        manager.profile.gym = self.gym
        manager.profile.save(update_fields=['role', 'gym'])
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
        coach.profile.gym = self.gym
        coach.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(coach)
        self.assertEqual(self.client.post(f'/payments/payments/{payment.pk}/delete/').status_code, 403)
        self.assertEqual(self.client.post('/payments/expenses/1/delete/').status_code, 403)

    def test_payment_status_filter_and_search_can_be_combined(self):
        matching = Payment.objects.create(
            member=self.member,
            amount=1000,
            status=Payment.STATUS_PENDING,
            date='2026-09-26',
            reference='FILTER-MATCH',
        )
        Payment.objects.create(
            member=self.member,
            amount=1000,
            status=Payment.STATUS_SUCCESS,
            date='2026-09-26',
            reference='FILTER-OTHER',
        )
        response = self.client.get('/payments/payments/', {'q': 'FILTER', 'status': Payment.STATUS_PENDING})
        self.assertEqual(list(response.context['payments']), [matching])
        self.assertContains(response, 'name="status"')
        self.assertContains(response, f'<option value="{Payment.STATUS_PENDING}" selected>')

    def test_subscription_list_paginates(self):
        manager = User.objects.create_user(username='subscription-manager', password='test-password')
        manager.profile.role = 'manager'
        manager.profile.gym = self.gym
        manager.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(manager)
        coach = Coach.objects.create(gym=self.gym, full_name='Pagination coach', phone='09121110000')
        gym_class = GymClass.objects.create(gym=self.gym, name='Pagination class', coach=coach, start_time='10:00', capacity=40)
        plan = ClassPlan.objects.create(gym_class=gym_class, sessions=12, price=250000)
        for index in range(26):
            member = Member.objects.create(gym=self.gym, first_name='Page', last_name=str(index), phone=f'0912555{index:04d}')
            Subscription.objects.create(member=member, plan=plan, sessions=12)
        response = self.client.get('/payments/subscriptions/?page=2')
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(len(response.context['subscriptions']), 1)
