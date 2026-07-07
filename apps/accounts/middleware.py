"""
Middleware d'expiration de session par inactivité.
Déconnecte l'utilisateur après SESSION_INACTIVITY_TIMEOUT secondes sans activité.
"""
import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

_TIMEOUT = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 7200)  # 2h par défaut
_SESSION_KEY = '_last_activity'


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
        return None
