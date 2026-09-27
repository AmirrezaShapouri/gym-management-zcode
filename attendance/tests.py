from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import Coach, GymClass
from members.models import Member
from .models import Attendance


class AttendanceWorkflowTests(TestCase):
	def setUp(self):
		user = User.objects.create_user(username='frontdesk', password='test-password')
		self.client.force_login(user)
		coach = Coach.objects.create(full_name='مربی تست')
		self.gym_class = GymClass.objects.create(
			name='کلاس تست', coach=coach, start_time='10:00', capacity=10,
		)
		self.member = Member.objects.create(
			first_name='عضو', last_name='تست', phone='09120000000', gym_class=self.gym_class,
		)

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
