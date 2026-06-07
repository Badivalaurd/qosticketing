"""
Vérification de version au démarrage et middleware de blocage.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def check_update_required(current_version: str = None) -> dict:
    """
    Interroge PostgreSQL pour connaître la dernière version.
    Retourne un dict :
      { 'update_required': bool, 'latest_version': str, 'download_url': str, 'release_notes': str }
    """
    if current_version is None:
        current_version = getattr(settings, 'APP_VERSION', '1.0.0')

    result = {
        'update_required': False,
        'latest_version': current_version,
        'download_url': '',
        'release_notes': '',
    }

    try:
        from config.db_availability import is_postgres_available
        if not is_postgres_available():
            return result

        from apps.updater.models import AppVersion
        latest = AppVersion.get_latest()
        if latest is None:
            return result

        result['latest_version'] = latest.version
        result['download_url'] = latest.download_url
        result['release_notes'] = latest.release_notes

        if latest.is_forced and latest.requires_update(current_version):
            result['update_required'] = True
            logger.warning(
                "Mise à jour requise : version actuelle %s, minimale requise %s",
                current_version, latest.min_required_version
            )

    except Exception as exc:
        logger.debug("Vérification version impossible : %s", exc)

    return result


class UpdateCheckMiddleware:
    """
    Bloque toutes les requêtes (sauf /update/ et /static/) si une mise à jour
    forcée est disponible et que la version courante est obsolète.
    """

    EXEMPT_PATHS = ['/update/', '/static/', '/media/', '/accounts/logout/']

    def __init__(self, get_response):
        self.get_response = get_response
        self._update_status = None

    def __call__(self, request):
        if not self._is_exempt(request.path):
            status = self._get_update_status()
            if status.get('update_required'):
                from django.shortcuts import render
                return render(request, 'updater/update_required.html', {
                    'latest_version': status['latest_version'],
                    'download_url': status['download_url'],
                    'release_notes': status['release_notes'],
                }, status=503)

        return self.get_response(request)

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.EXEMPT_PATHS)

    def _get_update_status(self) -> dict:
        # Mis en cache pour ne pas requêter PG à chaque hit
        import time
        now = time.monotonic()
        if self._update_status is None or now - self._update_status.get('_ts', 0) > 300:
            status = check_update_required()
            status['_ts'] = now
            self._update_status = status
        return self._update_status
