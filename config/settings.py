from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'mozilla_django_oidc',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'rest_framework',
    'drf_spectacular',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'import_export',
    # Local apps
    'apps.accounts',
    'apps.tickets',
    'apps.projects',
    'apps.notifications',
    'apps.knowledge_base',
    'apps.dashboard',
    'apps.reporting',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.accounts.middleware.SessionInactivityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Déconnexion automatique après 2h d'inactivité
SESSION_INACTIVITY_TIMEOUT = 7200  # secondes

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.notifications.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
# SQLite — désactivé (remplacé par PostgreSQL via Docker)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

_DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')
_DB_OPTIONS = {}
if 'postgresql' in _DB_ENGINE:
    _DB_OPTIONS = {'sslmode': os.getenv('DB_SSLMODE', 'disable')}
elif 'mysql' in _DB_ENGINE:
    _DB_OPTIONS = {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"}

DATABASES = {
    'default': {
        'ENGINE': _DB_ENGINE,
        'NAME': os.getenv('DB_NAME', 'qos_ticketing'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': _DB_OPTIONS,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'apps.accounts.oidc.KeycloakOIDCBackend',
]

from django.contrib.messages import constants as _msg
MESSAGE_TAGS = {_msg.ERROR: 'danger'}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# django-allauth (v65+)
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'apps.accounts.permissions.IsAdminRole',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'QoS Ticketing API',
    'DESCRIPTION': 'API de gestion des tickets, incidents et évolutions',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Email — Relay SMTP interne (sans authentification)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '172.26.76.151')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 25))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'QoS Ticketing <no-reply.extraction@orange.com>')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', 'no-reply.extraction@orange.com')

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# SLA hours by priority
SLA_HOURS = {
    'CRITIQUE': 4,
    'HAUTE': 8,
    'MOYENNE': 24,
    'FAIBLE': 72,
}

# ── Keycloak / OIDC ────────────────────────────────────────────────────────────
_KC_BASE  = os.getenv('OIDC_KEYCLOAK_URL',   'http://keycloak.adcm.orangecm/auth')
_KC_REALM = os.getenv('OIDC_KEYCLOAK_REALM', 'digital-app')
_KC_PROTO = f"{_KC_BASE}/realms/{_KC_REALM}/protocol/openid-connect"

OIDC_RP_CLIENT_ID     = os.getenv('OIDC_RP_CLIENT_ID',     'qos-ticketing')
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET', '')
OIDC_RP_SIGN_ALGO     = 'RS256'
OIDC_RP_SCOPES        = 'openid email profile'

OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_KC_PROTO}/auth"
OIDC_OP_TOKEN_ENDPOINT         = f"{_KC_PROTO}/token"
OIDC_OP_USER_ENDPOINT          = f"{_KC_PROTO}/userinfo"
OIDC_OP_JWKS_ENDPOINT          = f"{_KC_PROTO}/certs"
OIDC_OP_LOGOUT_ENDPOINT        = f"{_KC_PROTO}/logout"

OIDC_REDIRECT_OK_FIELD_NAME    = 'next'
OIDC_REDIRECT_FIELD_NAME       = 'next'
OIDC_STORE_ID_TOKEN            = True
LOGIN_REDIRECT_URL_FAILURE     = '/accounts/login/'

# ── Logging ────────────────────────────────────────────────────────────────────
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '\033[36m{asctime}\033[0m [{levelname}] {name} | {message}',
            'style': '{',
            'datefmt': '%H:%M:%S',
        },
        'file': {
            'format': '{asctime} [{levelname}] {name} | user={user} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'defaults': {'user': 'system'},
        },
    },
    'filters': [],
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'daily_global': {
            '()': 'apps.accounts.log_handlers.DailyFileHandler',
            'log_dir': str(LOGS_DIR),
            'formatter': 'file',
        },
        'daily_user': {
            '()': 'apps.accounts.log_handlers.UserDailyFileHandler',
            'log_dir': str(LOGS_DIR),
            'formatter': 'file',
        },
    },
    'loggers': {
        'mozilla_django_oidc': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'daily_global', 'daily_user'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'daily_global'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'daily_global'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
