from datetime import date, timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from PIL import Image
from django.core.exceptions import ValidationError

from .forms import GymSubscriptionRequestForm
from .models import GymSettings, GymSubscription

# Create your tests here.


class GymSettingsTests(TestCase):
	def test_gym_settings_is_singleton(self):
		self.assertEqual(GymSettings.load().pk, 1)
		with self.assertRaises(ValidationError):
			GymSettings(pk=2).save()


def png_upload(name='receipt.png'):
	image_data = BytesIO()
	Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
	return SimpleUploadedFile(name, image_data.getvalue(), content_type='image/png')


class GymSubscriptionWorkflowTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_superuser(username='saas-admin', password='test-password')
		self.manager = User.objects.create_user(username='gym-manager', password='test-password')
		self.manager.profile.role = 'manager'
		self.manager.profile.save(update_fields=['role'])

	def tearDown(self):
		for subscription in GymSubscription.objects.exclude(invoice_image=''):
			subscription.invoice_image.delete(save=False)

	def make_request(self, **kwargs):
		return GymSubscription.objects.create(
			sessions=kwargs.pop('sessions', 12),
			price=kwargs.pop('price', 2500000),
			status=GymSubscription.STATUS_PENDING,
			invoice_image=kwargs.pop('invoice_image', png_upload()),
			**kwargs,
		)

	def test_invoice_validation_rejects_non_images_and_oversized_uploads(self):
		for filename, contents in (
			('payload.exe', b'MZ executable'),
			('fake.png', b'MZ executable'),
		):
			form = GymSubscriptionRequestForm(data={'sessions': '12'}, files={
				'invoice_image': SimpleUploadedFile(filename, contents, content_type='image/png'),
			})
			self.assertFalse(form.is_valid())
			self.assertIn('invoice_image', form.errors)

		image_data = BytesIO()
		Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
		large_file = SimpleUploadedFile(
			'large.png', image_data.getvalue() + b'x' * (5 * 1024 * 1024 + 1),
			content_type='image/png',
		)
		large_form = GymSubscriptionRequestForm(data={'sessions': '12'}, files={'invoice_image': large_file})
		self.assertFalse(large_form.is_valid())

	def test_media_url_and_invoice_upload_directory(self):
		self.assertEqual(settings.MEDIA_URL, '/media/')
		self.assertEqual(GymSubscription._meta.get_field('invoice_image').upload_to,
			             'gym_subscriptions/invoices/')

	def test_approval_sets_dates_reviewer_and_active_status(self):
		request = self.make_request()
		request.approve(self.admin)
		self.assertEqual(request.status, GymSubscription.STATUS_ACTIVE)
		self.assertEqual(request.start_date, date.today())
		self.assertIsNotNone(request.end_date)
		self.assertIsNotNone(request.reviewed_at)
		self.assertEqual(request.reviewed_by, self.admin)

	def test_approval_requires_receipt(self):
		request = self.make_request(invoice_image='')
		with self.assertRaises(ValidationError):
			request.approve(self.admin)
		self.assertEqual(request.status, GymSubscription.STATUS_PENDING)

	def test_expired_active_subscriptions_transition_to_expired(self):
		old_subscription = GymSubscription.objects.create(
			sessions=12, price=2500000,
			start_date=timezone.localdate() - timedelta(days=31),
			end_date=timezone.localdate() - timedelta(days=1),
			status=GymSubscription.STATUS_ACTIVE,
		)
		self.assertEqual(GymSubscription.expire_due(), 1)
		old_subscription.refresh_from_db()
		self.assertEqual(old_subscription.status, GymSubscription.STATUS_EXPIRED)

	def test_admin_can_approve_pending_request(self):
		request = self.make_request()
		self.client.force_login(self.admin)
		response = self.client.post(reverse('admin:gyms_gymsubscription_changelist'), {
			'action': 'approve_requests',
			'_selected_action': [request.pk],
		})
		self.assertEqual(response.status_code, 302)
		request.refresh_from_db()
		self.assertEqual(request.status, GymSubscription.STATUS_ACTIVE)
		self.assertEqual(request.reviewed_by, self.admin)

	def test_admin_rejection_records_reason_and_preserves_active_subscription(self):
		active = GymSubscription.objects.create(
			sessions=12, price=2500000, start_date=date(2026, 9, 1),
			end_date=date(2026, 9, 30), status=GymSubscription.STATUS_ACTIVE,
		)
		request = self.make_request(sessions=36, price=6000000, rejection_reason='رسید ناخوانا')
		self.client.force_login(self.admin)
		response = self.client.post(reverse('admin:gyms_gymsubscription_changelist'), {
			'action': 'reject_requests',
			'_selected_action': [request.pk],
		})
		self.assertEqual(response.status_code, 302)
		request.refresh_from_db()
		active.refresh_from_db()
		self.assertEqual(request.status, GymSubscription.STATUS_REJECTED)
		self.assertEqual(request.rejection_reason, 'رسید ناخوانا')
		self.assertIsNotNone(request.reviewed_at)
		self.assertEqual(request.reviewed_by, self.admin)
		self.assertEqual(active.status, GymSubscription.STATUS_ACTIVE)

	def test_manager_cannot_access_saas_admin_review(self):
		self.client.force_login(self.manager)
		request = self.make_request()
		response = self.client.post(reverse('admin:gyms_gymsubscription_changelist'), {
			'action': 'approve_requests',
			'_selected_action': [request.pk],
		})
		self.assertNotEqual(response.status_code, 200)
		request.refresh_from_db()
		self.assertEqual(request.status, GymSubscription.STATUS_PENDING)

	def test_image_upload_uses_configured_invoice_path(self):
		form = GymSubscriptionRequestForm(data={'sessions': '12'}, files={'invoice_image': png_upload()})
		self.assertTrue(form.is_valid(), form.errors)
		with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			request = form.save()
			self.assertTrue(request.invoice_image.name.startswith('gym_subscriptions/invoices/'))
			self.assertTrue(request.invoice_image.storage.exists(request.invoice_image.name))
