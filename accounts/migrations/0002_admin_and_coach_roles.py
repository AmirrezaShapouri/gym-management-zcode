from django.conf import settings
from django.db import migrations, models


def promote_superusers(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)
    database = schema_editor.connection.alias

    for user in User.objects.using(database).filter(is_superuser=True).iterator():
        Profile.objects.using(database).update_or_create(
            user_id=user.pk,
            defaults={'role': 'admin'},
        )


def restore_superusers(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    database = schema_editor.connection.alias
    Profile.objects.using(database).filter(
        user__is_superuser=True,
        role='admin',
    ).update(role='manager')


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'ادمین'),
                    ('manager', 'مدیر'),
                    ('reception', 'پذیرش'),
                    ('coach', 'مربی'),
                ],
                default='reception',
                max_length=20,
                verbose_name='نقش',
            ),
        ),
        migrations.RunPython(promote_superusers, restore_superusers),
    ]