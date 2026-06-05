# Changelog — QoS Ticketing

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)  
Versionnement : [Semantic Versioning](https://semver.org/lang/fr/)

---

## [Non publié] — branche develop

### Ajouté
- Système ball-in-court : champ `responsable` sur les tickets pour suivre qui "détient" le ticket à chaque instant
- Département avec `ticketing_enabled` et `manager` : activation par l'admin pour permettre à d'autres directions de recevoir des tickets
- Onglet "Autres directions" dans la liste des tickets (visible Admin et Agent)
- Bouton "Répondre à la demande d'information" : seul `info_requested_from` peut y accéder ; résume le SLA et remet le ticket EN_COURS
- Transfert inter-département : admin et agent peuvent router un ticket NOUVEAU vers le manager d'un département activé
- @mentions dans les commentaires : `@admin`, `@agent`, `@username` génèrent des notifications in-app et email ciblées
- Sélecteur de nombre d'éléments par page (10/25/50/100) dans la liste des tickets
- Boutons Précédent/Suivant toujours visibles dans la pagination
- Recherche rapide par référence de ticket depuis la barre de navigation (redirect direct ou fallback liste)
- Message d'erreur friendy "Ticket introuvable ou vous n'avez pas les droits" (remplace PermissionDenied 403)
- Champs `department` et `email` rendus obligatoires à la création d'un utilisateur
- `department` pré-rempli et verrouillé dans le formulaire de création de ticket
- Champ `target_department` masqué si aucun département n'est activé pour le ticketing
- Onglet Projets masqué pour les non-membres IT
- Référence de ticket basée sur le département receveur (`target_department.code` ou IT par défaut)
- Dossier `documentation/` avec 15 livrables (cahier de tests, guides utilisateurs, documents techniques)

### Modifié
- `can_user_reassign()` : l'agent ne peut réaffecter que les tickets NOUVEAU (pas EN_COURS+)
- `can_user_see()` : inclut la vérification `responsable == user` en ATTENTE_INFO
- `get_tickets_for_user()` : paramètre `tab` pour séparer tickets IT et autres directions
- `TicketDetailView` : remplacement du `get_object()` + PermissionDenied par override de `get()` avec redirect
- `ticket_assign()` : utilise `can_user_reassign()` ; définit `ticket.responsable = assigned_to`
- `ticket_request_info()` : définit `ticket.responsable = info_user`
- `ticket_change_status()` : réinitialise `responsable` et `info_requested_from` à la sortie de ATTENTE_INFO
- `add_comment()` : gère les @mentions avec déduplication
- `load_dotenv()` : chemin explicite `BASE_DIR / '.env'` pour compatibilité PythonAnywhere
- Admins exclus de la liste des destinataires des demandes d'information

### Corrigé
- `load_dotenv()` sans chemin : échouait sur PythonAnywhere car le répertoire de travail diffère
- Filtre Django template `split` inexistant : remplacé par options HTML hardcodées pour la sélection par page
- PermissionDenied affichait une page 403 générique : remplacé par redirect avec message utilisateur

---

## [1.0.0] — 2026-05-XX — Version initiale

### Ajouté
- Système de ticketing complet (création, affectation, statuts, résolution)
- Gestion des utilisateurs et rôles (Admin, Manager, Agent, Technicien, Demandeur, Observateur)
- Gestion des départements et hiérarchie
- SLA configurable par priorité (P0–P3) avec pause automatique
- Notifications in-app et email via SMTP
- Commentaires publics et internes avec pièces jointes
- Historique complet des actions sur les tickets
- Tableau de bord KPIs
- Export CSV et Excel
- API REST (Django REST Framework)
- Interface Django Admin personnalisée
- Authentification par session Django
- Déploiement sur PythonAnywhere (SQLite)
