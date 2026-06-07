import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PendingTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('local_id', models.CharField(default=lambda: str(uuid.uuid4()), max_length=36, unique=True, verbose_name='ID local')),
                ('user_id', models.IntegerField(verbose_name='ID utilisateur (PG)')),
                ('username', models.CharField(max_length=150, verbose_name='Identifiant')),
                ('department_id', models.IntegerField(null=True, verbose_name='Département demandeur (ID)')),
                ('target_department_id', models.IntegerField(null=True, verbose_name='Département cible (ID)')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('description', models.TextField(verbose_name='Description')),
                ('priority', models.CharField(default='P2', max_length=5, verbose_name='Priorité')),
                ('category_id', models.IntegerField(null=True, verbose_name='Catégorie (ID)')),
                ('sync_status', models.CharField(choices=[('PENDING', 'En attente'), ('SYNCED', 'Synchronisé'), ('FAILED', 'Échec'), ('CANCELLED', 'Annulé')], default='PENDING', max_length=20, verbose_name='Statut sync')),
                ('created_at_local', models.DateTimeField(auto_now_add=True, verbose_name='Créé localement le')),
                ('synced_at', models.DateTimeField(null=True, verbose_name='Synchronisé le')),
                ('pg_ticket_number', models.CharField(blank=True, max_length=30, verbose_name='Référence PG')),
                ('error_message', models.TextField(blank=True, verbose_name='Erreur de sync')),
                ('retry_count', models.IntegerField(default=0, verbose_name='Tentatives')),
            ],
            options={
                'verbose_name': 'Ticket en attente',
                'verbose_name_plural': 'Tickets en attente',
                'ordering': ['created_at_local'],
                'app_label': 'local_sync',
            },
        ),
        migrations.CreateModel(
            name='CachedTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('ticket_number', models.CharField(max_length=30, unique=True, verbose_name='Référence')),
                ('user_id', models.IntegerField(verbose_name='Propriétaire du cache')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('status', models.CharField(max_length=30, verbose_name='Statut')),
                ('priority', models.CharField(max_length=5, verbose_name='Priorité')),
                ('created_by_name', models.CharField(blank=True, max_length=301, verbose_name='Demandeur')),
                ('assigned_to_name', models.CharField(blank=True, max_length=301, verbose_name='Assigné à')),
                ('department_name', models.CharField(blank=True, max_length=200, verbose_name='Département')),
                ('created_at', models.DateTimeField(verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(verbose_name='Modifié le')),
                ('cached_at', models.DateTimeField(auto_now=True, verbose_name='Mis en cache le')),
            ],
            options={
                'verbose_name': 'Ticket en cache',
                'verbose_name_plural': 'Tickets en cache',
                'ordering': ['-updated_at'],
                'app_label': 'local_sync',
            },
        ),
    ]
