"""
Utilitaire de vérification de la disponibilité de la base PostgreSQL.
Utilisé par le router et les vues pour décider du mode de fonctionnement.
"""
import threading
import time
import logging

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_cache = {
    'available': None,
    'last_checked': 0,
}

# Intervalle de re-check en secondes
CHECK_INTERVAL = 30


def is_postgres_available(force: bool = False) -> bool:
    """
    Retourne True si la base PostgreSQL centrale est joignable.
    Résultat mis en cache 30 secondes pour éviter de bloquer chaque requête.
    """
    now = time.monotonic()
    with _lock:
        if not force and _cache['available'] is not None:
            if now - _cache['last_checked'] < CHECK_INTERVAL:
                return _cache['available']
        result = _check_postgres()
        _cache['available'] = result
        _cache['last_checked'] = now
        return result


def _check_postgres() -> bool:
    """Tente une connexion réelle à PostgreSQL."""
    try:
        from django.db import connections
        conn = connections['default']
        conn.ensure_connection()
        return True
    except Exception as exc:
        logger.debug("PostgreSQL indisponible : %s", exc)
        return False


def invalidate_cache():
    """Force le prochain appel à re-checker la connexion."""
    with _lock:
        _cache['last_checked'] = 0
