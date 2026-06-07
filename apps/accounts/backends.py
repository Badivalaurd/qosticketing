"""
Backend d'authentification hybride : SQLite local → PostgreSQL.

Priorité :
  1. Si PG disponible → authentifier via PG, mettre à jour le cache local
  2. Si PG indisponible → authentifier via cache local (si non expiré)

Blocage :
  - PG disponible : vérification en direct de is_active
  - PG indisponible : vérification du flag is_active dans le credential local
    (mis à jour par le SyncService en arrière-plan)
"""
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

logger = logging.getLogger(__name__)
User = get_user_model()


class HybridAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        from config.db_availability import is_postgres_available

        if is_postgres_available():
            return self._auth_via_postgres(username, password)
        else:
            return self._auth_via_local_cache(username, password)

    # ------------------------------------------------------------------
    # Authentification en ligne (PostgreSQL)
    # ------------------------------------------------------------------
    def _auth_via_postgres(self, username: str, password: str):
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            return None

        if not user.is_active:
            return None

        if not user.check_password(password):
            return None

        # Mise à jour du cache local
        try:
            from apps.local_auth.models import LocalCredential
            LocalCredential.update_from_pg_user(user, raw_password=password)
        except Exception as exc:
            logger.warning("Impossible de mettre à jour le cache local : %s", exc)

        return user

    # ------------------------------------------------------------------
    # Authentification hors-ligne (SQLite cache)
    # ------------------------------------------------------------------
    def _auth_via_local_cache(self, username: str, password: str):
        try:
            from apps.local_auth.models import LocalCredential
            cred = LocalCredential.objects.using('auth_local').get(
                Q(username=username) | Q(email=username)
            )
        except Exception:
            return None

        if not cred.is_active:
            logger.info("Compte bloqué localement : %s", username)
            return None

        if cred.is_expired():
            logger.info("Cache local expiré pour : %s", username)
            return None

        if not cred.check_password(password):
            return None

        # Retourner un objet User synthétique (ou charger depuis PG si possible)
        return self._build_offline_user(cred)

    def _build_offline_user(self, cred):
        """
        Retourne un objet User minimal pour la session hors-ligne.
        Si PG redevient disponible avant la fin de session, les données
        seront rechargées normalement.
        """
        try:
            # Tenter de charger le vrai objet (si PG est revenu entre-temps)
            user = User.objects.get(pk=cred.pg_user_id)
            return user if user.is_active else None
        except Exception:
            pass

        # Construire un User non-persisté pour la session hors-ligne
        user = User(
            pk=cred.pg_user_id,
            username=cred.username,
            email=cred.email,
            first_name=cred.full_name.split(' ')[0] if cred.full_name else '',
            last_name=' '.join(cred.full_name.split(' ')[1:]) if cred.full_name else '',
            role=cred.role,
            is_active=True,
        )
        user._is_offline_user = True
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
