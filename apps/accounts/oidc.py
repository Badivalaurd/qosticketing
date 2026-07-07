"""
Backend OIDC Keycloak — authentification SSO pour les utilisateurs métier.
Les comptes génériques (ADMIN, AGENT) continuent d'utiliser le backend local.
"""
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from apps.accounts.models import Department, User


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """
    Mappe les claims Keycloak vers le modèle User Django.
    - Création automatique du compte à la première connexion SSO
    - Rôle par défaut : DEMANDEUR (modifiable depuis l'admin)
    - Mise à jour du nom/prénom à chaque connexion
    """

    def filter_users_by_claims(self, claims):
        email = claims.get('email', '').lower()
        username = claims.get('preferred_username', '')

        if email:
            qs = User.objects.filter(email__iexact=email)
            if qs.exists():
                return qs

        if username:
            qs = User.objects.filter(username=username)
            if qs.exists():
                return qs

        return User.objects.none()

    def create_user(self, claims):
        email = claims.get('email', '')
        username = claims.get('preferred_username') or email.split('@')[0]
        first_name = claims.get('given_name', '')
        last_name = claims.get('family_name', '')

        # Affecter NO-DEPT par défaut — jamais DSI pour les utilisateurs SSO
        try:
            dept = Department.objects.get(code='NO-DEPT')
        except Department.DoesNotExist:
            dept = None

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=User.ROLE_DEMANDEUR,
            department=dept,
        )
        user.set_unusable_password()
        user.save()
        return user

    def update_user(self, user, claims):
        changed = False
        for attr, claim in [('first_name', 'given_name'), ('last_name', 'family_name'), ('email', 'email')]:
            val = claims.get(claim, '')
            if val and getattr(user, attr) != val:
                setattr(user, attr, val)
                changed = True
        if changed:
            user.save(update_fields=['first_name', 'last_name', 'email'])
        return user

