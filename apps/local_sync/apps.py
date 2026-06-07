from django.apps import AppConfig


class LocalSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.local_sync'
    verbose_name = 'Synchronisation hors-ligne'

    def ready(self):
        from apps.local_sync import sync_service  # noqa: F401 — démarre le scheduler
