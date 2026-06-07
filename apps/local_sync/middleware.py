"""
Middleware de détection hors-ligne et de contrôle de blocage.

Rôles :
  1. Injecte `request.pg_available` à chaque requête
  2. Vérifie si l'utilisateur connecté est bloqué (via credential local)
  3. Si bloqué → déconnecte et redirige vers login
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse


class OfflineDetectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from config.db_availability import is_postgres_available

        # Disponibilité PG accessible dans toutes les vues et templates
        request.pg_available = is_postgres_available()

        # Vérification blocage utilisateur connecté
        if request.user.is_authenticated:
            self._check_user_block(request)

        response = self.get_response(request)
        return response

    def _check_user_block(self, request):
        """
        Si PG disponible → vérifier en direct.
        Sinon → vérifier dans le credential local.
        Les deux ont pu être mis à jour par le SyncService.
        """
        try:
            from apps.local_auth.models import LocalCredential
            try:
                cred = LocalCredential.objects.using('auth_local').get(
                    pg_user_id=request.user.pk
                )
                if not cred.is_active:
                    logout(request)
                    messages.error(
                        request,
                        "Votre compte a été désactivé. Contactez l'administrateur."
                    )
                    # Rediriger sauf si déjà sur login
                    login_url = reverse('account_login')
                    if request.path != login_url:
                        request.META['_force_redirect'] = login_url
            except LocalCredential.DoesNotExist:
                pass
        except Exception:
            pass

    def process_view(self, request, view_func, view_args, view_kwargs):
        redirect_url = request.META.pop('_force_redirect', None)
        if redirect_url:
            return redirect(redirect_url)
        return None
