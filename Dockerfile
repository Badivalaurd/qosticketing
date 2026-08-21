# ══════════════════════════════════════════════════════════════════════════════
# ITTIS — Dockerfile (production)
# Compatible OpenShift Local (CRC) : utilisateur non-root arbitraire
# Base de données : MariaDB externe
# ══════════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système (MariaDB client + gcc pour compiler mysqlclient)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Code source
COPY . .

# Collecte des fichiers statiques (nécessite SECRET_KEY au build)
RUN SECRET_KEY=build-placeholder-key \
    DB_ENGINE=django.db.backends.sqlite3 \
    DB_NAME=/tmp/build.db \
    python manage.py collectstatic --noinput

# ── OpenShift : permissions pour utilisateur arbitraire non-root ──────────────
# OpenShift exécute les conteneurs avec un UID aléatoire du namespace.
# On donne les droits sur /app et /app/media au groupe root (GID 0).
RUN mkdir -p /app/media /app/logs && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

USER 1001

EXPOSE 8000

# Gunicorn — 3 workers, timeout 120s
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
