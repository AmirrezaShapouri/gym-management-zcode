import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gyms', '0005_backfill_gym_tenancy'),
        ('accounts', '0003_profile_gym'),
        ('classes', '0002_coach_gym_gymclass_gym'),
        ('members', '0002_member_gym'),
        ('notifications', '0003_announcement_gym_smsmessage_gym_smssettings_gym'),
        ('payments', '0004_expense_gym'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gymsettings',
            name='gym',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='settings',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='gymsubscription',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subscriptions',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='gymsubscriptionrequest',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='subscription_requests',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='gymsubscriptionrequest',
            name='invoice_image',
            field=models.ImageField(
                blank=True,
                upload_to='gym_subscriptions/invoices/',
                validators=[__import__('gyms.models', fromlist=['validate_invoice_image']).validate_invoice_image],
                verbose_name='تصویر رسید پرداخت',
            ),
        ),
        migrations.AlterField(
            model_name='coach',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='coaches',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='gymclass',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='classes',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='member',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='members',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='expense',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='expenses',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='announcements',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='smsmessage',
            name='gym',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sms_messages',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
        migrations.AlterField(
            model_name='smssettings',
            name='gym',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sms_settings',
                to='gyms.gym',
                verbose_name='باشگاه',
            ),
        ),
    ]
