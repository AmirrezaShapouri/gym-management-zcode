from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from classes.models import Coach, ClassPlan, GymClass
from .models import Member, Subscription


class MemberWorkflowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='reception', password='test-password')
		self.client.force_login(self.user)

	def test_member_list_displays_database_records(self):
		member = Member.objects.create(first_name='آزمون', last_name='پایگاه', phone='09120000000')

		response = self.client.get('/members/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, member.full_name)

	def test_member_can_be_created_and_updated(self):
		response = self.client.post('/members/new/', {
			'first_name': 'علی',
			'last_name': 'رضایی',
			'phone': '09121111111',
			'gender': 'male',
		})

		member = Member.objects.get(phone='09121111111')
		self.assertRedirects(response, f'/members/{member.pk}/')
		response = self.client.post(f'/members/{member.pk}/edit/', {
			'first_name': 'علی',
			'last_name': 'کریمی',
			'phone': member.phone,
			'gender': 'male',
		})
		member.refresh_from_db()
		self.assertRedirects(response, f'/members/{member.pk}/')
		self.assertEqual(member.last_name, 'کریمی')

	def test_admin_role_cannot_access_member_pages(self):
		admin = User.objects.create_superuser(username='site-admin', password='test-password')
		self.client.force_login(admin)

		self.assertEqual(self.client.get('/members/').status_code, 403)

	def test_member_delete_requires_post(self):
		member = Member.objects.create(first_name='رضا', last_name='کریمی', phone='09123333333')

		response = self.client.get(f'/members/{member.pk}/delete/')

		self.assertEqual(response.status_code, 200)
		member.refresh_from_db()
		response = self.client.post(f'/members/{member.pk}/delete/')
		self.assertRedirects(response, '/members/')
		self.assertFalse(Member.objects.filter(pk=member.pk).exists())


class SubscriptionModelTests(TestCase):
	def setUp(self):
		self.member = Member.objects.create(first_name='آزمون', last_name='اشتراک', phone='09120000001')
		coach = Coach.objects.create(full_name='مربی اشتراک')
		gym_class = GymClass.objects.create(name='کلاس اشتراک', coach=coach, start_time='10:00', capacity=10)
		self.plan = ClassPlan.objects.create(gym_class=gym_class, sessions=12, price=250000)

	def test_new_subscription_initializes_sessions_and_plan_price(self):
		subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
		self.assertEqual(subscription.remaining_sessions, 12)
		self.assertEqual(subscription.price, self.plan.price)

	def test_session_change_preserves_consumed_session_count(self):
		subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
		subscription.remaining_sessions = 8
		subscription.save(update_fields=['remaining_sessions'])
		subscription.sessions = 36
		subscription.plan = ClassPlan.objects.create(
			gym_class=self.plan.gym_class, sessions=36, price=600000,
		)
		subscription.price = subscription.plan.price
		subscription.save()
		self.assertEqual(subscription.remaining_sessions, 32)

	def test_plan_session_and_date_validation(self):
		invalid = Subscription(
			member=self.member,
			plan=self.plan,
			sessions=36,
			start_date=date(2026, 9, 10),
			end_date=date(2026, 9, 9),
		)
		with self.assertRaises(ValidationError):
			invalid.full_clean()

	def test_latest_subscription_uses_prefetched_records(self):
		Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
		with self.assertNumQueries(3):
			member = Member.objects.prefetch_related('subscriptions__plan').get(pk=self.member.pk)
			self.assertEqual(member.latest_subscription.sessions, 12)

	def test_plan_price_changes_do_not_rewrite_historical_subscription_price(self):
		subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
		ClassPlan.objects.filter(pk=self.plan.pk).update(price=300000)
		subscription.remaining_sessions -= 1
		subscription.save(update_fields=['remaining_sessions'])
		self.assertEqual(subscription.price, 250000)
