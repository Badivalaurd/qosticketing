# Cas de Tests Fonctionnels — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Légende statut :** ✅ Passé | ❌ Échoué | ⏳ À tester | ⚠️ Bloqué

---

## MODULE 1 — Authentification

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| AUTH-01 | Connexion valide | Compte actif existant | 1. Aller sur `/accounts/login/` 2. Saisir identifiants valides 3. Cliquer Connexion | Redirection vers le tableau de bord | ⏳ |
| AUTH-02 | Connexion identifiants incorrects | — | 1. Saisir un mauvais mot de passe | Message d'erreur, pas de connexion | ⏳ |
| AUTH-03 | Compte inactif | Compte avec `is_active=False` | 1. Tenter de se connecter | Message : compte désactivé | ⏳ |
| AUTH-04 | Déconnexion | Utilisateur connecté | 1. Cliquer sur avatar → Déconnexion | Redirection vers login, session expirée | ⏳ |
| AUTH-05 | Accès page protégée sans connexion | Non connecté | 1. Aller sur `/tickets/` | Redirection vers login | ⏳ |

---

## MODULE 2 — Gestion des utilisateurs

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| USR-01 | Création utilisateur avec tous les champs | Connecté Admin | 1. Menu Utilisateurs → Nouveau 2. Remplir tous les champs (email, département obligatoires) 3. Valider | Utilisateur créé, email et département renseignés | ⏳ |
| USR-02 | Création sans département | Connecté Admin | 1. Laisser département vide 2. Valider | Erreur : département obligatoire | ⏳ |
| USR-03 | Création sans email | Connecté Admin | 1. Laisser email vide 2. Valider | Erreur : email obligatoire | ⏳ |
| USR-04 | Changement de rôle | Connecté Admin | 1. Éditer un utilisateur 2. Changer le rôle 3. Sauvegarder | Rôle mis à jour, permissions changées immédiatement | ⏳ |
| USR-05 | Non-admin ne peut pas changer les rôles | Connecté Agent | 1. Tenter d'accéder au formulaire d'édition de rôle | Accès refusé ou champ absent | ⏳ |
| USR-06 | Désactivation d'un utilisateur | Connecté Admin | 1. Éditer utilisateur 2. Décocher "Actif" 3. Sauvegarder | Utilisateur ne peut plus se connecter | ⏳ |

---

## MODULE 3 — Création de tickets

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| TKT-01 | Création ticket standard | Connecté Demandeur (dept renseigné) | 1. Nouveau ticket 2. Remplir titre, catégorie, priorité, description 3. Valider | Ticket créé avec numéro `OMCM-DSI-XXXXX`, SLA initialisé | ⏳ |
| TKT-02 | Département auto-rempli depuis le compte | Connecté Demandeur avec département | 1. Ouvrir formulaire création | Champ département pré-rempli et verrouillé | ⏳ |
| TKT-03 | Champ "envoyer vers" absent si aucun dept activé | Aucun dept `ticketing_enabled` | 1. Ouvrir formulaire création | Champ `target_department` absent | ⏳ |
| TKT-04 | Champ "envoyer vers" visible si dept activé | 1 dept `ticketing_enabled=True` | 1. Ouvrir formulaire création | Champ visible, liste filtrée aux depts activés uniquement | ⏳ |
| TKT-05 | Numéro ticket = dept receveur (IT) | Ticket sans `target_department` | 1. Créer ticket | Numéro contient le code du dept IT (ex. `DSI`) | ⏳ |
| TKT-06 | Numéro ticket = dept receveur (Finance) | Dept Finance activé, ticket vers Finance | 1. Créer ticket vers Finance | Numéro contient `FIN` (ou code Finance) | ⏳ |
| TKT-07 | Titre obligatoire | — | 1. Valider sans titre | Erreur validation | ⏳ |
| TKT-08 | Description obligatoire | — | 1. Valider sans description | Erreur validation | ⏳ |

---

## MODULE 4 — Cycle de vie et permissions

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| CYC-01 | Agent affecte un ticket NOUVEAU | Ticket `NOUVEAU`, connecté Agent | 1. Ouvrir ticket 2. Affecter à un technicien | Statut → `AFFECTÉ`, SLA réinitialisé | ⏳ |
| CYC-02 | Agent ne peut pas réaffecter un ticket EN_COURS | Ticket `EN_COURS`, connecté Agent | 1. Tenter d'affecter | Message : "seul l'admin peut réaffecter un ticket en cours" | ⏳ |
| CYC-03 | Admin peut réaffecter un ticket EN_COURS | Ticket `EN_COURS`, connecté Admin | 1. Affecter à un autre technicien | Réaffectation réussie | ⏳ |
| CYC-04 | Technicien passe EN_COURS → RÉSOLU | Ticket `EN_COURS` assigné au technicien | 1. Changer statut → Résolu | Statut mis à jour, `resolved_at` renseigné | ⏳ |
| CYC-05 | Demandeur annule son ticket NOUVEAU | Ticket `NOUVEAU` créé par le demandeur | 1. Changer statut → Annulé | Ticket annulé | ⏳ |
| CYC-06 | Demandeur ne peut pas modifier statut EN_COURS | Ticket `EN_COURS` | 1. Tenter de changer statut | Aucune action disponible | ⏳ |
| CYC-07 | Demandeur réouvre un ticket RÉSOLU | Ticket `RÉSOLU`, créé par ce demandeur | 1. Changer statut → Nouveau | Ticket réouvert, SLA réinitialisé | ⏳ |
| CYC-08 | Ticket CLÔTURÉ — aucune modification | Ticket `CLÔTURÉ` | 1. Tenter toute action | Toutes les actions désactivées | ⏳ |
| CYC-09 | Manager distribue dans son dept | Ticket pour son dept, connecté Manager | 1. Affecter à membre de son équipe | Affectation réussie | ⏳ |
| CYC-10 | Manager ne peut pas affecter hors de son dept | Ticket pour dept différent | 1. Tenter d'affecter | Accès refusé | ⏳ |

---

## MODULE 5 — SLA

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| SLA-01 | SLA initialisé à la création | Ticket créé | 1. Vérifier les champs `sla_response_deadline` et `sla_resolution_deadline` | Délais calculés selon priorité P0/P1/P2/P3 | ⏳ |
| SLA-02 | SLA réinitialisé à l'affectation | Ticket affecté | 1. Affecter ticket 2. Vérifier les deadlines | Deadlines recalculées depuis le moment de l'affectation | ⏳ |
| SLA-03 | SLA pausé en ATTENTE_INFO | Ticket `EN_COURS` | 1. Envoyer demande d'info 2. Vérifier `sla_paused_at` | `sla_paused_at` renseigné, timer arrêté | ⏳ |
| SLA-04 | SLA pausé en ATTENTE_PRESTATAIRE | Ticket `EN_COURS` | 1. Changer statut → Attente prestataire | SLA mis en pause | ⏳ |
| SLA-05 | SLA repris à la sortie d'un statut pause | Ticket `ATTENTE_INFO` | 1. Répondre à la demande → statut `EN_COURS` | `sla_paused_at` = null, deadlines prolongées de la durée de pause | ⏳ |
| SLA-06 | SLA réinitialisé au changement de priorité | Ticket `EN_COURS` | 1. Admin change priorité P2 → P0 | Nouvelles deadlines calculées depuis maintenant selon P0 | ⏳ |

---

## MODULE 6 — Ball-in-court (Demande d'information)

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| BIC-01 | Technicien envoie demande d'info | Ticket `EN_COURS`, connecté Technicien assigné | 1. Formulaire "Demande d'info" 2. Sélectionner un utilisateur (non admin) 3. Saisir message 4. Envoyer | Statut → `ATTENTE_INFO`, SLA pausé, `responsable` = destinataire, notification envoyée | ⏳ |
| BIC-02 | Admin exclu de la liste des destinataires | Formulaire demande d'info ouvert | 1. Vérifier la liste déroulante | Aucun admin dans la liste | ⏳ |
| BIC-03 | Bouton "Répondre" visible seulement pour la personne sollicitée | Ticket `ATTENTE_INFO` | 1. Se connecter avec le `info_requested_from` 2. Ouvrir le ticket | Bloc "Répondre à la demande" visible | ⏳ |
| BIC-04 | Bouton "Répondre" invisible pour les autres | Ticket `ATTENTE_INFO` | 1. Se connecter avec un autre utilisateur | Bloc absent | ⏳ |
| BIC-05 | Réponse fournie → ticket retourne au technicien | Connecté `info_requested_from` | 1. Remplir réponse 2. Soumettre | Statut → `EN_COURS`, `responsable` = technicien assigné, SLA repris, commentaire visible | ⏳ |
| BIC-06 | La réponse apparaît comme commentaire | Suite BIC-05 | 1. Voir la section commentaires | Commentaire publié par le répondant | ⏳ |
| BIC-07 | La personne sollicitée peut ajouter des commentaires librement | Ticket `ATTENTE_INFO` | 1. Ajouter un commentaire sans utiliser le bouton "Répondre" | Commentaire ajouté, statut inchangé | ⏳ |

---

## MODULE 7 — Transfert inter-départements

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| TRF-01 | Agent transfère un ticket NOUVEAU vers dept activé | Dept Finance activé avec manager | 1. Ouvrir ticket `NOUVEAU` 2. Formulaire "Transférer" 3. Sélectionner Finance 4. Valider | `target_department` = Finance, manager Finance notifié, ticket reste `NOUVEAU` | ⏳ |
| TRF-02 | Bouton transfert absent si ticket pas NOUVEAU | Ticket `EN_COURS` | 1. Ouvrir ticket | Bouton "Transférer" absent | ⏳ |
| TRF-03 | Technicien ne peut pas transférer | Connecté Technicien | 1. Ouvrir ticket NOUVEAU | Bouton "Transférer" absent | ⏳ |
| TRF-04 | Ticket transféré visible dans onglet "Autres directions" | Suite TRF-01 | 1. Admin/Agent ouvre liste tickets 2. Cliquer onglet "Autres directions" | Ticket visible dans cet onglet | ⏳ |
| TRF-05 | Ticket transféré absent de l'onglet IT | Suite TRF-01 | 1. Onglet "Département Informatique" | Ticket absent | ⏳ |

---

## MODULE 8 — Commentaires et @mentions

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| CMT-01 | Commentaire public visible par le demandeur | Ticket avec commentaire public | 1. Se connecter en Demandeur | Commentaire visible | ⏳ |
| CMT-02 | Commentaire interne invisible pour le demandeur | Commentaire `is_internal=True` | 1. Se connecter en Demandeur | Commentaire absent | ⏳ |
| CMT-03 | @admin notifie tous les admins actifs | Commentaire avec `@admin` | 1. Ajouter commentaire "@admin merci de vérifier" 2. Valider | Tous les admins actifs reçoivent une notification in-app et email | ⏳ |
| CMT-04 | @agent notifie tous les agents actifs | Commentaire avec `@agent` | 1. Même principe | Tous les agents reçoivent une notification | ⏳ |
| CMT-05 | @username notifie l'utilisateur spécifique | Commentaire avec `@jean.dupont` | 1. Mentionner un username existant | Cet utilisateur seul est notifié | ⏳ |
| CMT-06 | Pièce jointe uploadée | — | 1. Cliquer "Joindre un fichier" 2. Sélectionner un PDF | Fichier attaché au ticket | ⏳ |

---

## MODULE 9 — Notifications

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| NOT-01 | Notification à la création d'un ticket IT | Ticket créé | 1. Créer ticket | Agents + Admins notifiés in-app | ⏳ |
| NOT-02 | Notification à l'affectation | Ticket affecté | 1. Affecter ticket | Technicien assigné + Demandeur notifiés | ⏳ |
| NOT-03 | Notification changement de statut | Statut modifié | 1. Changer statut | Demandeur + technicien notifiés | ⏳ |
| NOT-04 | Notification réponse info | Réponse fournie | 1. Répondre à demande d'info | Technicien assigné notifié | ⏳ |
| NOT-05 | Cloche affiche compteur non lu | Notifications non lues | 1. Voir le badge sur la cloche | Compteur correct | ⏳ |
| NOT-06 | "Tout lire" vide le compteur | Notifications non lues | 1. Cliquer "Tout lire" | Badge disparaît | ⏳ |

---

## MODULE 10 — Recherche de tickets

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| SCH-01 | Recherche par référence exacte | Ticket `OMCM-DSI-00003` existant | 1. Saisir `OMCM-DSI-00003` dans la barre de recherche navbar | Redirection directe vers le ticket | ⏳ |
| SCH-02 | Recherche insensible à la casse | Suite SCH-01 | 1. Saisir `omcm-dsi-00003` | Même résultat | ⏳ |
| SCH-03 | Référence inexistante → fallback liste | — | 1. Saisir `OMCM-DSI-99999` | Redirection vers liste avec ce terme en filtre | ⏳ |
| SCH-04 | Référence existante mais accès refusé | Ticket d'un autre département | 1. Saisir la référence | Message d'erreur, pas de redirection vers le ticket | ⏳ |
| SCH-05 | Recherche par mot-clé dans la liste | — | 1. Filtrer par mot-clé dans la liste | Résultats filtrés par numéro/titre/description | ⏳ |

---

## MODULE 11 — Activation des départements (Admin)

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| DEP-01 | Admin active un département | Dept Finance existant | 1. Django Admin → Département Finance 2. Cocher `ticketing_enabled` 3. Choisir un manager 4. Sauvegarder | Dept activé, manager assigné | ⏳ |
| DEP-02 | Champ target_department visible après activation | Suite DEP-01 | 1. Demandeur ouvre formulaire création ticket | Champ "Envoyer vers" visible avec Finance dans la liste | ⏳ |
| DEP-03 | Un seul manager par département | Dept déjà avec manager | 1. Essayer d'assigner un 2e manager | Seul le dernier manager assigné est actif | ⏳ |

---

## MODULE 12 — Visibilité et accès

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| VIS-01 | Demandeur ne voit que les tickets de son département | Connecté Demandeur | 1. Aller sur `/tickets/` | Uniquement tickets créés par des membres de son département | ⏳ |
| VIS-02 | Technicien voit tous les tickets IT | Connecté Technicien | 1. Aller sur `/tickets/` | Tous les tickets IT visibles | ⏳ |
| VIS-03 | Agent voit onglet "Autres directions" | Connecté Agent | 1. Liste tickets | Onglet "Autres directions" visible | ⏳ |
| VIS-04 | Demandeur n'a pas d'onglet "Autres directions" | Connecté Demandeur | 1. Liste tickets | Onglet absent | ⏳ |
| VIS-05 | Onglet Projets visible uniquement IT | Connecté membre IT | 1. Sidebar | Onglet Projets présent | ⏳ |
| VIS-06 | Onglet Projets invisible pour non-IT | Connecté Demandeur non-IT | 1. Sidebar | Onglet Projets absent | ⏳ |
| VIS-07 | Accès direct URL ticket sans droits | URL ticket d'un autre dept | 1. Copier/coller l'URL | Message "introuvable ou droits insuffisants", redirection liste | ⏳ |

---

## MODULE 13 — Reporting et export

| ID | Cas de test | Préconditions | Étapes | Résultat attendu | Statut |
|----|-------------|---------------|--------|------------------|--------|
| RPT-01 | Export CSV | Connecté Admin | 1. Cliquer "CSV" dans la liste | Fichier CSV téléchargé avec tous les tickets visibles | ⏳ |
| RPT-02 | Export Excel | Connecté Admin | 1. Cliquer "Excel" | Fichier XLSX téléchargé | ⏳ |
| RPT-03 | Pagination fonctionne | > 25 tickets | 1. Utiliser les boutons de pagination | Navigation correcte entre les pages | ⏳ |
| RPT-04 | Sélecteur "éléments par page" | — | 1. Changer à 10/50/100 | La liste se recharge avec le bon nombre d'éléments | ⏳ |
