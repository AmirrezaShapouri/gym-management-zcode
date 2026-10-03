from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import Coach, ClassPlan, GymClass
from core.jalali import date_to_jalali_str, gregorian_to_jalali, jalali_str_to_date
from gyms.models import Gym, GymSettings
from members.models import Member, Subscription


class PortalEntryTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Portal Gym', slug='portal-gym')

    def test_home_and_login_pages_render(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/accounts/login/').status_code, 200)

    def test_login_sends_operational_user_to_dashboard(self):
        user = User.objects.create_user(username='reception-login', password='test-password')
        user.profile.gym = self.gym
        user.profile.role = 'reception'
        user.profile.save(update_fields=['gym', 'role'])

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
        user.profile.gym = self.gym
        user.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(user)
        GymSettings.objects.get_or_create(gym=self.gym, defaults={'name': self.gym.name})
        coach = Coach.objects.create(gym=self.gym, full_name='مربی صفحات', phone='09129990000')
        gym_class = GymClass.objects.create(gym=self.gym, name='کلاس صفحات', coach=coach, start_time='10:00', capacity=10)
        member = Member.objects.create(
            gym=self.gym,
            first_name='عضو',
            last_name='صفحات',
            phone='09129990000',
            gym_class=gym_class,
            coach=coach,
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


class JalaliConversionTests(TestCase):
    def test_normal_date_conversion(self):
        self.assertEqual(date_to_jalali_str(date(2024, 3, 20)), '۱۴۰۳/۰۱/۰۱')
        self.assertEqual(jalali_str_to_date('1403/01/01'), date(2024, 3, 20))

    def test_persian_and_english_digits_are_accepted(self):
        self.assertEqual(jalali_str_to_date('۱۴۰۳/۰۱/۰۱'), date(2024, 3, 20))
        self.assertEqual(jalali_str_to_date('1403-01-01'), date(2024, 3, 20))

    def test_leap_year_esfand_30(self):
        self.assertEqual(jalali_str_to_date('1399/12/30'), date(2021, 3, 20))
        self.assertIsNone(jalali_str_to_date('1400/12/30'))

    def test_end_of_esfand_and_start_of_farvardin(self):
        self.assertEqual(jalali_str_to_date('1402/12/29'), date(2024, 3, 19))
        self.assertEqual(gregorian_to_jalali(2024, 3, 20), (1403, 1, 1))

    def test_invalid_jalali_dates_are_rejected(self):
        for value in ('1403/13/01', '1403/00/01', '1403/01/32', '1402/12/30', 'invalid'):
            with self.subTest(value=value):
                self.assertIsNone(jalali_str_to_date(value))
