from django.contrib.auth.models import User
from django.test import TestCase

from .models import Member


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
