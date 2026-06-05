# Guide Demandeur — QoS Ticketing

**Rôle :** Demandeur  
**Version :** 1.0 | **Date :** Juin 2026

---

## Vos capacités dans la plateforme

En tant que demandeur, vous pouvez :
- Créer des tickets de demande d'assistance ou d'incident
- Suivre l'avancement de vos tickets
- Ajouter des commentaires publics sur vos tickets
- Annuler un ticket que vous avez créé (si encore au statut **Nouveau**)
- Réouvrir un ticket au statut **Résolu** si la solution ne vous convient pas

---

## 1. Créer un ticket

### Étapes

1. Cliquez sur **Nouveau ticket** dans la barre latérale ou le bouton en haut à droite de la liste.
2. Remplissez le formulaire :

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| **Titre** | Oui | Résumé court et précis de votre demande |
| **Catégorie** | Oui | Type de demande (Incident, Support, Évolution…) |
| **Sous-catégorie** | Non | Précision sur la catégorie (se charge automatiquement) |
| **Application concernée** | Non | L'application ou système concerné |
| **Priorité** | Oui | Évaluez l'urgence (P0 à P3) |
| **Département demandeur** | Auto | Pré-rempli depuis votre profil — non modifiable |
| **Envoyer vers** | Non | Si votre demande concerne un autre département activé |
| **Description** | Oui | Décrivez précisément le problème ou la demande |

3. Vous pouvez aussi joindre des fichiers (PDF, images, Excel…) après la création du ticket.
4. Cliquez sur **Créer le ticket**.

> **Numéro de ticket :** Après création, un numéro unique vous est attribué (ex. `OMCM-DSI-00012`). Notez-le pour pouvoir retrouver facilement votre ticket.

### Conseils pour une bonne description

- Décrivez **quand** le problème est apparu
- Précisez **l'impact** sur votre activité
- Mentionnez les étapes pour **reproduire** le problème
- Joignez des **captures d'écran** si pertinent

---

## 2. Suivre vos tickets

### Accéder à vos tickets

- **Mes tickets** dans la barre latérale → liste de tous vos tickets
- **Tous les tickets** → tickets de l'ensemble de votre département

### Informations visibles sur un ticket

Sur la fiche d'un ticket, vous pouvez voir :
- Le statut actuel et l'historique des changements
- Le technicien assigné et le responsable courant
- Les échéances SLA
- Les commentaires publics (les commentaires internes des techniciens ne vous sont pas visibles)
- Les pièces jointes

---

## 3. Communiquer sur un ticket

### Ajouter un commentaire

1. Ouvrez votre ticket.
2. Descendez jusqu'à la section **Commentaires**.
3. Tapez votre message dans la zone de texte.
4. Cliquez sur **Ajouter**.

> Vos commentaires sont visibles par toute l'équipe qui traite votre ticket.

### Mentionner quelqu'un

Dans un commentaire, vous pouvez mentionner :
- `@admin` — alerte tous les administrateurs
- `@agent` — alerte tous les agents de support

---

## 4. Répondre à une demande d'information

Si un technicien a besoin d'informations supplémentaires, votre ticket passe au statut **En attente d'information** et vous en êtes notifié.

Un bloc **"Répondre à la demande d'information"** apparaît sur votre ticket. Vous pouvez :
- Répondre via ce bloc (votre réponse est ajoutée comme commentaire et le ticket retourne au technicien)
- Ou simplement ajouter un commentaire si vous souhaitez poser une question sans clore la demande

---

## 5. Annuler ou réouvrir un ticket

### Annuler un ticket
- Uniquement possible si le ticket est au statut **Nouveau**
- Dans la fiche du ticket, utilisez le sélecteur de statut → **Annulé**

### Réouvrir un ticket résolu
- Si la solution proposée ne résout pas votre problème, vous pouvez réouvrir le ticket
- Dans la fiche, sélecteur de statut → **Nouveau**
- Le ticket repart en file d'attente avec un SLA réinitialisé

---

## 6. Questions fréquentes

**Mon ticket n'apparaît pas dans la liste.**  
Vérifiez que vous consultez la bonne vue. Dans "Tous les tickets", vous voyez les tickets de votre département. Dans "Mes tickets", uniquement les vôtres.

**Pourquoi mon ticket est-il passé en "Attente d'information" ?**  
Le technicien a besoin d'informations de votre part. Consultez le dernier commentaire — une question vous y est posée. Utilisez le bouton "Répondre à la demande" pour que le traitement reprenne.

**Comment savoir si mon ticket est en retard ?**  
L'indicateur SLA est affiché sur chaque ticket. S'il est rouge avec le label "Dépassé", le délai contractuel est dépassé.

**Je n'ai pas reçu de notification.**  
Vérifiez votre adresse email dans votre profil. Consultez également la cloche en haut à droite — les notifications in-app sont disponibles même sans email.
