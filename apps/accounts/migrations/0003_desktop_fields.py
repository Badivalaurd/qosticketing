from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_department_manager_department_ticketing_enabled'),
    ]

    operations = [
        # Champs desktop sur User
        migrations.AddField(
            model_name='user',
            name='email_confirm_token',
            field=models.CharField(blank=True, db_index=True, max_length=100, verbose_name='Token confirmation email'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_confirm_sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Email de confirmation envoyé le'),
        ),
        # Modèle ApprovedCUID
        migrations.CreateModel(
            name='ApprovedCUID',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cuid', models.CharField(max_length=50, unique=True, verbose_name='CUID professionnel')),
                ('email_hint', models.EmailField(blank=True, help_text="Optionnel — pré-indique l'email attendu pour ce CUID.", verbose_name='Email attendu')),
                ('is_registered', models.BooleanField(default=False, verbose_name='Inscrit')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_cuids', to=settings.AUTH_USER_MODEL, verbose_name='Ajouté par')),
                ('registered_user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_cuid', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'CUID approuvé',
                'verbose_name_plural': 'CUIDs approuvés',
                'ordering': ['cuid'],
            },
        ),
    ]
