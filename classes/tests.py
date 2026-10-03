from django.contrib.auth.models import User
from django.test import TestCase

from classes.models import Coach, GymClass
from gyms.models import Gym


class ClassWorkflowTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name='Class Gym', slug='class-gym')
        user = User.objects.create_user(username='manager', password='test-password')
        user.profile.role = 'manager'
        user.profile.gym = self.gym
        user.profile.save(update_fields=['role', 'gym'])
        self.client.force_login(user)

    def test_class_list_is_routed(self):
        response = self.client.get('/classes/')
        self.assertEqual(response.status_code, 200)

    def test_class_create_persists_schedule(self):
        coach = Coach.objects.create(gym=self.gym, full_name='مربی آزمایشی', phone='09120000000')
        response = self.client.post('/classes/new/', {
            'name': 'کلاس آزمایشی',
            'coach': coach.pk,
            'days': ['saturday', 'monday'],
            'start_time': '18:00',
            'end_time': '19:00',
            'capacity': 12,
            'is_active': 'on',
            'description': '',
            'plans-TOTAL_FORMS': '1',
            'plans-INITIAL_FORMS': '0',
            'plans-MIN_NUM_FORMS': '0',
            'plans-MAX_NUM_FORMS': '1000',
            'plans-0-sessions': '12',
            'plans-0-price': '250000',
        })
        self.assertEqual(response.status_code, 302)
        gym_class = GymClass.objects.get(name='کلاس آزمایشی')
        self.assertEqual(gym_class.gym, self.gym)
        self.assertEqual(gym_class.days, 'saturday monday')
        self.assertEqual(gym_class.plans.get(sessions=12).price, 250000)
