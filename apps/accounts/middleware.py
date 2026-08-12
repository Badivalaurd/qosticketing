"""
Middlewares du module accounts.

SessionInactivityMiddleware — déconnecte après SESSION_INACTIVITY_TIMEOUT secondes d'inactivité.
DepartmentRequiredMiddleware — redirige vers le choix de département si l'utilisateur n'en a pas.
"""
import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

_TIMEOUT = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 7200)  # 2h par défaut
_SESSION_KEY = '_last_activity'

# URL de sélection du département
_CHOOSE_DEPT_URL = '/accounts/setup/department/'

# Préfixes exemptés du contrôle "département requis"
_DEPT_EXEMPT_PREFIXES = (
    _CHOOSE_DEPT_URL,
    '/accounts/logout/',
    '/accounts/login/',
    '/accounts/password/',
    '/accounts/login/magic',  # magic-login flow
    '/oidc/',                 # Keycloak callbacks
    '/static/',
    '/media/',
    '/admin/',
)


class SessionInactivityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        now = time.time()
        last = request.session.get(_SESSION_KEY)

        if last and (now - last) > _TIMEOUT:
            logout(request)
            return HttpResponseRedirect(settings.LOGIN_URL + '?expired=1')

        request.session[_SESSION_KEY] = now

        # ── Département requis ──────────────────────────────────────────────
        # Si l'utilisateur connecté n'a pas encore de département, le rediriger
        # vers la page de sélection (sauf sur les URLs exemptées).
        if request.user.department_id is None:
            path = request.path
            if not any(path.startswith(prefix) for prefix in _DEPT_EXEMPT_PREFIXES):
                dest = _CHOOSE_DEPT_URL
                if path not in ('/', '/dashboard/'):
                    dest += f'?next={path}'
                return HttpResponseRedirect(dest)

        return None
