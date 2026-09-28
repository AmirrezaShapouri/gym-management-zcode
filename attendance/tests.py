from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from classes.models import Coach, GymClass
from members.models import Member, Subscription
from .models import Attendance


class AttendanceWorkflowTests(TestCase):
	def setUp(self):
		user = User.objects.create_user(username='frontdesk', password='test-password')
		self.client.force_login(user)
		self.coach = Coach.objects.create(full_name='مربی تست', phone='09123330000')
		self.gym_class = GymClass.objects.create(
			name='کلاس تست', coach=self.coach, start_time='10:00', capacity=10,
		)
		self.member = Member.objects.create(
			first_name='عضو', last_name='تست', phone='09120000000', gym_class=self.gym_class,
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

	def test_history_route_filters_member(self):
		Attendance.objects.create(
			member=self.member,
			gym_class=self.gym_class,
			date=date(2026, 9, 26),
			status=Attendance.STATUS_ABSENT,
		)
		response = self.client.get('/attendance/history/?q=عضو')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context['records']), 1)

	def test_attendance_without_selected_status_is_not_recorded(self):
		response = self.client.post('/attendance/', {
			'gym_class': self.gym_class.pk,
			'date': '2026-09-26',
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Attendance.objects.exists())

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
			first_name='عضو', last_name='بدون اشتراک', phone='09127770000', gym_class=self.gym_class,
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
			name='کلاس دیگر', coach=self.gym_class.coach, start_time='11:00', capacity=10,
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

	def test_coach_can_only_view_classes_matching_their_profile_phone(self):
		other_coach = Coach.objects.create(full_name='مربی دیگر', phone='09120001111')
		other_class = GymClass.objects.create(
			name='کلاس دیگر', coach=other_coach, start_time='11:00', capacity=10,
		)
		coach_user = User.objects.create_user(username='coach', password='test-password')
		coach_user.profile.role = 'coach'
		coach_user.profile.phone = self.coach.phone
		coach_user.profile.save(update_fields=['role', 'phone'])
		self.client.force_login(coach_user)

		response = self.client.get('/classes/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(list(response.context['classes']), [self.gym_class])
		self.assertEqual(self.client.get(f'/classes/{other_class.pk}/').status_code, 404)
		attendance_response = self.client.get('/attendance/')
		self.assertEqual(attendance_response.context['form'].fields['gym_class'].queryset.count(), 1)

	def test_attendance_history_protects_member_and_class_from_delete(self):
		Attendance.objects.create(
			member=self.member,
			gym_class=self.gym_class,
			date=date(2026, 9, 26),
			status=Attendance.STATUS_EXCUSED,
		)
		with self.assertRaises(ProtectedError):
			self.member.delete()
		with self.assertRaises(ProtectedError):
			self.gym_class.delete()
