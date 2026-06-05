# Matrice des Droits — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## Légende

| Symbole | Signification |
|---------|---------------|
| ✓ | Autorisé sans condition |
| ✓* | Autorisé sous condition (précisée) |
| — | Non autorisé |

---

## 1. Gestion des utilisateurs

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Créer un utilisateur | ✓ | — | — | — | — | — |
| Modifier un utilisateur | ✓ | — | — | — | — | — |
| Désactiver un compte | ✓ | — | — | — | — | — |
| Modifier son propre profil | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Changer son mot de passe | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Attribuer un rôle | ✓ | — | — | — | — | — |
| Voir la liste des utilisateurs | ✓ | ✓ | — | ✓* | — | — |

*Manager : uniquement les membres de son département.

---

## 2. Gestion des départements

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Créer un département | ✓ | — | — | — | — | — |
| Activer un département (ticketing) | ✓ | — | — | — | — | — |
| Désigner un manager dept | ✓ | — | — | — | — | — |
| Voir la liste des départements | ✓ | ✓ | — | — | — | — |

---

## 3. Création et accès aux tickets

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Créer un ticket | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Voir ses propres tickets | ✓ | ✓ | ✓ | ✓ | ✓ | ✓* |
| Voir tous les tickets IT | ✓ | ✓ | ✓ | — | — | — |
| Voir tickets de son département | ✓ | ✓ | — | ✓ | — | — |
| Voir tickets autres directions | ✓ | ✓ | — | — | — | — |
| Rechercher un ticket par référence | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

*Observateur : uniquement les tickets où il est désigné observateur.

---

## 4. Transitions de statut

| Transition | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|-----------|-------|-------|------------|---------|-----------|-------------|
| NOUVEAU → AFFECTÉ | ✓ | ✓ | — | ✓* | — | — |
| NOUVEAU → REJETÉ | ✓ | ✓ | — | ✓* | — | — |
| NOUVEAU → ANNULÉ | ✓ | — | — | — | ✓* | — |
| AFFECTÉ → EN_COURS | ✓ | ✓ | ✓* | ✓* | — | — |
| EN_COURS → ATTENTE_INFO | ✓ | — | ✓* | ✓* | — | — |
| EN_COURS → ATTENTE_PRESTATAIRE | ✓ | — | ✓* | ✓* | — | — |
| EN_COURS → RÉSOLU | ✓ | — | ✓* | ✓* | — | — |
| ATTENTE_INFO → EN_COURS | ✓ | — | ✓* | ✓* | — | — |
| ATTENTE_PRESTATAIRE → EN_COURS | ✓ | — | ✓* | ✓* | — | — |
| RÉSOLU → EN_COURS (réouverture) | ✓ | ✓ | ✓* | ✓* | ✓* | — |
| RÉSOLU → CLÔTURÉ | ✓ | ✓ | — | ✓* | — | — |

*Condition : le ticket appartient à leur périmètre (département, assignation).  
Demandeur : uniquement ses propres tickets.

---

## 5. Affectation des tickets

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Affecter ticket NOUVEAU (IT) | ✓ | ✓ | — | — | — | — |
| Affecter ticket NOUVEAU (autre dept) | ✓ | — | — | ✓* | — | — |
| Affecter ticket AFFECTÉ | ✓ | ✓* | — | ✓* | — | — |
| Réaffecter ticket EN_COURS | ✓ | — | — | — | — | — |
| Transférer vers autre département | ✓ | ✓ | — | — | — | — |
| Modifier la priorité d'un ticket | ✓ | ✓ | — | — | — | — |

*Agent : uniquement pour les tickets en statut NOUVEAU (pas EN_COURS ni au-delà).  
*Manager : uniquement pour les tickets de son département.

---

## 6. Commentaires et demandes d'information

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Ajouter un commentaire public | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Ajouter un commentaire interne | ✓ | ✓ | ✓ | ✓ | — | — |
| Envoyer une demande d'information | ✓ | — | ✓* | ✓* | — | — |
| Répondre à une demande d'info | — | — | — | — | ✓* | — |
| Utiliser @mentions | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Joindre un fichier | ✓ | ✓ | ✓ | ✓ | ✓ | — |

*Technicien / Manager : uniquement sur les tickets de leur périmètre.  
*Répondre à une demande d'info : uniquement l'utilisateur désigné (`info_requested_from`).

---

## 7. Notifications

| Événement | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|-----------|-------|-------|------------|---------|-----------|-------------|
| Ticket créé (IT) | ✓ | ✓ | — | — | — | — |
| Ticket créé (autre dept) | — | — | — | ✓* | — | — |
| Ticket affecté | — | — | ✓ | — | ✓ | — |
| Changement de statut | — | — | ✓* | ✓* | ✓ | — |
| Commentaire ajouté | — | — | ✓* | ✓* | ✓ | — |
| Mentionné (@username, @admin, @agent) | ✓* | ✓* | ✓* | ✓* | ✓* | — |
| Demande d'info envoyée | — | — | — | — | ✓* | — |
| Réponse à la demande d'info | — | — | ✓* | — | — | — |
| Ticket transféré | — | — | — | ✓* | — | — |
| SLA dépassé | ✓ | — | ✓* | — | — | — |

*Selon le contexte : manager du dept concerné, technicien assigné, utilisateur mentionné.

---

## 8. Projets IT

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Voir l'onglet Projets | ✓* | ✓* | ✓* | ✓* | — | — |
| Créer un projet | ✓ | — | — | ✓* | — | — |
| Gérer les sprints/tâches | ✓ | ✓* | ✓* | ✓* | — | — |
| Associer un ticket à un projet | ✓ | ✓ | ✓* | ✓* | — | — |

*Réservé aux membres IT (`is_it_member`). Manager IT uniquement pour la gestion de projets.

---

## 9. Administration et reporting

| Action | Admin | Agent | Technicien | Manager | Demandeur | Observateur |
|--------|-------|-------|------------|---------|-----------|-------------|
| Accès Django Admin (`/admin/`) | ✓ | — | — | — | — | — |
| Configurer les SLA | ✓ | — | — | — | — | — |
| Gérer les catégories | ✓ | — | — | — | — | — |
| Voir le tableau de bord global | ✓ | ✓ | — | ✓* | — | — |
| Exporter les tickets (CSV/Excel) | ✓ | ✓ | — | ✓* | — | — |
| Voir les logs d'audit | ✓ | — | — | — | — | — |

*Manager : uniquement les données de son département.
