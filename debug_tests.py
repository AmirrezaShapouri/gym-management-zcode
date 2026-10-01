import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_project.settings')

import django

django.setup()

from django.test.runner import DiscoverRunner

# Run the project test suite and save failures to a file.
runner = DiscoverRunner(verbosity=2, failfast=False)
result = runner.run_tests([])

print('TOTAL_TESTS', result)
