# Guide Manager — QoS Ticketing

**Rôle :** Manager de département  
**Version :** 1.0 | **Date :** Juin 2026

---

## Contexte de votre rôle

Le rôle de Manager dans QoS Ticketing est attribué par l'administrateur à **un seul membre par département activé** (hors IT). Vous êtes responsable de la distribution des tickets entrants dans votre département.

> **Note :** Le manager du département IT a un rôle différent (gestion des projets) — la distribution des tickets IT est assurée par l'agent de support.

---

## Vos capacités

- Voir tous les tickets de votre département
- Affecter les tickets **Nouveau** et **Affecté** aux membres de votre équipe
- Faire évoluer le statut des tickets de votre département
- Envoyer des demandes d'information
- Ajouter des commentaires

---

## 1. La file d'entrée de votre département

Quand un ticket vous est adressé (soit directement par le demandeur, soit transféré par l'agent de support IT), il apparaît dans votre liste au statut **Nouveau**.

Vous recevez une notification à chaque nouveau ticket entrant.

---

## 2. Distribuer un ticket à votre équipe

1. Ouvrez la fiche du ticket (statut **Nouveau**).
2. Dans le panneau droit, section **Affecter**, choisissez un membre de votre équipe.
3. Cliquez **Affecter**.

**Ce qui se passe :**
- Statut → **Affecté**
- SLA réinitialisé depuis ce moment
- Le membre de l'équipe et le demandeur sont notifiés

> La liste ne propose que les membres actifs de votre propre département.

---

## 3. Suivre les tickets de votre département

Dans **Tous les tickets**, vous voyez uniquement les tickets dont votre département est la cible ou le département demandeur.

Utilisez les filtres pour :
- Voir les tickets en retard (filtre **SLA dépassé**)
- Suivre la charge d'un technicien spécifique (filtre **Assigné à moi**)
- Filtrer par statut ou priorité

---

## 4. Transitions de statut disponibles

En tant que manager, vous pouvez faire évoluer les tickets de votre département ainsi :

| Depuis | Vers | Condition |
|--------|------|-----------|
| Nouveau | Affecté, Rejeté | — |
| Affecté | En cours | — |
| En cours | En attente d'info, Résolu | — |
| En attente d'info | En cours | — |
| Résolu | Clôturé | — |

---

## 5. Envoyer une demande d'information

Depuis un ticket **En cours** de votre département :

1. Formulaire **Demande d'information** dans le panneau droit.
2. Sélectionner la personne à solliciter.
3. Rédiger la question.
4. Cliquer **Envoyer**.

Le SLA se met en pause jusqu'à la réponse.

---

## 6. Questions fréquentes

**Je viens d'être nommé manager — pourquoi je ne vois pas les anciens tickets ?**  
Seuls les tickets créés après votre activation comme manager de ce département sont routés vers vous. Les anciens tickets existants dans le système restent tels quels.

**Un ticket est arrivé chez moi mais il concerne en réalité le département IT.**  
Vous ne pouvez pas le transférer directement. Informez l'agent de support IT par un commentaire ou par `@agent`, et il procèdera au retransfer si nécessaire.

**Puis-je modifier la priorité d'un ticket ?**  
Non, cette action est réservée à l'agent de support et à l'administrateur.
