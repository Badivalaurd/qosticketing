from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('version', models.CharField(max_length=20, verbose_name='Version')),
                ('release_notes', models.TextField(blank=True, verbose_name='Notes de version')),
                ('download_url', models.URLField(help_text='Lien SharePoint vers le nouvel exécutable.', verbose_name='URL de téléchargement')),
                ('min_required_version', models.CharField(help_text='Les clients dont la version est inférieure seront bloqués.', max_length=20, verbose_name='Version minimale requise')),
                ('is_forced', models.BooleanField(default=True, help_text="Si activé, les anciens clients ne peuvent plus utiliser l'app.", verbose_name='Mise à jour forcée')),
                ('released_at', models.DateTimeField(auto_now_add=True, verbose_name='Publiée le')),
                ('released_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='app_versions', to=settings.AUTH_USER_MODEL, verbose_name='Publié par')),
            ],
            options={
                'verbose_name': 'Version applicative',
                'verbose_name_plural': 'Versions applicatives',
                'ordering': ['-released_at'],
            },
        ),
    ]
