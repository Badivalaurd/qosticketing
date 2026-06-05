#!/bin/bash
# ============================================================
# QoS Ticketing — Script de déploiement PythonAnywhere
# À exécuter dans la console Bash de PythonAnywhere
# ============================================================

set -e

APP_NAME="qosticket"        # Ton username PythonAnywhere
REPO_URL="REMPLACER_PAR_URL_GIT"   # ex: https://github.com/ton-user/qos-ticketing.git
PROJECT_DIR="/home/$APP_NAME/qos_ticketing"
VENV_DIR="/home/$APP_NAME/venv_qos"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo ""
echo "========================================"
echo "  QoS Ticketing — Déploiement"
echo "========================================"
echo ""

# 1. Cloner ou mettre à jour le dépôt
if [ -d "$PROJECT_DIR" ]; then
    echo "[1/7] Mise à jour du code..."
    cd "$PROJECT_DIR" && git pull origin main
else
    echo "[1/7] Clonage du dépôt..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 2. Créer le virtualenv si inexistant
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/7] Création du virtualenv Python 3.10..."
    python3.10 -m venv "$VENV_DIR"
fi

# 3. Installer les dépendances
echo "[3/7] Installation des dépendances..."
$PIP install --upgrade pip -q
$PIP install -r "$PROJECT_DIR/requirements.txt" -q

# 4. Copier le fichier .env de production
echo "[4/7] Vérification du fichier .env..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "  ATTENTION : Copie .env.production → .env"
    cp "$PROJECT_DIR/.env.production" "$PROJECT_DIR/.env"
    echo "  !! Édite $PROJECT_DIR/.env avec tes vraies valeurs !!"
fi

# 5. Migrations
echo "[5/7] Application des migrations..."
cd "$PROJECT_DIR"
$PYTHON manage.py migrate --noinput

# 6. Collecte des fichiers statiques
echo "[6/7] Collecte des fichiers statiques..."
$PYTHON manage.py collectstatic --noinput --clear -v 0

# 7. Données initiales (seulement si nouvelle installation)
if [ "$1" == "--init" ]; then
    echo "[7/7] Chargement des données initiales..."
    $PYTHON setup_initial_data.py
else
    echo "[7/7] Données initiales ignorées (passe --init pour les charger)"
fi

echo ""
echo "========================================"
echo "  Déploiement terminé !"
echo "  → Va dans l'onglet Web de PythonAnywhere"
echo "  → Clique sur 'Reload' pour appliquer"
echo "========================================"
