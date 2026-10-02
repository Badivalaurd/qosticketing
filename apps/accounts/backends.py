"""
Backend d'authentification local pour la connexion par identifiant/mot de passe.

Règles :
- Superuser et staff (admin_omcm, agent_omcm) : connexion normale, sans restriction.
- Tous les autres utilisateurs : connexion par mot de passe uniquement si un mot de
  passe temporaire a été défini par un administrateur (temp_password_expires_at renseigné)
  et qu'il n'a pas encore expiré.
- À l'expiration, le mot de passe est automatiquement rendu inutilisable.
"""
import logging

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone

logger = logging.getLogger(__name__)


class LocalPasswordBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is None:
            return None

        # Admin et agent permanents — pas de restriction
        if user.is_superuser or user.is_staff:
            logger.info("[AUTH OK] Connexion locale staff : %s", user.username)
            return user

        # Utilisateurs normaux : exige un mot de passe temporaire actif
        expires = user.temp_password_expires_at
        if not expires:
            logger.warning(
                "[AUTH BLOQUE] Connexion locale refusée (aucun MDP temporaire) : %s",
                user.username,
            )
            return None

        if timezone.now() > expires:
            user.set_unusable_password()
            user.temp_password_expires_at = None
            user.save(update_fields=['password', 'temp_password_expires_at'])
            logger.warning(
                "[AUTH BLOQUE] MDP temporaire expiré et invalidé : %s", user.username
            )
            return None

        logger.info(
            "[AUTH OK] Connexion locale MDP temporaire : %s (expire %s)",
            user.username,
            expires.strftime('%H:%M'),
        )
        return user
