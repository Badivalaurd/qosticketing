"""
Modèles stockés dans la base SQLite locale `auth_local`.

LocalCredential : cache chiffré des identifiants de connexion.
Durée de validité : 3 mois (configurable via LOCAL_AUTH_CACHE_DAYS).
"""
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check
from django.utils import timezone
from datetime import timedelta


class LocalCredential(models.Model):
    """Cache local des identifiants d'un utilisateur."""

    # Identifiants PostgreSQL de référence
    pg_user_id = models.IntegerField('ID utilisateur (PG)', db_index=True)
    username = models.CharField('Identifiant', max_length=150, unique=True)
    email = models.EmailField('Email', unique=True)
    password_hash = models.CharField('Hash mot de passe', max_length=255)

    # Informations de profil (dupliquées pour le mode hors-ligne)
    full_name = models.CharField('Nom complet', max_length=301, blank=True)
    role = models.CharField('Rôle', max_length=20)
    department_id = models.IntegerField('Département (ID)', null=True)
    department_name = models.CharField('Département (nom)', max_length=200, blank=True)
    department_code = models.CharField('Département (code)', max_length=20, blank=True)

    # Flags
    is_active = models.BooleanField('Compte actif', default=True)
    is_temporary_password = models.BooleanField('Mot de passe temporaire', default=False)

    # Cycle de vie du cache
    cached_at = models.DateTimeField('Mis en cache le', auto_now_add=True)
    expires_at = models.DateTimeField('Expire le')
    last_online_check = models.DateTimeField('Dernier check PG', null=True)

    class Meta:
        app_label = 'local_auth'
        verbose_name = 'Credential local'
        verbose_name_plural = 'Credentials locaux'

    def __str__(self):
        return f"{self.username} (expire {self.expires_at:%d/%m/%Y})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            from django.conf import settings
            days = getattr(settings, 'LOCAL_AUTH_CACHE_DAYS', 90)
            self.expires_at = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def set_password(self, raw_password: str):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return django_check(raw_password, self.password_hash)

    def renew(self):
        """Renouvelle l'expiration à partir d'aujourd'hui."""
        from django.conf import settings
        days = getattr(settings, 'LOCAL_AUTH_CACHE_DAYS', 90)
        self.expires_at = timezone.now() + timedelta(days=days)
        self.cached_at = timezone.now()

    @classmethod
    def update_from_pg_user(cls, pg_user, raw_password: str = None):
        """
        Crée ou met à jour le credential local depuis un objet User PostgreSQL.
        Si raw_password est fourni, met à jour le hash.
        """
        obj, created = cls.objects.using('auth_local').get_or_create(
            username=pg_user.username,
            defaults={
                'pg_user_id': pg_user.pk,
                'email': pg_user.email,
                'full_name': pg_user.get_full_name(),
                'role': pg_user.role,
                'department_id': pg_user.department_id,
                'department_name': pg_user.department.name if pg_user.department else '',
                'department_code': pg_user.department.code if pg_user.department else '',
                'is_active': pg_user.is_active,
            }
        )
        if not created:
            obj.email = pg_user.email
            obj.full_name = pg_user.get_full_name()
            obj.role = pg_user.role
            obj.department_id = pg_user.department_id
            obj.department_name = pg_user.department.name if pg_user.department else ''
            obj.department_code = pg_user.department.code if pg_user.department else ''
            obj.is_active = pg_user.is_active
            obj.renew()

        if raw_password:
            obj.set_password(raw_password)

        obj.last_online_check = timezone.now()
        obj.save(using='auth_local')
        return obj
