from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from classes.models import Coach, GymClass
from gyms.models import Gym
from members.models import Member, Subscription
from .models import Attendance


class AttendanceWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Attendance Gym', slug='attendance-gym')
        user = User.objects.create_user(username='frontdesk', password='test-password')
        user.profile.gym = self.gym
        user.profile.role = 'reception'
        user.profile.save(update_fields=['gym', 'role'])
        self.client.force_login(user)
        self.coach = Coach.objects.create(gym=self.gym, full_name='مربی تست', phone='09123330000')
        self.gym_class = GymClass.objects.create(
            gym=self.gym, name='کلاس تست', coach=self.coach, start_time='10:00', capacity=10,
        )
        self.member = Member.objects.create(
            gym=self.gym, first_name='عضو', last_name='تست', phone='09120000000', gym_class=self.gym_class, coach=self.coach,
        )
        plan = self.gym_class.plans.create(sessions=12, price=120000)
        self.subscription = Subscription.objects.create(member=self.member, plan=plan, sessions=12)

    def test_attendance_post_saves_record_and_user(self):
        response = self.client.post('/attendance/', {
            'gym_class': self.gym_class.pk,
            'date': '2026-09-26',
            f'status_{self.member.pk}': Attendance.STATUS_PRESENT,
        })
        self.assertEqual(response.status_code, 200)
        record = Attendance.objects.get(member=self.member)
        self.assertEqual(record.status, Attendance.STATUS_PRESENT)
        self.assertEqual(record.recorded_by.username, 'frontdesk')

    def test_status_changes_consume_and_restore_exactly_once(self):
        record = Attendance.objects.create(
            member=self.member,
            gym_class=self.gym_class,
            date=date(2026, 9, 26),
            status=Attendance.STATUS_PRESENT,
        )
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.remaining_sessions, 11)

        record.status = Attendance.STATUS_ABSENT
        record.save()
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.remaining_sessions, 11)

        record.status = Attendance.STATUS_EXCUSED
        record.save()
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.remaining_sessions, 12)

        record.status = Attendance.STATUS_PRESENT
        record.save()
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.remaining_sessions, 11)

    def test_no_sessions_left_rejects_counted_attendance(self):
        self.subscription.remaining_sessions = 0
        self.subscription.save(update_fields=['remaining_sessions'])

        with self.assertRaises(ValidationError):
            Attendance.objects.create(
                member=self.member,
                gym_class=self.gym_class,
                date=date(2026, 9, 27),
                status=Attendance.STATUS_ABSENT,
            )
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.remaining_sessions, 0)
        self.assertFalse(Attendance.objects.filter(date=date(2026, 9, 27)).exists())

    def test_counted_attendance_requires_an_active_subscription(self):
        member_without_subscription = Member.objects.create(
            gym=self.gym,
            first_name='عضو',
            last_name='بدون اشتراک',
            phone='09127770000',
            gym_class=self.gym_class,
            coach=self.coach,
        )
        with self.assertRaises(ValidationError):
            Attendance.objects.create(
                member=member_without_subscription,
                gym_class=self.gym_class,
                date=date(2026, 9, 27),
                status=Attendance.STATUS_PRESENT,
            )

    def test_member_must_be_enrolled_in_attendance_class(self):
        other_class = GymClass.objects.create(
            gym=self.gym,
            name='کلاس دیگر',
            coach=self.gym_class.coach,
            start_time='11:00',
            capacity=10,
        )
        record = Attendance(
            member=self.member,
            gym_class=other_class,
            date=date(2026, 9, 26),
            status=Attendance.STATUS_PRESENT,
        )
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_duplicate_attendance_is_rejected(self):
        Attendance.objects.create(
            member=self.member,
            gym_class=self.gym_class,
            date=date(2026, 9, 26),
            status=Attendance.STATUS_EXCUSED,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(
                    member=self.member,
                    gym_class=self.gym_class,
                    date=date(2026, 9, 26),
                    status=Attendance.STATUS_EXCUSED,
                )
