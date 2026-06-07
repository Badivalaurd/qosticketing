from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='LocalCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pg_user_id', models.IntegerField(db_index=True, verbose_name='ID utilisateur (PG)')),
                ('username', models.CharField(max_length=150, unique=True, verbose_name='Identifiant')),
                ('email', models.EmailField(unique=True, verbose_name='Email')),
                ('password_hash', models.CharField(max_length=255, verbose_name='Hash mot de passe')),
                ('full_name', models.CharField(blank=True, max_length=301, verbose_name='Nom complet')),
                ('role', models.CharField(max_length=20, verbose_name='Rôle')),
                ('department_id', models.IntegerField(null=True, verbose_name='Département (ID)')),
                ('department_name', models.CharField(blank=True, max_length=200, verbose_name='Département (nom)')),
                ('department_code', models.CharField(blank=True, max_length=20, verbose_name='Département (code)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Compte actif')),
                ('is_temporary_password', models.BooleanField(default=False, verbose_name='Mot de passe temporaire')),
                ('cached_at', models.DateTimeField(auto_now_add=True, verbose_name='Mis en cache le')),
                ('expires_at', models.DateTimeField(verbose_name='Expire le')),
                ('last_online_check', models.DateTimeField(null=True, verbose_name='Dernier check PG')),
            ],
            options={
                'verbose_name': 'Credential local',
                'verbose_name_plural': 'Credentials locaux',
                'app_label': 'local_auth',
            },
        ),
    ]
