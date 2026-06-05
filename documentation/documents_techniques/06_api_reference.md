# Référence API — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI  
**Base URL :** `https://votre-domaine.com/api/v1/`

---

## 1. Authentification

L'API utilise l'authentification par **token** (Django REST Framework TokenAuthentication) ou par **session** (pour les clients web).

### Obtenir un token

```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "mon_identifiant",
  "password": "mon_mot_de_passe"
}
```

**Réponse :**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Utiliser le token

Inclure dans toutes les requêtes :

```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## 2. Tickets

### 2.1 Lister les tickets

```http
GET /api/v1/tickets/
```

**Paramètres de filtre (query string) :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `status` | string | Filtrer par statut (`NOUVEAU`, `EN_COURS`, etc.) |
| `priority` | string | Filtrer par priorité (`P0`, `P1`, `P2`, `P3`) |
| `assigned_to` | integer | ID de l'utilisateur assigné |
| `created_by` | integer | ID du créateur |
| `department` | integer | ID du département |
| `search` | string | Recherche texte (titre, description, numéro) |
| `page` | integer | Numéro de page |
| `page_size` | integer | Éléments par page (max 100) |

**Réponse :**
```json
{
  "count": 42,
  "next": "https://votre-domaine.com/api/v1/tickets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "number": "OMCM-DSI-00001",
      "title": "Problème réseau bureau 3",
      "status": "EN_COURS",
      "priority": "P1",
      "created_by": {"id": 5, "username": "jdupont", "full_name": "Jean Dupont"},
      "assigned_to": {"id": 12, "username": "atech", "full_name": "Alice Tech"},
      "responsable": {"id": 12, "username": "atech", "full_name": "Alice Tech"},
      "department": {"id": 2, "name": "Direction Générale", "code": "DG"},
      "target_department": null,
      "category": {"id": 3, "name": "Réseau"},
      "sla_response_deadline": "2026-06-05T10:00:00Z",
      "sla_resolution_deadline": "2026-06-05T14:00:00Z",
      "created_at": "2026-06-05T08:00:00Z",
      "updated_at": "2026-06-05T09:30:00Z"
    }
  ]
}
```

### 2.2 Créer un ticket

```http
POST /api/v1/tickets/
Content-Type: application/json

{
  "title": "Imprimante hors service",
  "description": "L'imprimante du couloir B ne répond plus.",
  "priority": "P2",
  "category": 5,
  "target_department": null
}
```

> `department` est automatiquement rempli avec le département de l'utilisateur connecté.

**Réponse :** `201 Created` + objet ticket créé.

### 2.3 Détail d'un ticket

```http
GET /api/v1/tickets/{number}/
```

**Réponse :** Objet ticket complet avec commentaires et pièces jointes.

### 2.4 Modifier un ticket (champs partiels)

```http
PATCH /api/v1/tickets/{number}/
Content-Type: application/json

{
  "priority": "P1"
}
```

**Champs modifiables selon rôle :**
- `priority` : Admin, Agent uniquement
- `title`, `description` : Admin, créateur (si NOUVEAU)

### 2.5 Changer le statut

```http
POST /api/v1/tickets/{number}/change-status/
Content-Type: application/json

{
  "status": "EN_COURS",
  "comment": "Prise en charge immédiate."
}
```

### 2.6 Affecter un ticket

```http
POST /api/v1/tickets/{number}/assign/
Content-Type: application/json

{
  "assigned_to": 12
}
```

### 2.7 Demande d'information

```http
POST /api/v1/tickets/{number}/request-info/
Content-Type: application/json

{
  "user_id": 8,
  "message": "Pouvez-vous préciser l'heure d'apparition du problème ?"
}
```

### 2.8 Répondre à une demande d'information

```http
POST /api/v1/tickets/{number}/respond-info/
Content-Type: application/json

{
  "response": "Le problème est apparu hier vers 14h00."
}
```

> Réservé à l'utilisateur désigné comme `info_requested_from`.

### 2.9 Transférer vers un département

```http
POST /api/v1/tickets/{number}/transfer-dept/
Content-Type: application/json

{
  "target_department": 4,
  "comment": "Cette demande concerne le département Finance."
}
```

---

## 3. Commentaires

### 3.1 Lister les commentaires d'un ticket

```http
GET /api/v1/tickets/{number}/comments/
```

**Réponse :**
```json
[
  {
    "id": 1,
    "author": {"id": 12, "username": "atech", "full_name": "Alice Tech"},
    "content": "Je prends en charge ce ticket.",
    "is_internal": false,
    "created_at": "2026-06-05T09:30:00Z",
    "attachments": []
  }
]
```

### 3.2 Ajouter un commentaire

```http
POST /api/v1/tickets/{number}/comments/
Content-Type: multipart/form-data

content=Mon commentaire avec @mention
is_internal=false
file=<fichier optionnel>
```

---

## 4. Notifications

### 4.1 Lister les notifications de l'utilisateur connecté

```http
GET /api/v1/notifications/
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `is_read` | boolean | Filtrer par lu/non-lu |

### 4.2 Marquer comme lu

```http
PATCH /api/v1/notifications/{id}/
Content-Type: application/json

{
  "is_read": true
}
```

### 4.3 Marquer toutes comme lues

```http
POST /api/v1/notifications/mark-all-read/
```

---

## 5. Utilisateurs

### 5.1 Profil de l'utilisateur connecté

```http
GET /api/v1/users/me/
```

### 5.2 Lister les utilisateurs (Admin seulement)

```http
GET /api/v1/users/
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `department` | integer | Filtrer par département |
| `role` | string | Filtrer par rôle |
| `is_active` | boolean | Filtrer par statut actif |

---

## 6. Départements

### 6.1 Lister les départements

```http
GET /api/v1/departments/
```

**Paramètres :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `ticketing_enabled` | boolean | Filtrer les depts activés pour ticketing |
| `is_it_department` | boolean | Filtrer le département IT |

---

## 7. Codes d'erreur

| Code HTTP | Signification | Exemple |
|-----------|---------------|---------|
| `200` | Succès | Requête GET réussie |
| `201` | Créé | Ticket créé |
| `400` | Données invalides | Champ obligatoire manquant |
| `401` | Non authentifié | Token absent ou expiré |
| `403` | Non autorisé | Rôle insuffisant pour cette action |
| `404` | Introuvable | Ticket inexistant ou accès refusé |
| `409` | Conflit | Transition de statut non autorisée |
| `500` | Erreur serveur | Erreur inattendue côté serveur |

**Format des erreurs :**
```json
{
  "detail": "Vous n'avez pas les droits pour effectuer cette action.",
  "code": "permission_denied"
}
```

---

## 8. Documentation interactive

La documentation Swagger/OpenAPI est disponible à :

- **Swagger UI :** `https://votre-domaine.com/api/schema/swagger-ui/`
- **Redoc :** `https://votre-domaine.com/api/schema/redoc/`
- **Schéma OpenAPI (JSON) :** `https://votre-domaine.com/api/schema/`

---

## 9. Limitations et bonnes pratiques

| Règle | Valeur |
|-------|--------|
| Rate limiting | 100 requêtes/minute par token |
| Taille maximale d'upload | 10 Mo par fichier |
| Pagination par défaut | 25 éléments/page |
| Pagination maximale | 100 éléments/page |
| Durée de validité du token | Illimitée (révocation manuelle) |

> Pour révoquer un token, utiliser l'endpoint `POST /api/auth/token/logout/` ou le supprimer via Django Admin.
