# Architecture Système — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## 1. Vue d'ensemble

QoS Ticketing est une application web monolithique basée sur le framework **Django 5.x**. Elle suit l'architecture MVT (Model-View-Template) de Django.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Navigateur Web                           │
│                   (Chrome, Firefox, Edge)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────────┐
│                    Serveur Web / WSGI                           │
│        PythonAnywhere (Gunicorn) | Dev: Django runserver        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  Application Django 5.x                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ accounts │ │ tickets  │ │ projects │ │  notifications   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │dashboard │ │reporting │ │    api   │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌───────▼──────┐ ┌─────▼──────────┐
│   Base de      │ │   Fichiers   │ │   Email SMTP   │
│   données      │ │   statiques  │ │  (Gmail SMTP)  │
│  SQLite (dev)  │ │  Whitenoise  │ └────────────────┘
│ PostgreSQL(prd)│ └──────────────┘
└────────────────┘
```

---

## 2. Stack technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.11+ |
| Framework web | Django | 5.1.x |
| ORM | Django ORM | — |
| Base de données (dev/test) | SQLite | 3.x |
| Base de données (production) | PostgreSQL | 15+ |
| Serveur WSGI | Gunicorn (PythonAnywhere) | — |
| Fichiers statiques | Whitenoise | 6.7+ |
| API REST | Django REST Framework | 3.15+ |
| Documentation API | drf-spectacular | 0.27+ |
| Filtres API | django-filter | 24.0+ |
| Traitement d'images | Pillow | 10.0+ |
| Export Excel | openpyxl | 3.1+ |
| Export PDF | reportlab | 4.2+ |
| Formulaires | django-crispy-forms + crispy-bootstrap5 | — |
| Authentification sociale | django-allauth | 65.0+ |
| Import/Export admin | django-import-export | 4.1+ |
| Variables d'environnement | python-dotenv | 1.0+ |
| QR Code | qrcode | 7.4+ |
| Tâches asynchrones | Celery + Redis | 5.4+ (optionnel) |
| Frontend | Bootstrap 5.3 + Bootstrap Icons | — |

---

## 3. Structure des applications Django

```
config/               # Configuration projet
├── settings.py       # Paramètres (env-driven)
├── urls.py           # Routage principal
├── wsgi.py           # Point d'entrée WSGI
└── celery.py         # Config Celery (optionnel)

apps/
├── accounts/         # Utilisateurs, rôles, départements
├── tickets/          # Cœur métier — tickets, SLA, historique
├── projects/         # Projets IT (sprints, épics, tâches)
├── notifications/    # Notifications in-app et emails
├── dashboard/        # Tableau de bord KPIs
├── reporting/        # Exports CSV/Excel, statistiques
├── knowledge_base/   # Base de connaissance
└── api/              # API REST (DRF)

templates/            # Templates HTML (Django templates)
static/               # CSS, JS, images statiques
media/                # Fichiers uploadés (avatars, pièces jointes)
```

---

## 4. Modèle de données — relations principales

```
Department ──────────────────────────────────────────────────────┐
  │ is_it_department (bool)                                       │
  │ ticketing_enabled (bool)                                      │
  │ manager → User (FK, nullable)                                 │
  └─────────────────────────────────────────────────────────────┐ │
                                                                │ │
User ──────────────────────────────────────────────────────┐   │ │
  │ role (Admin|Manager|Agent|Technicien|Demandeur|Observ.) │   │ │
  │ department → Department (FK)                             │   │ │
  └──────────────────────────────────────────────────────┐  │   │ │
                                                         │  │   │ │
Ticket ───────────────────────────────────────────────── │  │   │ │
  │ number (unique, auto)                                │  │   │ │
  │ status (9 valeurs)                                  │  │   │ │
  │ priority (P0-P3)                                    │  │   │ │
  │ created_by → User                                   │──┘  │ │
  │ assigned_to → User (nullable)                       │─────┘ │
  │ responsable → User (nullable, ball-in-court)        │       │
  │ info_requested_from → User (nullable)               │       │
  │ department → Department (demandeur)                 │───────┘
  │ target_department → Department (receveur)           │
  │ category → Category                                 │
  │ project → Project (nullable)                        │
  │ sla_* (champs SLA)                                  │
  └─────────────────────────────────────────────────────┘
       │
       ├── Comment (1..N)
       ├── Attachment (1..N)
       └── TicketHistory (1..N)
```

---

## 5. Flux de traitement d'un ticket standard

```
Demandeur crée ticket
        │
        ▼
  [NOUVEAU] ─── Agent/Admin reçoit notification
        │
        │ Agent affecte (ou Technicien prend en charge)
        ▼
  [AFFECTÉ] ─── SLA réinitialisé
        │
        │ Technicien commence
        ▼
  [EN COURS] ──────────────────┐
        │                      │ Demande info
        │                      ▼
        │               [ATTENTE INFO] ─── SLA pausé
        │                      │ Réponse fournie
        │                      │ SLA repris
        │◄──────────────────────┘
        │
        │ OU attente prestataire
        ▼
  [ATTENTE PRESTATAIRE] ─── SLA pausé
        │ Prestataire intervient
        ▼
  [EN COURS] ─── SLA repris
        │
        │ Technicien résout
        ▼
  [RÉSOLU] ─── Demandeur notifié
        │
        │ Agent clôture OU Demandeur réouvre
        ▼
  [CLÔTURÉ] (terminal, verrouillé)
```

---

## 6. Système de notifications

Les notifications fonctionnent sur deux canaux :

| Canal | Technologie | Mode |
|-------|-------------|------|
| In-app | Modèle `Notification` en base | Synchrone |
| Email | Gmail SMTP / threading Python | Asynchrone (thread) |

**Événements déclencheurs :**

| Événement | Destinataires |
|-----------|---------------|
| `created` | Admins + Agents (si IT) ou Manager dept cible |
| `assigned` | Technicien assigné + Demandeur |
| `status_changed` | Demandeur + Technicien assigné |
| `comment_added` | Demandeur + Technicien assigné |
| `mentioned` | Utilisateur mentionné |
| `info_responded` | Technicien assigné |
| `transferred` | Manager du département cible |
| `sla_exceeded` | Technicien assigné + Admins |

---

## 7. Sécurité

| Mécanisme | Implémentation |
|-----------|----------------|
| Authentification | Session Django (cookie) |
| Autorisation | Contrôle rôle dans chaque vue |
| CSRF | Middleware Django CSRF |
| XSS | Échappement automatique Django templates |
| Variables sensibles | Fichier `.env` (non versionné) |
| Mots de passe | PBKDF2-SHA256 (Django par défaut) |
| HTTPS | Géré par PythonAnywhere en prod |

---

## 8. Déploiement

Voir le document [04_guide_deploiement.md](04_guide_deploiement.md) pour les instructions détaillées.

| Environnement | Détail |
|---------------|--------|
| Développement | `python manage.py runserver`, SQLite |
| Test / Recette | PythonAnywhere gratuit, SQLite |
| Production | PythonAnywhere payant, PostgreSQL |
