# Guide de Déploiement — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## 1. Prérequis

| Composant | Version minimale |
|-----------|-----------------|
| Python | 3.11 |
| pip | 23+ |
| Git | 2.40+ |
| Compte PythonAnywhere | Gratuit (test) ou payant (production) |

---

## 2. Déploiement sur PythonAnywhere (mode test — SQLite)

### 2.1 Cloner le dépôt

Depuis la console **Bash** de PythonAnywhere :

```bash
cd ~
git clone https://github.com/votre-org/qos-ticketing.git
cd qos-ticketing
```

### 2.2 Créer l'environnement virtuel

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 Configurer le fichier `.env`

Créer le fichier `.env` à la racine du projet :

```bash
nano .env
```

Contenu minimal pour l'environnement de test :

```ini
SECRET_KEY=votre-cle-secrete-longue-et-aleatoire
DEBUG=False
ALLOWED_HOSTS=votre-username.pythonanywhere.com

# Email (facultatif en test)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-application
DEFAULT_FROM_EMAIL=votre-email@gmail.com

# DB_ENGINE non défini → SQLite automatiquement
```

> **Important :** Ne jamais versionner `.env`. Il est dans `.gitignore`.

### 2.4 Appliquer les migrations et collecter les statiques

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 2.5 Créer le superutilisateur

```bash
python manage.py createsuperuser
```

Suivre les invites : username, email, mot de passe.

### 2.6 Configurer le WSGI dans PythonAnywhere

Dans le tableau de bord PythonAnywhere → **Web** → **Add a new web app** :

- Framework : **Manual configuration**
- Python version : **3.11**

Modifier le fichier WSGI généré (`/var/www/votre-username_pythonanywhere_com_wsgi.py`) :

```python
import os
import sys

# Chemin vers le projet
path = '/home/votre-username/qos-ticketing'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 2.7 Configurer le répertoire statique

Dans **Web** → **Static files** de PythonAnywhere :

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/votre-username/qos-ticketing/staticfiles/` |
| `/media/` | `/home/votre-username/qos-ticketing/media/` |

### 2.8 Configurer le virtualenv

Dans **Web** → **Virtualenv** : saisir le chemin :

```
/home/votre-username/qos-ticketing/venv
```

### 2.9 Recharger l'application

Cliquer le bouton **Reload** vert dans le tableau de bord.

Accéder à : `https://votre-username.pythonanywhere.com`

---

## 3. Mise à jour du déploiement

Après un `git push` sur le dépôt, appliquer les changements :

```bash
cd ~/qos-ticketing
source venv/bin/activate
git pull origin master
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Puis recharger via le tableau de bord PythonAnywhere.

---

## 4. Déploiement en production (PostgreSQL)

### 4.1 Variables d'environnement supplémentaires

Ajouter au `.env` :

```ini
DB_ENGINE=django.db.backends.postgresql
DB_NAME=qos_ticketing
DB_USER=qos_user
DB_PASSWORD=mot-de-passe-db
DB_HOST=localhost
DB_PORT=5432
```

### 4.2 Créer la base PostgreSQL (PythonAnywhere payant)

Dans le tableau de bord → **Databases** → créer une base PostgreSQL.

Utiliser le nom d'hôte fourni par PythonAnywhere pour `DB_HOST`.

### 4.3 Appliquer les migrations PostgreSQL

```bash
python manage.py migrate
```

> Les migrations sont identiques — Django adapte le SQL au moteur configuré.

---

## 5. Déploiement local (développement)

```bash
git clone https://github.com/votre-org/qos-ticketing.git
cd qos-ticketing
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Adapter les valeurs
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Accéder à `http://127.0.0.1:8000`.

---

## 6. Structure des fichiers de configuration importants

| Fichier | Rôle |
|---------|------|
| `config/settings.py` | Paramètres Django (lit `.env`) |
| `config/wsgi.py` | Point d'entrée WSGI |
| `.env` | Variables d'environnement (non versionné) |
| `requirements.txt` | Dépendances Python |
| `staticfiles/` | Statiques collectés par collectstatic |
| `media/` | Uploads utilisateurs |

---

## 7. Commandes utiles en production

```bash
# Vérifier la configuration
python manage.py check --deploy

# Créer une sauvegarde SQLite
cp db.sqlite3 db.sqlite3.bak

# Exporter les données
python manage.py dumpdata --natural-foreign --natural-primary > backup.json

# Importer les données
python manage.py loaddata backup.json

# Vider les sessions expirées
python manage.py clearsessions

# Voir les migrations en attente
python manage.py showmigrations
```

---

## 8. Variables d'environnement — référence complète

| Variable | Obligatoire | Exemple | Description |
|----------|-------------|---------|-------------|
| `SECRET_KEY` | Oui | `abc123...` | Clé secrète Django (64 chars+) |
| `DEBUG` | Non | `False` | Mode debug (False en prod) |
| `ALLOWED_HOSTS` | Oui | `monsite.com` | Hôtes autorisés (virgule si multiples) |
| `DB_ENGINE` | Non | `django.db.backends.postgresql` | Moteur DB (SQLite si absent) |
| `DB_NAME` | Si PostgreSQL | `qos_ticketing` | Nom de la base |
| `DB_USER` | Si PostgreSQL | `qos_user` | Utilisateur DB |
| `DB_PASSWORD` | Si PostgreSQL | `***` | Mot de passe DB |
| `DB_HOST` | Si PostgreSQL | `localhost` | Hôte DB |
| `DB_PORT` | Si PostgreSQL | `5432` | Port DB |
| `EMAIL_HOST` | Non | `smtp.gmail.com` | Serveur SMTP |
| `EMAIL_PORT` | Non | `587` | Port SMTP |
| `EMAIL_HOST_USER` | Non | `user@gmail.com` | Adresse email expéditeur |
| `EMAIL_HOST_PASSWORD` | Non | `***` | Mot de passe applicatif |
| `DEFAULT_FROM_EMAIL` | Non | `user@gmail.com` | Adresse d'expédition par défaut |

---

## 9. Résolution de problèmes fréquents

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Pages CSS/images manquantes | `collectstatic` non exécuté | Relancer `collectstatic` |
| Erreur 500 au démarrage | `SECRET_KEY` ou `ALLOWED_HOSTS` manquant | Vérifier `.env` |
| Emails non envoyés | Mauvaise config SMTP ou mot de passe app | Vérifier paramètres Gmail, activer "Mots de passe d'application" |
| Migrations en conflit | Deux développeurs ont créé des migrations | `python manage.py showmigrations` puis résoudre à la main |
| Fichiers media non servis | Chemin `/media/` non configuré dans PythonAnywhere | Configurer l'entrée Static files |
