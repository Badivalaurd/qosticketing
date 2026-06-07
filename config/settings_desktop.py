"""
Paramètres Django — Mode DESKTOP (exécutable Windows).

Hérite de settings.py et surcharge :
- Bases de données multiples (PostgreSQL central + 3 SQLite locaux)
- Routeur de base personnalisé
- Middleware de détection hors-ligne
- Apps supplémentaires (local_auth, local_sync, updater)
- Authentification hybride (SQLite cache → PostgreSQL)
- Domaine d'email autorisé pour l'inscription
"""
import os
from pathlib import Path
from .settings import *  # noqa: F401, F403

# ── Répertoire de données utilisateur (défini par le launcher) ─────────────
_DATA_DIR = Path(os.environ.get('QOS_DATA_DIR', Path.home() / 'AppData' / 'Roaming' / 'QoSTicketing' / 'data'))
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Version de l'application ───────────────────────────────────────────────
APP_VERSION = os.environ.get('QOS_VERSION', '1.1.0')

# ── Domaine email autorisé pour l'inscription ──────────────────────────────
ALLOWED_EMAIL_DOMAIN = os.environ.get('ALLOWED_EMAIL_DOMAIN', '@orange.com')

# ── Durée de validité du cache de credentials (en jours) ──────────────────
LOCAL_AUTH_CACHE_DAYS = int(os.environ.get('LOCAL_AUTH_CACHE_DAYS', '90'))

# ── Bases de données ───────────────────────────────────────────────────────
DATABASES = {
    # Base centrale — PostgreSQL (réseau local)
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'qos_ticketing'),
        'USER': os.environ.get('DB_USER', 'qos_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'qos_secret_2026'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 30,
        'OPTIONS': {
            'connect_timeout': 5,  # Timeout court pour détecter l'indisponibilité
        },
    },

    # SQLite 1 — Cache d'authentification (credentials locaux, 3 mois)
    'auth_local': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DATA_DIR / 'auth.db',
        'OPTIONS': {
            'timeout': 10,
        },
    },

    # SQLite 2 — Tickets en attente de synchronisation (créés hors-ligne)
    'pending': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DATA_DIR / 'tickets_pending.db',
        'OPTIONS': {
            'timeout': 10,
        },
    },

    # SQLite 3 — Cache du listing des tickets (consultation hors-ligne)
    'cache': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _DATA_DIR / 'tickets_cache.db',
        'OPTIONS': {
            'timeout': 10,
        },
    },
}

DATABASE_ROUTERS = ['config.db_router.DesktopDBRouter']

# ── Applications supplémentaires ───────────────────────────────────────────
INSTALLED_APPS = [app for app in INSTALLED_APPS] + [  # noqa: F405
    'apps.local_auth',
    'apps.local_sync',
    'apps.updater',
]

# ── Middleware ─────────────────────────────────────────────────────────────
# Insérer le middleware de détection hors-ligne juste après SecurityMiddleware
_mw = list(MIDDLEWARE)  # noqa: F405
_security_idx = next(
    (i for i, m in enumerate(_mw) if 'SecurityMiddleware' in m), 0
)
_mw.insert(_security_idx + 1, 'apps.local_sync.middleware.OfflineDetectionMiddleware')
MIDDLEWARE = _mw

# ── Authentification hybride ───────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.HybridAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ── Sécurité ───────────────────────────────────────────────────────────────
# En mode desktop, l'app tourne sur localhost — pas besoin d'HTTPS forcé
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Session longue en mode desktop (1 semaine)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7

# ── Context processors ────────────────────────────────────────────────────────
# Ajouter le context processor hors-ligne à la liste existante
for _tpl in TEMPLATES:  # noqa: F405
    if _tpl.get('BACKEND') == 'django.template.backends.django.DjangoTemplates':
        _tpl['OPTIONS']['context_processors'].append(
            'apps.local_sync.context_processors.offline_status'
        )

# ── Email ──────────────────────────────────────────────────────────────────
# Hérite de settings.py (SMTP Gmail)
# Ajouter ici des surcharges si nécessaire

# ── Logging desktop ────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': str(_DATA_DIR / 'qos_ticketing.log'),
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'apps.local_sync': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.updater': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
