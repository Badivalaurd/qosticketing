from django.apps import AppConfig


class LocalAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.local_auth'
    verbose_name = 'Authentification locale'
