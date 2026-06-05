from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='sla_warning_1h_sent',
            field=models.BooleanField(default=False, verbose_name='Alerte SLA 1h envoyée'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='sla_warning_30m_sent',
            field=models.BooleanField(default=False, verbose_name='Alerte SLA 30min envoyée'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='sla_warning_10m_sent',
            field=models.BooleanField(default=False, verbose_name='Alerte SLA 10min envoyée'),
        ),
    ]
