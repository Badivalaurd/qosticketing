#!/usr/bin/env bash
set -e

echo "==> [1/3] Migrations..."
python manage.py migrate --no-input

echo "==> [2/3] Initialisation des données..."
python manage.py init_prod || echo "WARN: init_prod a échoué (données déjà présentes ou erreur non bloquante)"

echo "==> [3/3] Démarrage gunicorn sur port ${PORT}..."
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
