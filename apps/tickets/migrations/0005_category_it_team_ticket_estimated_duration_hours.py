from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_add_is_placeholder_to_department'),
        ('tickets', '0004_title_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='it_team',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='category_team',
                to='accounts.department',
                verbose_name='Sous-département IT responsable',
            ),
        ),
        migrations.AddField(
            model_name='ticket',
            name='estimated_duration_hours',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Durée estimée (heures)',
                help_text='Durée estimative de traitement. Modifiable par agent de support et manager uniquement.',
            ),
        ),
    ]
