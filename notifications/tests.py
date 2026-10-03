from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from classes.models import Coach, GymClass
from gyms.models import Gym
from members.models import Member
from .models import Announcement, SMSMessage, SMSSettings


class NotificationWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Notification Gym', slug='notification-gym')
        user = User.objects.create_user(username='operator', password='test-password')
        user.profile.role = 'reception'
        user.profile.gym = self.gym
        user.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(user)
        coach = Coach.objects.create(gym=self.gym, full_name='مربی پیامک', phone='09125555555')
        self.gym_class = GymClass.objects.create(gym=self.gym, name='کلاس پیامک', coach=coach, start_time='10:00', capacity=10)
        self.member = Member.objects.create(gym=self.gym, first_name='عضو', last_name='اعلان', phone='09125555555', gym_class=self.gym_class, coach=coach)

    def test_announcement_creates_pending_message_records(self):
        response = self.client.post('/notifications/', {
            'message_type': 'تغییر برنامه',
            'body': 'کلاس امروز برگزار نمی‌شود.',
            'classes': [self.gym_class.pk],
        })
        self.assertRedirects(response, '/notifications/')
        self.assertEqual(Announcement.objects.filter(gym=self.gym).count(), 1)
        message = SMSMessage.objects.get(member=self.member, gym=self.gym)
        self.assertEqual(message.status, SMSMessage.STATUS_PENDING)

    def test_notification_settings_render_and_save_member_preferences(self):
        manager = User.objects.create_user(username='manager-settings', password='test-password')
        manager.profile.role = 'manager'
        manager.profile.gym = self.gym
        manager.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(manager)
        response = self.client.get('/notifications/settings/')
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/notifications/settings/', {
            'save_members': '1',
            f'member_{self.member.pk}_class_reminder': 'on',
            f'member_{self.member.pk}_payment': 'on',
        })
        self.assertRedirects(response, '/notifications/settings/')
        self.member.refresh_from_db()
        self.assertTrue(self.member.notification_setting.class_reminder)
        self.assertFalse(self.member.notification_setting.subscription_expiry)

    def test_sms_settings_reject_a_second_record(self):
        SMSSettings.objects.create(gym=self.gym)
        with self.assertRaises(ValidationError):
            SMSSettings(gym=self.gym).save()

    def test_message_history_survives_member_deletion(self):
        message = SMSMessage.objects.create(
            gym=self.gym,
            member=self.member,
            message_type=SMSMessage.TYPE_ANNOUNCEMENT,
            body='Historical message',
        )
        self.member.delete()
        message.refresh_from_db()
        self.assertIsNone(message.member)
        self.assertEqual(str(message), 'عضو حذف‌شده - اعلانیه')
