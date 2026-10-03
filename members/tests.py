from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from classes.models import Coach, ClassPlan, GymClass
from gyms.models import Gym
from .models import Member, Subscription


class MemberWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Member Gym', slug='member-gym')
        self.user = User.objects.create_user(username='reception', password='test-password')
        self.user.profile.role = 'reception'
        self.user.profile.gym = self.gym
        self.user.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(self.user)

    def test_member_list_displays_database_records(self):
        member = Member.objects.create(gym=self.gym, first_name='آزمون', last_name='پایگاه', phone='09120000000')

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
        member = Member.objects.create(gym=self.gym, first_name='رضا', last_name='کریمی', phone='09123333333')

        response = self.client.get(f'/members/{member.pk}/delete/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/members/{member.pk}/delete/')
        self.assertRedirects(response, '/members/')
        self.assertFalse(Member.objects.filter(pk=member.pk).exists())


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Subscription Gym', slug='subscription-gym')
        self.member = Member.objects.create(gym=self.gym, first_name='آزمون', last_name='اشتراک', phone='09120000001')
        self.coach = Coach.objects.create(gym=self.gym, full_name='مربی اشتراک', phone='09120000002')
        self.gym_class = GymClass.objects.create(gym=self.gym, name='کلاس اشتراک', coach=self.coach, start_time='10:00', capacity=10)
        self.member.gym_class = self.gym_class
        self.member.coach = self.coach
        self.member.save(update_fields=['gym_class', 'coach'])
        self.plan = ClassPlan.objects.create(gym_class=self.gym_class, sessions=12, price=250000)

    def test_new_subscription_initializes_sessions_and_plan_price(self):
        subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
        self.assertEqual(subscription.remaining_sessions, 12)
        self.assertEqual(subscription.price, self.plan.price)

    def test_session_change_preserves_consumed_session_count(self):
        subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
        subscription.remaining_sessions = 8
        subscription.save(update_fields=['remaining_sessions'])
        subscription.sessions = 36
        subscription.plan = ClassPlan.objects.create(gym_class=self.gym_class, sessions=36, price=600000)
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

    def test_member_profile_validate_rejects_other_gym_class(self):
        other_gym = Gym.objects.create(name='Other Gym', slug='other-gym')
        other_coach = Coach.objects.create(gym=other_gym, full_name='مربی دیگر', phone='09120001111')
        other_class = GymClass.objects.create(gym=other_gym, name='کلاس دیگر', coach=other_coach, start_time='11:00', capacity=10)
        member = Member(gym=self.gym, first_name='X', last_name='Y', phone='09120000099', gym_class=other_class)
        with self.assertRaises(ValidationError):
            member.full_clean()

    def test_plan_price_changes_do_not_rewrite_historical_subscription_price(self):
        subscription = Subscription.objects.create(member=self.member, plan=self.plan, sessions=12)
        ClassPlan.objects.filter(pk=self.plan.pk).update(price=300000)
        subscription.remaining_sessions -= 1
        subscription.save(update_fields=['remaining_sessions'])
        self.assertEqual(subscription.price, 250000)
