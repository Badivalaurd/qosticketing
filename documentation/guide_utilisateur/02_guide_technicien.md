# Guide Technicien — QoS Ticketing

**Rôle :** Technicien  
**Version :** 1.0 | **Date :** Juin 2026

---

## Vos capacités dans la plateforme

En tant que technicien, vous pouvez :
- Voir tous les tickets du département IT
- Prendre en charge les tickets qui vous sont assignés
- Faire évoluer le statut de vos tickets
- Envoyer des demandes d'information
- Ajouter des commentaires (publics ou internes)
- Résoudre les tickets

---

## 1. Tableau de bord

À la connexion, votre tableau de bord affiche :
- Le nombre de tickets qui vous sont assignés
- Les tickets dont le SLA est proche ou dépassé
- Les dernières activités sur vos tickets
- Les tickets en attente de retour

---

## 2. Mes tickets assignés

Cliquez sur **Mes tickets** dans la barre latérale pour voir uniquement les tickets qui vous sont affectés.

Le badge **SLA** sur chaque ligne indique l'état du délai :
- **OK** (vert) — Dans les délais
- **X%** (orange) — Délai entamé à X%
- **Dépassé** (rouge) — Délai contractuel expiré

---

## 3. Prendre en charge un ticket

Quand un ticket vous est affecté (statut **Affecté**) :

1. Ouvrez la fiche du ticket.
2. Dans le panneau de droite, sous "Actions", sélectionnez **En cours** comme nouveau statut.
3. Ajoutez un commentaire si nécessaire.
4. Cliquez **Changer le statut**.

> Une fois passé en **En cours**, le ticket est "verrouillé" sous votre responsabilité. Seul l'administrateur peut vous retirer l'affectation.

---

## 4. Faire évoluer le statut

Depuis un ticket **En cours**, vous pouvez :

| Action | Nouveau statut | Quand l'utiliser |
|--------|----------------|------------------|
| Résoudre | **Résolu** | Solution apportée, en attente de confirmation |
| Demander info | **En attente d'information** | Il vous manque des éléments |
| Bloquer prestataire | **En attente prestataire** | En attente d'un intervenant externe |

---

## 5. Envoyer une demande d'information

Quand vous avez besoin d'une information d'un utilisateur ou d'un collègue :

1. Ouvrez votre ticket (statut **En cours**).
2. Dans le panneau droit, cliquez sur le formulaire **Demande d'information**.
3. Sélectionnez la personne à qui vous posez la question (tout utilisateur sauf les admins).
4. Rédigez votre message/question.
5. Cliquez **Envoyer la demande**.

**Ce qui se passe ensuite :**
- Le ticket passe en **En attente d'information**
- Le SLA est mis en pause automatiquement
- La personne sollicitée reçoit une notification
- Elle devient temporairement **responsable** du ticket
- Quand elle répond, le ticket vous revient automatiquement et le SLA reprend

> Vous pouvez continuer à ajouter des commentaires libres pendant cette période.

---

## 6. Gérer l'attente prestataire

Quand vous attendez une intervention externe :

1. Passer le statut en **En attente prestataire**.
2. Le SLA est automatiquement mis en pause.
3. Quand l'intervenant a agi, repassez en **En cours** pour reprendre le compteur.

---

## 7. Résoudre un ticket

1. Ouvrez le ticket (statut **En cours**).
2. Sélectionnez **Résolu** comme nouveau statut.
3. Ajoutez obligatoirement un commentaire décrivant la solution apportée.
4. Cliquez **Changer le statut**.

Le demandeur est notifié. Il peut :
- Confirmer en laissant le ticket se faire clôturer (par l'agent)
- Réouvrir s'il estime que le problème persiste

---

## 8. Commentaires internes vs publics

| Type | Visible par le demandeur | Quand l'utiliser |
|------|--------------------------|------------------|
| **Public** | Oui | Communication avec le demandeur |
| **Interne** | Non | Notes techniques, coordination équipe |

Cochez "Commentaire interne" avant d'envoyer pour le rendre invisible au demandeur.

---

## 9. Pièces jointes

Vous pouvez à tout moment joindre des fichiers à un ticket :
- Logs, captures d'écran, documents…
- Formats acceptés : PDF, Excel, Word, images, TXT, CSV

Cliquez sur **Joindre un fichier** dans la fiche ticket.

---

## 10. SLA — ce que vous devez savoir

Le SLA (Service Level Agreement) mesure les délais de traitement :

- **Délai de prise en charge** : temps entre la création et votre premier passage en **En cours**
- **Délai de résolution** : temps total entre la création et le statut **Résolu**

Le SLA est **automatiquement mis en pause** lors des statuts :
- En attente d'information
- En attente prestataire

Il reprend automatiquement à la sortie de ces statuts.

> Si vous estimez que la priorité d'un ticket doit changer, informez l'agent de support ou l'admin — seuls eux peuvent la modifier.
