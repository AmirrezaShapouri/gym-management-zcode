from django.db import migrations


def keep_one_settings_record(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    for app_label, model_name in (('gyms', 'GymSettings'), ('notifications', 'SMSSettings')):
        model = apps.get_model(app_label, model_name)
        records = model.objects.using(db_alias).order_by('pk')
        first = records.first()
        if first is None:
            continue
        records.exclude(pk=first.pk).delete()
        if first.pk != 1:
            model.objects.using(db_alias).filter(pk=first.pk).update(pk=1)


class Migration(migrations.Migration):

    dependencies = [
        ('gyms', '0001_initial'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(keep_one_settings_record, migrations.RunPython.noop),
    ]