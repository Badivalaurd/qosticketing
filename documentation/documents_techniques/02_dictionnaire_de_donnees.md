# Dictionnaire de Données — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## 1. Modèle `Department` (apps/accounts)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `name` | CharField(100) | Non | — | Nom complet du département |
| `code` | CharField(10) | Non | — | Code court unique (ex. `DSI`, `FIN`) |
| `parent` | FK → Department | Oui | NULL | Département parent (hiérarchie) |
| `is_it_department` | BooleanField | Non | False | Marque le département IT (un seul) |
| `ticketing_enabled` | BooleanField | Non | False | Département activé pour recevoir des tickets |
| `manager` | FK → User | Oui | NULL | Manager ticketing du département |
| `is_active` | BooleanField | Non | True | Département actif |
| `created_at` | DateTimeField | Non | now | Date de création |

**Contraintes :** `code` est unique. Un seul département peut avoir `is_it_department=True`.

---

## 2. Modèle `User` (apps/accounts)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `username` | CharField(150) | Non | — | Identifiant de connexion (unique) |
| `email` | EmailField | Non | — | Adresse email (obligatoire, unique) |
| `first_name` | CharField(150) | Non | — | Prénom |
| `last_name` | CharField(150) | Non | — | Nom |
| `role` | CharField(20) | Non | `DEMANDEUR` | Rôle (voir tableau rôles) |
| `department` | FK → Department | Oui | NULL | Département d'appartenance |
| `phone` | CharField(20) | Oui | NULL | Téléphone |
| `avatar` | ImageField | Oui | NULL | Photo de profil |
| `is_active` | BooleanField | Non | True | Compte actif |
| `is_staff` | BooleanField | Non | False | Accès à Django Admin |
| `date_joined` | DateTimeField | Non | now | Date de création du compte |

**Valeurs de `role` :**

| Constante | Valeur | Description |
|-----------|--------|-------------|
| `ROLE_ADMIN` | `ADMIN` | Accès complet |
| `ROLE_MANAGER` | `MANAGER` | Distribution dans un département |
| `ROLE_AGENT` | `AGENT` | Agent de support IT |
| `ROLE_TECHNICIEN` | `TECHNICIEN` | Traitement des tickets IT |
| `ROLE_DEMANDEUR` | `DEMANDEUR` | Création de tickets uniquement |
| `ROLE_OBSERVATEUR` | `OBSERVATEUR` | Lecture seule |

**Propriétés calculées :**

| Propriété | Description |
|-----------|-------------|
| `is_it_member` | True si `department.is_it_department` |
| `full_name` | `first_name + ' ' + last_name` |

---

## 3. Modèle `Ticket` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire interne |
| `number` | CharField(30) | Non | Auto | Référence unique (ex. `OMCM-DSI-00001`) |
| `title` | CharField(200) | Non | — | Titre du ticket |
| `description` | TextField | Non | — | Description détaillée |
| `status` | CharField(30) | Non | `NOUVEAU` | Statut courant |
| `priority` | CharField(5) | Non | `P2` | Priorité (P0–P3) |
| `category` | FK → Category | Oui | NULL | Catégorie de problème |
| `created_by` | FK → User | Non | — | Demandeur |
| `assigned_to` | FK → User | Oui | NULL | Technicien assigné |
| `responsable` | FK → User | Oui | NULL | Responsable courant (ball-in-court) |
| `info_requested_from` | FK → User | Oui | NULL | Personne sollicitée en ATTENTE_INFO |
| `department` | FK → Department | Non | — | Département du demandeur |
| `target_department` | FK → Department | Oui | NULL | Département receveur (si autre que IT) |
| `project` | FK → Project | Oui | NULL | Projet IT associé |
| `sla_response_deadline` | DateTimeField | Oui | NULL | Échéance prise en charge |
| `sla_resolution_deadline` | DateTimeField | Oui | NULL | Échéance résolution |
| `sla_paused_at` | DateTimeField | Oui | NULL | Début de la pause SLA |
| `sla_total_paused` | DurationField | Non | 0 | Durée cumulée des pauses SLA |
| `rejection_reason` | TextField | Oui | NULL | Motif du rejet |
| `created_at` | DateTimeField | Non | now | Date de création |
| `updated_at` | DateTimeField | Non | now | Dernière modification |

**Valeurs de `status` :**

| Constante | Valeur | Description |
|-----------|--------|-------------|
| `STATUS_NOUVEAU` | `NOUVEAU` | Ticket créé, non pris en charge |
| `STATUS_AFFECTE` | `AFFECTE` | Technicien désigné, non démarré |
| `STATUS_EN_COURS` | `EN_COURS` | En traitement actif |
| `STATUS_ATTENTE_INFO` | `ATTENTE_INFO` | En attente d'information, SLA pausé |
| `STATUS_ATTENTE_PRESTATAIRE` | `ATTENTE_PRESTATAIRE` | En attente prestataire, SLA pausé |
| `STATUS_RESOLU` | `RESOLU` | Solution apportée |
| `STATUS_CLOTURE` | `CLOTURE` | Terminé définitivement |
| `STATUS_REJETE` | `REJETE` | Non recevable |
| `STATUS_ANNULE` | `ANNULE` | Annulé par le demandeur |

**Valeurs de `priority` :**

| Valeur | Libellé | Délai prise en charge | Délai résolution |
|--------|---------|----------------------|-----------------|
| `P0` | Critique | 15 min | 1h |
| `P1` | Haute | 1h | 4h |
| `P2` | Normale | 4h | 24h |
| `P3` | Basse | 8h | 72h |

---

## 4. Modèle `Comment` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `ticket` | FK → Ticket | Non | — | Ticket concerné |
| `author` | FK → User | Non | — | Auteur du commentaire |
| `content` | TextField | Non | — | Corps du commentaire (peut contenir @mentions) |
| `is_internal` | BooleanField | Non | False | Commentaire interne (invisible au demandeur) |
| `created_at` | DateTimeField | Non | now | Date de création |

---

## 5. Modèle `Attachment` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `ticket` | FK → Ticket | Non | — | Ticket parent |
| `comment` | FK → Comment | Oui | NULL | Commentaire associé (si via commentaire) |
| `uploaded_by` | FK → User | Non | — | Utilisateur ayant uploadé |
| `file` | FileField | Non | — | Fichier (chemin relatif `media/`) |
| `original_name` | CharField(255) | Non | — | Nom original du fichier |
| `file_size` | IntegerField | Non | 0 | Taille en octets |
| `created_at` | DateTimeField | Non | now | Date d'upload |

---

## 6. Modèle `TicketHistory` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `ticket` | FK → Ticket | Non | — | Ticket concerné |
| `user` | FK → User | Non | — | Auteur de l'action |
| `action` | CharField(50) | Non | — | Type d'action (`status_changed`, `assigned`, etc.) |
| `old_value` | CharField(200) | Oui | NULL | Ancienne valeur |
| `new_value` | CharField(200) | Oui | NULL | Nouvelle valeur |
| `comment` | TextField | Oui | NULL | Détail additionnel |
| `created_at` | DateTimeField | Non | now | Horodatage de l'action |

---

## 7. Modèle `Notification` (apps/notifications)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `recipient` | FK → User | Non | — | Destinataire |
| `ticket` | FK → Ticket | Oui | NULL | Ticket concerné |
| `event_type` | CharField(50) | Non | — | Type d'événement |
| `title` | CharField(200) | Non | — | Titre de la notification |
| `message` | TextField | Non | — | Corps de la notification |
| `is_read` | BooleanField | Non | False | Lu ou non |
| `created_at` | DateTimeField | Non | now | Date de création |

---

## 8. Modèle `Category` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `name` | CharField(100) | Non | — | Nom de la catégorie |
| `description` | TextField | Oui | NULL | Description |
| `department` | FK → Department | Oui | NULL | Département propriétaire (NULL = global) |
| `is_active` | BooleanField | Non | True | Catégorie disponible |
| `order` | IntegerField | Non | 0 | Ordre d'affichage |

---

## 9. Modèle `SLAConfig` (apps/tickets)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `priority` | CharField(5) | Non | — | Priorité (P0–P3) |
| `response_time_minutes` | IntegerField | Non | — | Délai prise en charge (minutes) |
| `resolution_time_minutes` | IntegerField | Non | — | Délai résolution (minutes) |
| `updated_at` | DateTimeField | Non | now | Dernière modification |

---

## 10. Modèle `Project` (apps/projects)

| Champ | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | Non | Auto | Clé primaire |
| `name` | CharField(200) | Non | — | Nom du projet |
| `description` | TextField | Oui | NULL | Description |
| `manager` | FK → User | Oui | NULL | Chef de projet (membre IT) |
| `status` | CharField(20) | Non | `PLANIFIE` | État du projet |
| `start_date` | DateField | Oui | NULL | Date de début |
| `end_date` | DateField | Oui | NULL | Date de fin prévue |
| `is_active` | BooleanField | Non | True | Projet actif |
| `created_at` | DateTimeField | Non | now | Date de création |
