# Guide Administrateur — QoS Ticketing

**Rôle :** Administrateur  
**Version :** 1.0 | **Date :** Juin 2026

---

## Vue d'ensemble

L'administrateur dispose des droits les plus étendus de la plateforme. Il est responsable de la configuration, de la gestion des utilisateurs et de la supervision globale.

---

## 1. Gestion des utilisateurs

### Créer un utilisateur

1. Menu **Utilisateurs** → **Nouvel utilisateur**
2. Remplir les champs :
   - **Prénom, Nom** (obligatoires)
   - **Identifiant** (obligatoire, unique)
   - **Email** (obligatoire — utilisé pour les notifications)
   - **Rôle** (Admin, Manager, Agent, Technicien, Demandeur, Observateur)
   - **Département** (obligatoire — détermine la visibilité des tickets)
   - **Téléphone** (facultatif)
3. Définir un mot de passe temporaire
4. Valider

> **Seul l'administrateur peut attribuer ou changer les rôles.**

### Modifier un utilisateur

1. Menu **Utilisateurs** → Cliquer sur l'utilisateur
2. Modifier les champs nécessaires
3. **Sauvegarder**

### Désactiver un compte

Décochez la case **Actif** dans le formulaire d'édition. L'utilisateur ne peut plus se connecter mais ses données (tickets, commentaires) sont conservées.

---

## 2. Gestion des départements

### Créer un département

Via **Django Admin** (`/admin/`) → **Departments** → **Ajouter** :
- **Nom** et **Code** (ex. `Finance`, `FIN`)
- **Département parent** (si hiérarchique)
- **Département Informatique** : cocher uniquement pour le service IT

### Activer un département pour le ticketing

Un département autre que l'IT peut recevoir des tickets une fois activé (après accord contractuel) :

1. Ouvrir **Django Admin** → **Departments**
2. Sélectionner le département concerné
3. Cocher **Ticketing activé**
4. Sélectionner un **Manager ticketing** parmi les membres actifs de ce département
5. **Sauvegarder**

**Effets de l'activation :**
- Le champ "Envoyer vers" apparaît dans le formulaire de création de ticket
- L'onglet "Autres directions" apparaît pour les agents et admins
- Le manager choisi reçoit les tickets transférés vers son département

> Un seul manager par département. L'admin peut changer de manager à tout moment (en cas d'absence ou de changement organisationnel).

---

## 3. Configuration SLA

Accédez à la configuration SLA via le menu **Tickets** → **Configuration SLA** (ou directement `/tickets/sla-config/`).

Pour chaque priorité (P0, P1, P2, P3) :
- **Délai de prise en charge** (en minutes) — temps maximum avant qu'un technicien prenne en main
- **Délai de résolution** (en minutes) — temps maximum avant résolution

Après modification, cliquez **Enregistrer**. Les nouveaux SLA s'appliquent aux tickets créés ou réaffectés après cette modification.

---

## 4. Réaffecter un ticket EN_COURS

Seul l'admin peut réaffecter un ticket qui est déjà **En cours** (l'agent de support ne peut le faire que pour les tickets **Nouveau**).

1. Ouvrir la fiche du ticket
2. Section **Affecter** → Sélectionner le nouveau technicien
3. Cliquer **Affecter**

---

## 5. Supervision globale

### Tableau de bord

Vous voyez tous les KPIs de la plateforme :
- Tickets ouverts / en cours / résolus
- Tickets en dépassement SLA
- Activité récente

### Liste des tickets — onglet IT et Autres directions

Vous avez accès aux deux onglets et pouvez voir tous les tickets de toutes les directions.

### Export

Boutons **CSV** et **Excel** dans la liste des tickets pour extraire toutes les données.

---

## 6. Administration Django (`/admin/`)

L'interface Django Admin est réservée aux opérations avancées :

| Opération | Localisation dans l'admin |
|-----------|--------------------------|
| Activation d'un département | Admin → Departments |
| Configuration avancée des utilisateurs | Admin → Users |
| Consultation des logs d'audit | Admin → AuditLogs |
| Gestion des catégories | Admin → Categories |
| Gestion des applications | Admin → Applications |
| Configuration SLA avancée | Admin → SLAConfigs |

> L'accès à `/admin/` nécessite que votre compte soit marqué `is_staff=True` dans la base de données. Contactez un développeur si vous n'y avez pas accès.

---

## 7. Sécurité et bonnes pratiques

- Changez la clé secrète (`SECRET_KEY`) avant toute mise en production
- Ne partagez jamais les credentials SMTP de notification
- Désactivez les comptes des personnes qui quittent l'organisation plutôt que de les supprimer
- Revoyez périodiquement les rôles attribués
- Assurez des sauvegardes régulières de la base de données
