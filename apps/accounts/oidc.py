"""
Backend OIDC Keycloak — authentification SSO pour les utilisateurs métier.
Les comptes génériques (ADMIN, AGENT) continuent d'utiliser le backend local.
"""
import requests
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect

from apps.accounts.models import Department, User


class SafeOIDCCallbackView(OIDCAuthenticationCallbackView):
    """Capture les erreurs de connexion Keycloak et affiche un message clair."""

    def get(self, request):
        try:
            return super().get(request)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        ):
            messages.error(
                request,
                "Le serveur SSO (Keycloak) est temporairement indisponible. "
                "Utilisez la connexion par code email ci-dessous."
            )
            return redirect('/accounts/login/?fallback=1')
        except SuspiciousOperation:
            messages.error(
                request,
                "Session SSO expirée ou invalide. "
                "Utilisez la connexion par identifiant/mot de passe ou le code email."
            )
            return redirect('/accounts/login/?fallback=1')
        except Exception as exc:
            err = str(exc)
            if any(k in err for k in ('Token', '403', '401', 'OIDC')):
                messages.error(
                    request,
                    "La connexion SSO a échoué. "
                    "Utilisez la connexion par identifiant/mot de passe ou le code email."
                )
                return redirect('/accounts/login/?fallback=1')
            raise


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """
    Mappe les claims Keycloak vers le modèle User Django.
    - Création automatique du compte à la première connexion SSO
    - Rôle par défaut : DEMANDEUR (modifiable depuis l'admin)
    - Mise à jour du nom/prénom à chaque connexion
    """

    def filter_users_by_claims(self, claims):
        # preferred_username = CUID, toujours unique dans Django → priorité absolue
        username = claims.get('preferred_username', '')
        if username:
            qs = User.objects.filter(username=username)
            if qs.exists():
                return qs

        # Fallback email — limité à 1 pour éviter "Multiple users returned"
        # (des comptes dupliqués peuvent avoir le même email)
        email = claims.get('email', '').lower()
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                return User.objects.filter(pk=user.pk)

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

