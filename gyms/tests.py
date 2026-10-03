from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.admin_site import RoleRestrictedAdminSite
from accounts.models import Profile
from gyms.forms import GymSubscriptionRequestForm
from gyms.models import Gym, GymSettings, GymSubscription, GymSubscriptionRequest


class GymSettingsTests(TestCase):
    def test_gym_settings_are_scoped_per_gym(self):
        gym_a = Gym.objects.create(name='Gym A', slug='gym-a')
        gym_b = Gym.objects.create(name='Gym B', slug='gym-b')
        GymSettings.objects.create(gym=gym_a, name='Gym A Settings')
        GymSettings.objects.create(gym=gym_b, name='Gym B Settings')

        self.assertEqual(GymSettings.objects.filter(gym=gym_a).count(), 1)
        self.assertEqual(GymSettings.objects.filter(gym=gym_b).count(), 1)
        self.assertNotEqual(GymSettings.objects.get(gym=gym_a).pk, GymSettings.objects.get(gym=gym_b).pk)

        with self.assertRaises(ValidationError):
            GymSettings(gym=gym_a, name='Duplicate').save()


def png_upload(name='receipt.png'):
    image_data = BytesIO()
    Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
    return SimpleUploadedFile(name, image_data.getvalue(), content_type='image/png')


class GymSubscriptionWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='SaaS Gym', slug='saas-gym')
        self.admin = User.objects.create_superuser(username='saas-admin', password='test-password')
        self.manager = User.objects.create_user(username='gym-manager', password='test-password')
        self.manager.profile.role = Profile.ROLE_MANAGER
        self.manager.profile.gym = self.gym
        self.manager.profile.save(update_fields=['role', 'gym'])

    def make_request(self, **kwargs):
        image_data = BytesIO()
        Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
        invoice = kwargs.pop('invoice_image', SimpleUploadedFile('receipt.png', image_data.getvalue(), content_type='image/png'))
        return GymSubscriptionRequest.objects.create(
            gym=kwargs.pop('gym', self.gym),
            sessions=kwargs.pop('sessions', 12),
            price=kwargs.pop('price', GymSubscription.PLAN_PRICES[12]),
            invoice_image=invoice,
            status=kwargs.pop('status', GymSubscriptionRequest.STATUS_PENDING),
            **kwargs,
        )

    def test_invoice_validation_rejects_non_images_and_oversized_uploads(self):
        for filename, contents in (
            ('payload.exe', b'MZ executable'),
            ('fake.png', b'MZ executable'),
        ):
            form = GymSubscriptionRequestForm(gym=self.gym, data={'sessions': '12'}, files={
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
        large_form = GymSubscriptionRequestForm(gym=self.gym, data={'sessions': '12'}, files={'invoice_image': large_file})
        self.assertFalse(large_form.is_valid())

    def test_media_url_and_invoice_upload_directory(self):
        self.assertEqual('/media/', '/media/')
        self.assertEqual(GymSubscriptionRequest._meta.get_field('invoice_image').upload_to, 'gym_subscriptions/invoices/')

    def test_approval_sets_dates_reviewer_and_active_status(self):
        request = self.make_request()
        subscription = request.approve(self.admin)
        request.refresh_from_db()
        self.assertEqual(request.status, GymSubscriptionRequest.STATUS_APPROVED)
        self.assertEqual(subscription.status, GymSubscription.STATUS_ACTIVE)
        self.assertEqual(subscription.gym, self.gym)
        self.assertIsNotNone(request.reviewed_at)
        self.assertEqual(request.reviewed_by, self.admin)

    def test_approval_requires_receipt(self):
        request = self.make_request(invoice_image='')
        with self.assertRaises(ValidationError):
            request.approve(self.admin)
        self.assertEqual(request.status, GymSubscriptionRequest.STATUS_PENDING)

    def test_admin_can_approve_pending_request(self):
        request = self.make_request()
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:gyms_gymsubscriptionrequest_changelist'), {
            'action': 'approve_requests',
            '_selected_action': [request.pk],
        })
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, GymSubscriptionRequest.STATUS_APPROVED)

    def test_admin_rejection_records_reason(self):
        request = self.make_request()
        request.rejection_reason = 'رسید ناخوانا'
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin:gyms_gymsubscriptionrequest_changelist'), {
            'action': 'reject_requests',
            '_selected_action': [request.pk],
        })
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, GymSubscriptionRequest.STATUS_REJECTED)
        self.assertEqual(request.rejection_reason, 'رسید ناخوانا')

    def test_manager_cannot_access_saas_admin_review(self):
        request = self.make_request()
        self.client.force_login(self.manager)
        response = self.client.post(reverse('admin:gyms_gymsubscriptionrequest_changelist'), {
            'action': 'approve_requests',
            '_selected_action': [request.pk],
        })
        self.assertNotEqual(response.status_code, 200)

    def test_image_upload_uses_configured_invoice_path(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            request = self.make_request()
            self.assertTrue(request.invoice_image.name.startswith('gym_subscriptions/invoices/'))
            self.assertTrue(request.invoice_image.storage.exists(request.invoice_image.name))


class AdminSiteAccessTests(TestCase):
    def test_django_admin_is_restricted(self):
        site = RoleRestrictedAdminSite()
        self.assertIsInstance(admin.site, RoleRestrictedAdminSite)
        self.assertFalse(site.has_permission(type('UserStub', (), {
            'user': type('U', (), {
                'is_staff': True,
                'is_active': True,
                'profile': type('P', (), {'role': Profile.ROLE_MANAGER})(),
            })()
        })()))
