import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='member',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='members.member',
                verbose_name='عضو',
            ),
        ),
    ]