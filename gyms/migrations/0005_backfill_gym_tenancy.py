from django.db import migrations, models
from django.db.models import Q


def backfill_default_gym(apps, schema_editor):
    alias = schema_editor.connection.alias
    Gym = apps.get_model('gyms', 'Gym')
    GymSettings = apps.get_model('gyms', 'GymSettings')
    GymSubscription = apps.get_model('gyms', 'GymSubscription')
    GymSubscriptionRequest = apps.get_model('gyms', 'GymSubscriptionRequest')
    Profile = apps.get_model('accounts', 'Profile')
    Coach = apps.get_model('classes', 'Coach')
    GymClass = apps.get_model('classes', 'GymClass')
    Member = apps.get_model('members', 'Member')
    Expense = apps.get_model('payments', 'Expense')
    Announcement = apps.get_model('notifications', 'Announcement')
    SMSMessage = apps.get_model('notifications', 'SMSMessage')
    SMSSettings = apps.get_model('notifications', 'SMSSettings')

    gym, _ = Gym.objects.using(alias).get_or_create(
        slug='default-gym',
        defaults={'name': 'Default Gym', 'is_active': True},
    )

    settings_row = GymSettings.objects.using(alias).order_by('pk').first()
    if settings_row is None:
        GymSettings.objects.using(alias).create(gym_id=gym.pk, name=gym.name)
    else:
        GymSettings.objects.using(alias).filter(pk=settings_row.pk).update(gym_id=gym.pk)
    GymSettings.objects.using(alias).get_or_create(gym_id=gym.pk, defaults={'name': gym.name})

    sms_settings = SMSSettings.objects.using(alias).order_by('pk').first()
    if sms_settings is None:
        SMSSettings.objects.using(alias).create(gym_id=gym.pk)
    else:
        SMSSettings.objects.using(alias).filter(pk=sms_settings.pk).update(gym_id=gym.pk)
    SMSSettings.objects.using(alias).get_or_create(gym_id=gym.pk)

    GymSubscription.objects.using(alias).filter(gym_id__isnull=True).update(gym_id=gym.pk)

    old_pending = 'در انتظار بررسی'
    old_rejected = 'رد شده'
    legacy_rows = GymSubscription.objects.using(alias).filter(
        Q(status__in=(old_pending, old_rejected)) | Q(invoice_image__gt='')
    ).order_by('pk')
    for row in legacy_rows.iterator():
        if row.status == old_pending:
            request_status = old_pending
        elif row.status == old_rejected:
            request_status = old_rejected
        else:
            request_status = 'تأیید شده'
        GymSubscriptionRequest.objects.using(alias).create(
            gym_id=row.gym_id or gym.pk,
            sessions=row.sessions,
            price=row.price,
            invoice_image=row.invoice_image or '',
            status=request_status,
            submitted_at=row.submitted_at,
            reviewed_at=row.reviewed_at,
            reviewed_by_id=row.reviewed_by_id,
            rejection_reason=row.rejection_reason,
            subscription_id=row.pk if request_status == 'تأیید شده' else None,
        )

    GymSubscription.objects.using(alias).filter(status__in=(old_pending, old_rejected)).delete()
    for model in (Coach, GymClass, Member, Expense, Announcement, SMSMessage):
        model.objects.using(alias).filter(gym_id__isnull=True).update(gym_id=gym.pk)
    Profile.objects.using(alias).filter(gym_id__isnull=True).exclude(role='admin').update(gym_id=gym.pk)
    GymSubscriptionRequest.objects.using(alias).filter(gym_id__isnull=True).update(gym_id=gym.pk)

    pending_requests = GymSubscriptionRequest.objects.using(alias).filter(
        status=old_pending,
    ).order_by('gym_id', '-submitted_at', '-pk')
    seen_gyms = set()
    for request in pending_requests.iterator():
        if request.gym_id in seen_gyms:
            GymSubscriptionRequest.objects.using(alias).filter(pk=request.pk).update(
                status=old_rejected,
                reviewed_at=request.submitted_at,
                rejection_reason='Automatically closed during tenancy migration because another pending request existed.',
            )
        else:
            seen_gyms.add(request.gym_id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('gyms', '0004_gym_alter_gymsubscription_options_and_more'),
        ('accounts', '0003_profile_gym'),
        ('classes', '0002_coach_gym_gymclass_gym'),
        ('members', '0002_member_gym'),
        ('notifications', '0003_announcement_gym_smsmessage_gym_smssettings_gym'),
        ('payments', '0004_expense_gym'),
    ]

    operations = [
        migrations.RunPython(backfill_default_gym, noop_reverse),
        migrations.RemoveField(
            model_name='gymsubscription',
            name='invoice_image',
        ),
        migrations.RemoveField(
            model_name='gymsubscription',
            name='rejection_reason',
        ),
        migrations.RemoveField(
            model_name='gymsubscription',
            name='reviewed_at',
        ),
        migrations.RemoveField(
            model_name='gymsubscription',
            name='reviewed_by',
        ),
        migrations.RemoveField(
            model_name='gymsubscription',
            name='submitted_at',
        ),
        migrations.AddConstraint(
            model_name='gymsubscriptionrequest',
            constraint=models.UniqueConstraint(
                fields=('gym',),
                condition=Q(status='در انتظار بررسی'),
                name='one_pending_subscription_request_per_gym',
            ),
        ),
    ]
