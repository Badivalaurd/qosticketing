# Glossaire — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## Termes métier

**Agent de support**  
Rôle IT chargé de la distribution des tickets entrants vers les techniciens. L'agent voit tous les tickets (IT et autres directions) et peut transférer, rejeter, clôturer ou changer la priorité d'un ticket.

**Ball-in-court**  
Concept de responsabilité instantanée inspiré de Jira. À tout moment, un seul acteur est "en possession du ticket" (champ `responsable`). Cela permet de savoir immédiatement qui doit agir sans ambiguïté.

**Clôture**  
Statut terminal d'un ticket après résolution confirmée. Un ticket clôturé est verrouillé définitivement — aucune modification n'est possible.

**Demandeur**  
Tout employé de l'OMCM qui soumet une demande d'assistance. C'est le rôle par défaut de tout utilisateur créé.

**Département activé**  
Département non-IT pour lequel l'administrateur a activé la réception de tickets (`ticketing_enabled=True`) et désigné un manager. Un département non activé ne peut recevoir de tickets.

**Demande d'information (DI)**  
Mécanisme permettant au technicien de solliciter des clarifications auprès d'un utilisateur. Pendant ce temps, le SLA est mis en pause et la responsabilité passe à la personne sollicitée.

**Dépassement SLA**  
Situation où le délai contractuel (prise en charge ou résolution) est écoulé sans que l'action correspondante ait été réalisée. Génère une alerte automatique.

**Distribution**  
Acte par lequel un agent (pour l'IT) ou un manager (pour un autre département) affecte un ticket à un membre de son équipe.

**IT / DSI**  
Département Informatique (Direction des Systèmes d'Information). Seul département pouvant avoir le champ `is_it_department=True`.

**Manager**  
Rôle attribué par l'admin à un membre d'un département activé. Il distribue les tickets entrants dans son département. Le manager IT a un rôle différent (gestion de projets).

**Mention (@mention)**  
Tag textuel dans un commentaire (`@admin`, `@agent`, `@username`) déclenchant une notification ciblée.

**Observateur**  
Rôle donnant un accès en lecture seule aux tickets sur lesquels il est désigné.

**Prise en charge**  
Action par laquelle un technicien accepte officiellement un ticket (passage de AFFECTÉ à EN_COURS). Différent du "transfert" qui ne constitue pas une prise en charge.

**Priorité**  
Niveau d'urgence d'un ticket (P0 Critique, P1 Haute, P2 Normale, P3 Basse). Détermine les délais SLA applicables.

**QoS (Quality of Service)**  
Qualité de service — mesurée ici via le respect des délais SLA et la satisfaction des demandeurs.

**Référence de ticket**  
Identifiant unique lisible : `OMCM-{CODE_DEPT}-{NNNNN}`. Exemple : `OMCM-DSI-00042`. Le code département est celui du département receveur.

**Responsable courant**  
Champ `responsable` sur le ticket — indique qui "détient le ticket" à l'instant t (ball-in-court). Peut être différent du technicien assigné en cas de demande d'information.

**Rejet**  
Décision de l'agent ou du manager de ne pas traiter un ticket (hors périmètre, doublon, demande invalide). Requiert obligatoirement un motif.

**SLA (Service Level Agreement)**  
Engagement de délais de traitement. Deux délais : prise en charge et résolution. Le compteur se met en pause sur les statuts ATTENTE_INFO et ATTENTE_PRESTATAIRE.

**Technicien**  
Membre de l'IT chargé du traitement opérationnel des tickets qui lui sont affectés.

**Transfert inter-département**  
Action de router un ticket NOUVEAU vers le manager d'un autre département activé. Le ticket reste en statut NOUVEAU — ce n'est pas une prise en charge IT.

---

## Termes techniques

**Django**  
Framework web Python suivant l'architecture MVT (Model-View-Template). Base technologique du projet.

**Django Admin**  
Interface d'administration automatique de Django accessible sur `/admin/`. Réservée aux utilisateurs `is_staff=True`.

**DRF (Django REST Framework)**  
Extension Django pour la construction d'API REST. Utilisée pour exposer les données de l'application aux clients API.

**Migration**  
Fichier Python généré par Django qui décrit une modification du schéma de base de données. Appliqué avec `python manage.py migrate`.

**ORM (Object-Relational Mapping)**  
Couche d'abstraction Django permettant d'interagir avec la base de données via des objets Python plutôt que du SQL brut.

**PythonAnywhere**  
Hébergeur web spécialisé Python. Utilisé pour le déploiement du projet (gratuit en test, payant en production).

**SQLite**  
Moteur de base de données fichier, sans serveur. Utilisé en développement et test. Remplacé par PostgreSQL en production.

**PostgreSQL**  
Moteur de base de données relationnelle robuste. Recommandé pour la production.

**Session**  
Mécanisme d'authentification web — l'identité de l'utilisateur est maintenue via un cookie de session entre les requêtes.

**SLA pausé**  
État où le compteur SLA est suspendu. Survient automatiquement lors des statuts ATTENTE_INFO et ATTENTE_PRESTATAIRE.

**Whitenoise**  
Bibliothèque Python servant les fichiers statiques (CSS, JS, images) directement depuis Django/Gunicorn sans serveur web externe (nginx).

**WSGI**  
Interface standard Python pour les serveurs web. PythonAnywhere utilise ce protocole pour communiquer avec l'application Django.

---

## Abréviations

| Abréviation | Signification |
|-------------|---------------|
| OMCM | Organisation (nom de l'institution cliente) |
| DSI | Direction des Systèmes d'Information |
| DI | Demande d'Information |
| SLA | Service Level Agreement |
| QoS | Quality of Service |
| KPI | Key Performance Indicator |
| MVT | Model-View-Template (architecture Django) |
| DRF | Django REST Framework |
| ORM | Object-Relational Mapping |
| SMTP | Simple Mail Transfer Protocol |
| WSGI | Web Server Gateway Interface |
| FK | Foreign Key (clé étrangère en base de données) |
| CRUD | Create, Read, Update, Delete |
