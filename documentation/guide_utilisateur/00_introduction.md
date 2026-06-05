# Guide Utilisateur — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026

---

## Qu'est-ce que QoS Ticketing ?

**QoS Ticketing** est la plateforme de gestion des demandes et incidents de votre organisation. Elle vous permet de :

- Soumettre une demande d'assistance ou signaler un incident
- Suivre l'avancement de vos demandes en temps réel
- Communiquer avec les équipes techniques via les commentaires
- Recevoir des notifications à chaque étape du traitement

---

## Accéder à la plateforme

Ouvrez votre navigateur et accédez à l'URL fournie par votre administrateur.  
Saisissez votre **identifiant** et votre **mot de passe**, puis cliquez sur **Connexion**.

> Si vous n'avez pas encore de compte, contactez votre administrateur ou l'agent de support IT.

---

## Votre rôle dans la plateforme

Le comportement de la plateforme dépend du rôle qui vous a été attribué. Consultez le guide correspondant à votre rôle :

| Vous êtes... | Guide à consulter |
|---|---|
| Un utilisateur qui crée des demandes | [Guide Demandeur](01_guide_demandeur.md) |
| Un technicien qui traite les tickets | [Guide Technicien](02_guide_technicien.md) |
| L'agent de support IT | [Guide Agent de Support](03_guide_agent_support.md) |
| Un manager de département | [Guide Manager](04_guide_manager.md) |
| L'administrateur de la plateforme | [Guide Administrateur](05_guide_administrateur.md) |

---

## Éléments communs à tous les utilisateurs

### La barre de navigation (en haut)

- **Barre de recherche** — Saisir une référence de ticket (ex. `OMCM-DSI-00012`) pour y accéder directement, ou un mot-clé pour chercher dans la liste.
- **Cloche** — Vos notifications. Un badge rouge indique le nombre de messages non lus.
- **Avatar / Nom** — Accéder à votre profil ou vous déconnecter.

### La barre latérale (à gauche)

- **Tableau de bord** — Vue synthétique de votre activité.
- **Tous les tickets** — Liste des tickets auxquels vous avez accès.
- **Nouveau ticket** — Créer une nouvelle demande.
- **Mes tickets** — Vos tickets (créés ou assignés selon votre rôle).
- **Projets** — *(Visible uniquement pour les membres du département IT)*
- **Base de connaissance** — Ressources et documentation interne.
- **Reporting** — Exports et statistiques.

### Les notifications

Vous recevez une notification chaque fois que :
- Un de vos tickets change de statut
- Un commentaire est ajouté sur un de vos tickets
- Vous êtes mentionné avec `@admin`, `@agent` ou `@votre_identifiant`
- Une demande d'information vous est adressée

Cliquez sur la cloche pour voir vos dernières notifications. Cliquez sur "Tout lire" pour les marquer toutes comme lues.

---

## Priorités des tickets

| Priorité | Couleur | Délai de prise en charge | Délai de résolution |
|----------|---------|--------------------------|---------------------|
| P0 — Critique | Rouge | 10 min | 2 h |
| P1 — Haute | Orange | 30 min | 4 h |
| P2 — Moyenne | Bleu | 2 h | 24 h |
| P3 — Faible | Gris | 4 h | 48 h |

---

## Statuts des tickets

| Statut | Signification |
|--------|---------------|
| **Nouveau** | Ticket créé, en attente de prise en charge |
| **Affecté** | Assigné à un technicien, pas encore traité |
| **En cours** | Le technicien travaille activement dessus |
| **En attente d'information** | Le technicien attend une réponse d'une tierce personne |
| **En attente prestataire** | En attente d'un intervenant externe |
| **Résolu** | Solution apportée, en attente de confirmation |
| **Clôturé** | Ticket fermé définitivement |
| **Rejeté** | Demande non recevable |
| **Annulé** | Ticket annulé par le demandeur |
