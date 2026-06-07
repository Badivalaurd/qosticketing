# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file — QoS Ticketing Desktop
Compile avec : pyinstaller launcher.spec
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

PROJECT_ROOT = Path('.').resolve()

# ── Fichiers de données à inclure dans l'exe ─────────────────────────────────
datas = [
    # Templates Django
    (str(PROJECT_ROOT / 'templates'), 'templates'),
    # Fichiers statiques pré-compilés
    (str(PROJECT_ROOT / 'staticfiles'), 'staticfiles'),
    # Configuration
    (str(PROJECT_ROOT / 'config'), 'config'),
    # Applications
    (str(PROJECT_ROOT / 'apps'), 'apps'),
]

# Ajouter les données des packages Python (DRF, crispy, etc.)
datas += collect_data_files('rest_framework')
datas += collect_data_files('crispy_forms')
datas += collect_data_files('crispy_bootstrap5')
datas += collect_data_files('drf_spectacular')

# ── Imports cachés (Django discovery ne suffit pas en mode frozen) ────────────
hiddenimports = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # DB backends
    'django.db.backends.sqlite3',
    'django.db.backends.postgresql',
    'psycopg2',
    # Apps
    'apps.accounts',
    'apps.tickets',
    'apps.projects',
    'apps.notifications',
    'apps.dashboard',
    'apps.reporting',
    'apps.api',
    'apps.local_auth',
    'apps.local_sync',
    'apps.updater',
    # Third-party
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'whitenoise',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Encoders
    'encodings.utf_8',
    'encodings.ascii',
]

hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('apps')

# ── Analyse ───────────────────────────────────────────────────────────────────
a = Analysis(
    ['launcher.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['celery', 'redis', 'kombu', 'amqp'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Exécutable ────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QoSTicketing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # Pas de fenêtre console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='static/img/icon.ico',  # Décommenter si un .ico est disponible
)
