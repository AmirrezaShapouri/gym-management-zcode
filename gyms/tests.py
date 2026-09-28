from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import GymSettings

# Create your tests here.


class GymSettingsTests(TestCase):
	def test_gym_settings_is_singleton(self):
		self.assertEqual(GymSettings.load().pk, 1)
		with self.assertRaises(ValidationError):
			GymSettings(pk=2).save()
