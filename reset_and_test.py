import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_project.settings')

import django
import psycopg2
from django.conf import settings
from django.core.management import call_command


django.setup()

cfg = settings.DATABASES['default']
db_name = cfg['NAME']
postgres_name = 'postgres'
conn = psycopg2.connect(
    dbname=postgres_name,
    user=cfg['USER'],
    password=cfg['PASSWORD'],
    host=cfg['HOST'],
    port=cfg['PORT'],
)
conn.autocommit = True
cursor = conn.cursor()
cursor.execute(f'DROP DATABASE IF EXISTS test_{db_name}')
cursor.close()
conn.close()
print(f'Dropped test_{db_name}')

call_command('test', verbosity=2)
