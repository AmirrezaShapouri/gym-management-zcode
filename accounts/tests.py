from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from accounts.admin_site import RoleRestrictedAdminSite
from accounts.models import Profile
from core.mixins import user_role
from gyms.models import Gym, GymSubscriptionRequest


class AdminSiteAccessTests(SimpleTestCase):
    def setUp(self):
        self.site = RoleRestrictedAdminSite()

    def has_access(self, role, is_staff=True, is_active=True):
        user = SimpleNamespace(is_staff=is_staff, is_active=is_active)
        if role is not None:
            user.profile = SimpleNamespace(role=role)
        return self.site.has_permission(SimpleNamespace(user=user))

    def test_admin_role_can_access_admin_site(self):
        self.assertTrue(self.has_access(Profile.ROLE_ADMIN))

    def test_django_uses_restricted_admin_site(self):
        self.assertIsInstance(admin.site, RoleRestrictedAdminSite)

    def test_other_roles_cannot_access_admin_site(self):
        for role in (Profile.ROLE_MANAGER, Profile.ROLE_RECEPTION, Profile.ROLE_COACH):
            with self.subTest(role=role):
                self.assertFalse(self.has_access(role))

    def test_admin_role_requires_active_staff_account(self):
        self.assertFalse(self.has_access(Profile.ROLE_ADMIN, is_staff=False))
        self.assertFalse(self.has_access(Profile.ROLE_ADMIN, is_active=False))

    def test_missing_profile_cannot_access_admin_site(self):
        self.assertFalse(self.has_access(None))


class ProfileRoleTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Test Gym', slug='test-gym')

    def test_superuser_gets_admin_role(self):
        user = User.objects.create_superuser(username='site-admin', password='test-password')
        self.assertEqual(user.profile.role, Profile.ROLE_ADMIN)

    def test_user_without_profile_gets_least_privileged_role(self):
        user = SimpleNamespace(is_authenticated=True, is_superuser=False)
        self.assertEqual(user_role(user), Profile.ROLE_RECEPTION)

    def test_profile_form_updates_user_and_phone(self):
        user = User.objects.create_user(username='member-manager', password='test-password')
        user.profile.gym = self.gym
        user.profile.save(update_fields=['gym'])
        self.client.force_login(user)

        response = self.client.post('/accounts/profile/', {
            'save_profile': '1',
            'first_name': 'مدیر',
            'last_name': 'باشگاه',
            'email': 'manager@example.com',
            'phone': '09121112222',
        })

        self.assertRedirects(response, '/accounts/profile/')
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'مدیر')
        self.assertEqual(user.profile.phone, '09121112222')

    def test_manager_can_create_staff_account_with_selected_role(self):
        manager = User.objects.create_user(username='manager', password='test-password')
        manager.profile.role = Profile.ROLE_MANAGER
        manager.profile.gym = self.gym
        manager.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(manager)

        response = self.client.post('/accounts/profile/', {
            'create_staff': '1',
            'username': 'coach-account',
            'first_name': 'مربی',
            'last_name': 'باشگاه',
            'password': 'StrongExamplePass_927!',
            'phone': '09123334444',
            'role': Profile.ROLE_COACH,
        })

        self.assertRedirects(response, '/accounts/profile/')
        staff = User.objects.get(username='coach-account')
        self.assertEqual(staff.profile.role, Profile.ROLE_COACH)
        self.assertEqual(staff.profile.gym, self.gym)
        self.assertTrue(staff.check_password('StrongExamplePass_927!'))

    def test_non_manager_cannot_create_staff_account(self):
        user = User.objects.create_user(username='reception-user', password='test-password')
        user.profile.gym = self.gym
        user.profile.save(update_fields=['gym'])
        self.client.force_login(user)

        response = self.client.post('/accounts/profile/', {
            'create_staff': '1',
            'username': 'forbidden-user',
            'password': 'StrongExamplePass_927!',
            'phone': '09123334444',
            'role': Profile.ROLE_COACH,
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='forbidden-user').exists())

    def test_manager_can_request_gym_subscription_renewal(self):
        manager = User.objects.create_user(username='gym-manager', password='test-password')
        manager.profile.role = Profile.ROLE_MANAGER
        manager.profile.gym = self.gym
        manager.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(manager)

        image_data = BytesIO()
        Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
        invoice = SimpleUploadedFile('receipt.png', image_data.getvalue(), content_type='image/png')

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post('/accounts/subscription/renew/', {
                'sessions': '36',
                'invoice_image': invoice,
            })

        self.assertRedirects(response, '/accounts/profile/')
        request = GymSubscriptionRequest.objects.get(gym=self.gym)
        self.assertEqual(request.sessions, 36)
        self.assertEqual(request.price, 6000000)
        self.assertTrue(request.invoice_image.name.startswith('gym_subscriptions/invoices/'))
        self.assertIsNotNone(request.submitted_at)
        self.assertEqual(request.status, GymSubscriptionRequest.STATUS_PENDING)

    def test_invalid_password_change_renders_form(self):
        user = User.objects.create_user(username='password-user', password='old-password')
        user.profile.gym = self.gym
        user.profile.save(update_fields=['gym'])
        self.client.force_login(user)

        response = self.client.post('/accounts/password/', {
            'old_password': 'wrong-password',
            'new_password1': 'NewStrongPass_927!',
            'new_password2': 'NewStrongPass_927!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_change.html')

    def test_admin_login_routes_to_django_admin(self):
        User.objects.create_superuser(username='admin-login', password='test-password')

        response = self.client.post('/accounts/login/', {
            'username': 'admin-login',
            'password': 'test-password',
        })

        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)
