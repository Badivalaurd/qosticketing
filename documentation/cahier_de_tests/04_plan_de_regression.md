# Plan de Régression — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## 1. Objectif

Le plan de régression définit les tests à exécuter systématiquement avant chaque déploiement en production, pour s'assurer que les nouvelles modifications n'ont pas dégradé les fonctionnalités existantes.

---

## 2. Déclencheurs

Les tests de régression sont obligatoires dans les cas suivants :

| Déclencheur | Niveau de régression |
|-------------|---------------------|
| Déploiement d'une nouvelle version | Complet |
| Correctif d'un bug critique | Complet (module impacté) |
| Mise à jour d'une dépendance majeure | Complet |
| Modification du modèle de données | Complet |
| Changement de configuration serveur | Partiel (accès, auth) |
| Modification d'un template | Partiel (UI) |

---

## 3. Matrice de criticité des fonctionnalités

| ID | Fonctionnalité | Criticité | Priorité de test |
|----|----------------|-----------|-----------------|
| R01 | Connexion / Déconnexion | Critique | P0 |
| R02 | Création d'un ticket | Critique | P0 |
| R03 | Affectation d'un ticket | Critique | P0 |
| R04 | Changement de statut | Critique | P0 |
| R05 | Notifications in-app | Haute | P1 |
| R06 | Envoi d'email | Haute | P1 |
| R07 | Pagination et filtres | Haute | P1 |
| R08 | Demande d'information | Haute | P1 |
| R09 | Répondre à une DI | Haute | P1 |
| R10 | Transfert inter-dept | Haute | P1 |
| R11 | Recherche par référence | Normale | P2 |
| R12 | @mentions | Normale | P2 |
| R13 | SLA (calcul, pause, reprise) | Haute | P1 |
| R14 | Export CSV/Excel | Normale | P2 |
| R15 | Accès Django Admin | Haute | P1 |
| R16 | Création d'utilisateur | Haute | P1 |
| R17 | Activation département | Normale | P2 |
| R18 | Droits par rôle (RBAC) | Critique | P0 |
| R19 | Visibilité des tickets | Critique | P0 |
| R20 | Clôture et statuts terminaux | Haute | P1 |

---

## 4. Scénarios de régression — niveau P0 (bloquants)

### R01 — Connexion / Déconnexion

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Accéder à `/login/` | Page de connexion affichée |
| 2 | Saisir identifiants valides | Redirection vers tableau de bord |
| 3 | Cliquer Déconnexion | Redirection vers `/login/`, session détruite |
| 4 | Accéder à `/tickets/` sans connexion | Redirection vers `/login/` |

### R02 — Création d'un ticket (Demandeur)

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Se connecter en tant que Demandeur | — |
| 2 | Aller sur `/tickets/nouveau/` | Formulaire affiché ; département pré-rempli et non modifiable |
| 3 | Soumettre avec titre + description | Ticket créé ; référence générée `OMCM-{CODE}-NNNNN` |
| 4 | Vérifier l'onglet IT de l'agent | Ticket visible en statut NOUVEAU |

### R03 — Affectation d'un ticket (Agent)

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Se connecter en tant qu'Agent | — |
| 2 | Ouvrir un ticket NOUVEAU | Panneau "Affecter" visible |
| 3 | Sélectionner un technicien et confirmer | Statut → AFFECTÉ ; technicien notifié |
| 4 | Vérifier que l'Agent ne peut plus réaffecter (EN_COURS) | Panneau "Affecter" absent |

### R18 — Contrôle des droits (RBAC)

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Demandeur tente `/tickets/{num}/assign/` | Rejet (403 ou redirect avec message) |
| 2 | Technicien tente de réaffecter ticket EN_COURS | Rejet |
| 3 | Observateur tente de commenter | Bouton commentaire absent |
| 4 | Demandeur accède à un ticket qui n'est pas le sien | "Ticket introuvable ou vous n'avez pas les droits" |

### R19 — Visibilité des tickets

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Demandeur A crée ticket T1 | T1 visible pour A |
| 2 | Demandeur B (autre dept) se connecte | T1 non visible pour B |
| 3 | Agent se connecte | T1 visible (onglet IT) |
| 4 | Admin se connecte | T1 visible |

---

## 5. Scénarios de régression — niveau P1

### R08 — Demande d'information + R09 — Réponse

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Technicien envoie DI sur ticket EN_COURS | Statut → ATTENTE_INFO ; SLA pausé |
| 2 | Vérifier `responsable` dans la fiche | = utilisateur sollicité |
| 3 | Utilisateur sollicité voit le bouton "Répondre" | Visible uniquement pour `info_requested_from` |
| 4 | Utilisateur répond | Statut → EN_COURS ; SLA reprend ; `responsable` = technicien |

### R13 — SLA

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Créer ticket P1 (SLA résolution : 4h) | `sla_resolution_deadline` = now + 4h |
| 2 | Passer en ATTENTE_INFO | `sla_paused_at` renseigné |
| 3 | Repasser EN_COURS après 1h | `sla_total_paused` += 1h ; deadline repoussée d'1h |
| 4 | Passer en RÉSOLU | Compteur SLA arrêté |

### R10 — Transfert inter-département

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Agent ouvre ticket NOUVEAU | Formulaire "Transférer" visible |
| 2 | Sélectionner un département activé | — |
| 3 | Confirmer le transfert | Ticket dans onglet "Autres directions" ; manager notifié |
| 4 | Agent tente de transférer un ticket EN_COURS | Action non disponible |

---

## 6. Environnement de test de régression

- Utiliser l'environnement de recette (PythonAnywhere test) avec des données de test réinitialisées.
- Base de données : fixture de départ (`python manage.py loaddata test_data.json`).
- Réinitialiser la base entre deux passages complets : `python manage.py flush --noinput`.

---

## 7. Critères d'acceptation

| Niveau | Critère |
|--------|---------|
| **GO** | Tous les tests P0 passent ; ≥ 90% des P1 passent |
| **GO avec réserves** | Tous P0 passent ; ≥ 75% P1 ; anomalies P1 connues et documentées |
| **NO GO** | Au moins un P0 échoue |

---

## 8. Rapport de régression

À chaque passage, renseigner :

| Champ | Valeur |
|-------|--------|
| Date | |
| Version testée | |
| Testeur | |
| Nb tests P0 exécutés / passés | |
| Nb tests P1 exécutés / passés | |
| Nb tests P2 exécutés / passés | |
| Anomalies bloquantes | |
| Anomalies mineures | |
| Décision (GO / NO GO) | |
| Observations | |
