# Spécifications Fonctionnelles — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI  
**Organisation :** OMCM

---

## 1. Présentation générale

QoS Ticketing est une plateforme interne de gestion des demandes d'assistance informatique (et éventuellement d'autres départements) au sein de l'OMCM. Elle vise à :

- Centraliser toutes les demandes de support
- Assurer un suivi traçable et horodaté
- Respecter des engagements de délais via les SLA
- Fournir une visibilité claire sur la charge et la performance des équipes

---

## 2. Acteurs et périmètre

### 2.1 Acteurs du système

| Acteur | Description |
|--------|-------------|
| **Demandeur** | Tout employé de l'OMCM qui soumet une demande d'assistance |
| **Technicien** | Membre de l'IT chargé de traiter les tickets |
| **Agent de support** | Coordinateur IT distribuant et supervisant les tickets |
| **Manager** | Responsable d'un département activé pour le ticketing |
| **Administrateur** | Gestionnaire de la plateforme, droits étendus |
| **Observateur** | Accès lecture seule sur les tickets le concernant |

### 2.2 Périmètre

- La plateforme couvre les tickets **IT** par défaut.
- D'autres départements peuvent être **activés** par l'admin pour recevoir des tickets.
- La gestion de projets est réservée aux membres IT.

---

## 3. Modules fonctionnels

### 3.1 Gestion des tickets

#### 3.1.1 Création d'un ticket

**Acteurs :** Tous sauf Observateur  
**Règles :**

- Le champ **Département** est pré-rempli avec le département du demandeur et non modifiable.
- Le champ **Envoyer vers** (target_department) n'est visible que si au moins un département hors IT a été activé pour le ticketing.
- Seuls les départements avec `ticketing_enabled=True` et `is_it_department=False` apparaissent dans la liste "Envoyer vers".
- Si aucun département n'est activé, le ticket va directement à l'IT.
- La référence du ticket est générée automatiquement : `OMCM-{CODE_DEPT_RECEVEUR}-{NNNNN}` (séquence 5 chiffres, incrémentale par département).
- Le département receveur est `target_department` si renseigné, sinon l'IT.

#### 3.1.2 Cycle de vie et statuts

```
NOUVEAU → AFFECTÉ → EN_COURS → RÉSOLU → CLÔTURÉ
                         ↕
                   ATTENTE_INFO
                         ↕
               ATTENTE_PRESTATAIRE
```

Statuts terminaux (aucune transition possible) : `CLÔTURÉ`, `REJETÉ`, `ANNULÉ`.

**Transitions autorisées par rôle :**

| Depuis → Vers | Admin | Agent | Technicien | Manager |
|---------------|-------|-------|------------|---------|
| NOUVEAU → AFFECTÉ | ✓ | ✓ | — | ✓ (son dept) |
| NOUVEAU → REJETÉ | ✓ | ✓ | — | ✓ (son dept) |
| AFFECTÉ → EN_COURS | ✓ | ✓ | ✓ (si assigné) | ✓ (son dept) |
| EN_COURS → ATTENTE_INFO | ✓ | — | ✓ (si assigné) | ✓ (son dept) |
| EN_COURS → ATTENTE_PRESTATAIRE | ✓ | — | ✓ (si assigné) | ✓ (son dept) |
| EN_COURS → RÉSOLU | ✓ | — | ✓ (si assigné) | ✓ (son dept) |
| ATTENTE_INFO → EN_COURS | ✓ | — | ✓ (si assigné) | ✓ (son dept) |
| RÉSOLU → CLÔTURÉ | ✓ | ✓ | — | ✓ (son dept) |
| RÉSOLU → EN_COURS | ✓ | ✓ | ✓ (si assigné) | ✓ (son dept) |

#### 3.1.3 Système ball-in-court (responsabilité courante)

Le champ `responsable` indique qui "tient le ticket" à un instant donné :

| Situation | Responsable |
|-----------|-------------|
| Ticket affecté | `assigned_to` |
| Demande d'info envoyée | `info_requested_from` |
| Réponse à la demande d'info | `assigned_to` (rétabli) |
| Changement de technicien | Nouveau `assigned_to` |

#### 3.1.4 Affectation

- **IT :** L'agent de support ou l'admin affecte aux techniciens IT.
- **Autres depts :** Le manager du département affecte aux membres de son équipe.
- **Restriction :** L'agent de support ne peut réaffecter un ticket déjà **EN_COURS**. Seul l'admin le peut.

#### 3.1.5 Transfert inter-département

- Uniquement par admin ou agent de support.
- Uniquement sur tickets au statut **NOUVEAU**.
- Le ticket reste **NOUVEAU** après transfert.
- Le manager du département cible est notifié.
- Le ticket apparaît dans l'onglet "Autres directions" pour admin et agent.

### 3.2 Gestion des commentaires et mentions

#### 3.2.1 Commentaires

- Tout utilisateur ayant accès au ticket peut commenter.
- Les commentaires peuvent être marqués **internes** (invisibles au demandeur).
- Les pièces jointes peuvent être ajoutées via les commentaires.

#### 3.2.2 @mentions

Dans le corps d'un commentaire, les mentions déclenchent des notifications :

| Mention | Destinataires |
|---------|---------------|
| `@admin` | Tous les administrateurs actifs |
| `@agent` | Tous les agents de support actifs |
| `@username` | L'utilisateur dont l'identifiant est `username` |

Les destinataires reçoivent une notification in-app et un email. La déduplication évite les envois multiples.

### 3.3 Demandes d'information

#### 3.3.1 Envoi d'une demande

- Accessible depuis un ticket **EN_COURS**.
- Le technicien ou manager choisit un destinataire (tous rôles sauf admin).
- La demande crée un commentaire daté.
- Le SLA est mis en pause.
- Le ticket passe en **ATTENTE_INFO**.

#### 3.3.2 Réponse à une demande

- Seul `info_requested_from` voit le bouton "Répondre à la demande".
- La réponse crée un commentaire.
- Le ticket repasse en **EN_COURS**.
- Le SLA reprend.
- Le `responsable` revient à `assigned_to`.
- `info_requested_from` est vidé.

### 3.4 SLA (Service Level Agreement)

| Événement | Effet sur SLA |
|-----------|---------------|
| Ticket créé ou affecté | Démarrage / réinitialisation |
| Passage en ATTENTE_INFO | Pause |
| Retour de ATTENTE_INFO | Reprise (durée pause déduite) |
| Passage en ATTENTE_PRESTATAIRE | Pause |
| Retour de ATTENTE_PRESTATAIRE | Reprise |
| Ticket RÉSOLU | Arrêt du compteur |

**Dépassement :** Une alerte est envoyée au technicien et aux admins. L'indicateur SLA de la liste tickets passe en rouge.

### 3.5 Notifications

Toutes les notifications sont générées in-app (badge) et par email (SMTP configuré).

### 3.6 Recherche de tickets

- La barre de recherche de la navbar accepte une référence exacte ou un mot-clé.
- Référence exacte trouvée → redirection directe.
- Ticket trouvé mais accès non autorisé → message "Ticket introuvable ou vous n'avez pas les droits".
- Mot-clé → liste filtrée.

### 3.7 Gestion des utilisateurs et départements

#### 3.7.1 Création d'un utilisateur

- Champs obligatoires : email, département, rôle.
- L'email est unique dans le système.
- Seul l'admin peut attribuer le rôle ADMIN, AGENT ou TECHNICIEN.

#### 3.7.2 Activation d'un département

Via Django Admin :
1. Sélectionner le département.
2. Cocher `ticketing_enabled`.
3. Désigner un `manager` parmi les membres actifs.

Après activation, le département apparaît dans le formulaire de création de ticket.

### 3.8 Projets IT

- Module réservé aux membres IT (`is_it_member`).
- Accessible via l'onglet **Projets** (masqué pour les non-IT).
- Lie des tickets à des projets.

---

## 4. Règles de visibilité des tickets

| Rôle | Tickets visibles |
|------|-----------------|
| Admin | Tous |
| Agent | Tous (IT + autres directions) |
| Technicien | Tickets IT (tous) + ses tickets assignés |
| Manager | Tickets de son département |
| Demandeur | Tickets qu'il a créés |
| Observateur | Tickets où il est désigné observateur |

---

## 5. Exigences non-fonctionnelles

| Exigence | Valeur cible |
|----------|-------------|
| Temps de réponse pages | < 2 secondes (charge nominale) |
| Disponibilité | 99% (hors maintenances planifiées) |
| Accès concurrent | 50 utilisateurs simultanés |
| Navigateurs supportés | Chrome 120+, Firefox 120+, Edge 120+ |
| Résolution minimale | 1280×768 |
| Conformité | Données sur serveur interne OMCM |

---

## 6. Exigences de sécurité

- Authentification par identifiant/mot de passe.
- Session expirée après inactivité (configurable).
- Toutes les actions critiques sont consignées dans l'historique du ticket.
- Accès admin Django protégé par `is_staff`.
- Aucune donnée sensible en clair dans les logs.
