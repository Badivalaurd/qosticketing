# Guide Agent de Support — QoS Ticketing

**Rôle :** Agent de Support (IT)  
**Version :** 1.0 | **Date :** Juin 2026

---

## Vos capacités dans la plateforme

L'agent de support IT est le pivot de la distribution des tickets IT. Vous pouvez :
- Voir **tous** les tickets (IT et autres directions)
- Affecter les tickets **Nouveau** aux techniciens IT
- Transférer un ticket mal orienté vers le manager du bon département
- Clôturer les tickets résolus
- Rejeter les tickets non recevables
- Modifier la priorité d'un ticket (avec réinitialisation du SLA)
- Ajouter des commentaires sur tous les tickets
- Exporter les tickets en CSV ou Excel

> **Important :** Une fois un ticket passé en **En cours**, vous ne pouvez plus le réaffecter. Seul l'administrateur peut le faire.

---

## 1. La file d'entrée — tickets Nouveaux

Votre priorité quotidienne est l'onglet **Département Informatique** de la liste des tickets, filtré sur le statut **Nouveau**.

Pour chaque ticket entrant :
1. Lire la description et évaluer la priorité
2. Choisir le bon technicien selon la charge de travail et la spécialité
3. Affecter le ticket (voir section 2)

---

## 2. Affecter un ticket

1. Ouvrez la fiche du ticket (statut **Nouveau**).
2. Dans le panneau de droite, section **Affecter**, sélectionnez un technicien dans la liste déroulante.
3. Cliquez **Affecter**.

**Ce qui se passe :**
- Statut → **Affecté**
- Le SLA est réinitialisé depuis ce moment
- Le technicien et le demandeur sont notifiés

> La liste ne propose que les utilisateurs du département IT (hors admins, agents, observateurs).

---

## 3. Transférer un ticket vers un autre département

Si un demandeur a envoyé sa demande au mauvais endroit et qu'elle concerne un autre département activé :

1. Ouvrez le ticket (statut **Nouveau** uniquement).
2. Section **Transférer à un département**.
3. Sélectionnez le département cible (uniquement les départements activés par l'admin).
4. Ajoutez un motif (optionnel mais recommandé).
5. Cliquez **Transférer**.

**Ce qui se passe :**
- Le ticket passe dans l'onglet **Autres directions**
- Le manager du département cible est notifié
- Le ticket **reste au statut Nouveau** — ce n'est pas une prise en charge
- Le manager s'occupe ensuite de le distribuer à son équipe

---

## 4. L'onglet "Autres directions"

Cet onglet dans la liste des tickets vous permet de visualiser les tickets des **autres départements activés** (Finance, RH, etc.).

- Vous avez une **vue en lecture** sur ces tickets
- Vous pouvez ajouter des commentaires
- Vous ne pouvez **pas** les traiter ou les réaffecter (sauf l'admin via Django Admin)

---

## 5. Rejeter un ticket

Un ticket peut être rejeté s'il est hors périmètre, doublon, ou mal formulé :

1. Ouvrez le ticket (statut **Nouveau**).
2. Sélectionnez **Rejeté** dans le panneau de statut.
3. Renseignez obligatoirement le **motif du rejet**.
4. Cliquez **Changer le statut**.

Le demandeur est notifié avec le motif.

---

## 6. Clôturer un ticket résolu

Quand un technicien passe un ticket en **Résolu** et que le demandeur confirme ou ne conteste pas :

1. Ouvrez le ticket (statut **Résolu**).
2. Sélectionnez **Clôturé**.
3. Cliquez **Changer le statut**.

> Un ticket clôturé est verrouillé définitivement — aucune modification n'est possible.

---

## 7. Modifier la priorité d'un ticket

Uniquement vous (ou l'admin) pouvez modifier la priorité :

1. Ouvrez un ticket actif (hors statuts terminaux).
2. Section **Priorité** dans le panneau droit.
3. Sélectionnez la nouvelle priorité.
4. Renseignez le motif du changement.
5. Cliquez **Appliquer**.

**Effet :** Le SLA est entièrement réinitialisé selon la nouvelle priorité.

---

## 8. @mentions dans les commentaires

Dans vos commentaires, vous pouvez utiliser :
- `@admin` — alerte tous les administrateurs actifs
- `@agent` — alerte tous les agents actifs (utile si vous êtes en équipe)
- `@username` — alerte un utilisateur spécifique par son identifiant

---

## 9. Export des données

Dans la liste des tickets, deux boutons en haut à droite :
- **CSV** — Export de tous vos tickets visibles
- **Excel** — Même export au format XLSX, avec mise en forme

Ces exports respectent les filtres actifs — si vous filtrez par statut avant d'exporter, seuls les tickets filtrés sont exportés.

---

## 10. Recherche rapide par référence

Depuis n'importe quelle page, utilisez la barre de recherche en haut :
- Tapez une référence exacte (ex. `OMCM-DSI-00045`) → accès direct au ticket
- Tapez un mot-clé → recherche dans la liste
