from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import Coach, ClassPlan, GymClass
from members.models import Member, Subscription


class PortalEntryTests(TestCase):
	def test_home_and_login_pages_render(self):
		self.assertEqual(self.client.get('/').status_code, 200)
		self.assertEqual(self.client.get('/accounts/login/').status_code, 200)

	def test_login_sends_operational_user_to_dashboard(self):
		User.objects.create_user(username='reception-login', password='test-password')

		response = self.client.post('/accounts/login/', {
			'username': 'reception-login',
			'password': 'test-password',
		})

		self.assertRedirects(response, '/dashboard/')
		self.assertEqual(self.client.get('/dashboard/').status_code, 200)

	def test_dashboard_requires_login(self):
		response = self.client.get('/dashboard/')
		self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

	def test_primary_pages_render_for_operational_user(self):
		user = User.objects.create_user(username='portal-manager', password='test-password')
		user.profile.role = 'manager'
		user.profile.save(update_fields=['role'])
		self.client.force_login(user)
		coach = Coach.objects.create(full_name='مربی صفحات')
		gym_class = GymClass.objects.create(name='کلاس صفحات', coach=coach, start_time='10:00', capacity=10)
		member = Member.objects.create(
			first_name='عضو', last_name='صفحات', phone='09129990000', gym_class=gym_class,
		)
		plan = ClassPlan.objects.create(gym_class=gym_class, sessions=12, price=100000)
		Subscription.objects.create(member=member, plan=plan, sessions=12)
		paths = [
			'/dashboard/', '/members/', '/members/new/', f'/members/{member.pk}/',
			f'/members/{member.pk}/edit/', f'/members/{member.pk}/delete/',
			'/classes/', '/classes/new/', f'/classes/{gym_class.pk}/',
			f'/classes/{gym_class.pk}/edit/', f'/classes/{gym_class.pk}/delete/',
			'/attendance/', '/attendance/history/', '/payments/subscriptions/',
			'/payments/subscriptions/new/', f'/payments/subscriptions/{Subscription.objects.get(member=member).pk}/',
			'/payments/payments/', '/payments/finance/',
			'/payments/expenses/', '/gyms/settings/', '/notifications/',
			'/notifications/settings/', '/accounts/profile/',
		]
		for path in paths:
			with self.subTest(path=path):
				self.assertEqual(self.client.get(path).status_code, 200)
