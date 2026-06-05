# Plan de Tests — QoS Ticketing

**Projet :** QoS Ticketing  
**Version :** 1.0  
**Date :** Juin 2026  
**Statut :** Draft  
**Auteur :** Équipe DSI  

---

## 1. Objet du document

Ce document définit la stratégie, le périmètre et l'organisation des tests de la plateforme **QoS Ticketing**. Il s'adresse aux équipes de développement, de recette et de pilotage.

---

## 2. Périmètre des tests

### 2.1 Fonctionnalités couvertes

| Module | Description |
|--------|-------------|
| Authentification | Connexion, déconnexion, gestion des sessions |
| Gestion des utilisateurs | Création, modification, rôles, départements |
| Création de tickets | Formulaire, validation, numérotation automatique |
| Cycle de vie des tickets | Transitions de statut, affectation, ball-in-court |
| Gestion SLA | Déclenchement, pause, reprise, alertes |
| Demande d'information | Envoi, réponse, transfert de responsabilité |
| Commentaires & pièces jointes | Ajout, visibilité, @mentions |
| Notifications | In-app, email, déclencheurs |
| Gestion des départements | Activation ticketing, attribution manager |
| Transfert inter-départements | Routing agent → manager |
| Projets (IT) | Création, sprints, épics, tâches |
| Reporting | Export CSV, Excel, KPIs |
| API REST | Endpoints, authentification, réponses |
| Administration | Django Admin, configuration SLA |

### 2.2 Hors périmètre

- Tests de charge / performance
- Tests de sécurité avancés (pentest)
- Tests d'accessibilité WCAG
- Compatibilité navigateurs mobiles (hors Chrome/Firefox desktop)

---

## 3. Types de tests

### 3.1 Tests fonctionnels
Vérification que chaque fonctionnalité se comporte conformément aux spécifications.

### 3.2 Tests d'intégration
Vérification des interactions entre modules (ex. : création ticket → notification → SLA).

### 3.3 Tests de non-régression
Après chaque évolution, vérification que les fonctionnalités existantes ne sont pas impactées.

### 3.4 Tests de recette (UAT)
Validation par les utilisateurs métier dans un environnement représentatif de la production.

---

## 4. Environnement de test

| Paramètre | Valeur |
|-----------|--------|
| URL de test | `http://localhost:8000` |
| Base de données | SQLite (`db.sqlite3`) |
| Serveur | Django development server |
| Navigateurs | Chrome 124+, Firefox 125+ |
| Email | Backend console Django (pas d'envoi réel) |

### 4.1 Données de test requises

Avant le début des tests, les éléments suivants doivent être créés :

- [ ] 1 département IT (`is_it_department=True`, code `DSI`)
- [ ] 1 département non-IT activé (ex. Finance, `ticketing_enabled=True`)
- [ ] 1 utilisateur par rôle : Admin, Agent, Technicien, Manager, Demandeur, Observateur
- [ ] 1 configuration SLA pour chaque priorité (P0, P1, P2, P3)
- [ ] Au moins 3 catégories de tickets

---

## 5. Rôles et responsabilités

| Rôle | Responsabilité |
|------|----------------|
| Chef de projet | Validation du plan, suivi des anomalies |
| Développeur | Correction des anomalies, support technique |
| Testeur fonctionnel | Exécution des cas de tests, rapports |
| Utilisateur métier | Tests de recette UAT |

---

## 6. Critères d'entrée et de sortie

### 6.1 Critères d'entrée (début des tests)
- Environnement de test opérationnel
- Données de test chargées
- Accès aux comptes de test confirmés
- Cas de tests validés et prêts

### 6.2 Critères de sortie (fin des tests / recette)
- 100 % des cas de tests critiques (P0) passés
- ≥ 95 % des cas de tests P1 passés
- Aucune anomalie bloquante ouverte
- Rapport de recette signé par le responsable métier

---

## 7. Gestion des anomalies

### 7.1 Niveaux de sévérité

| Niveau | Définition | Délai de correction |
|--------|------------|---------------------|
| **Bloquant** | Fonctionnalité critique inutilisable | Immédiat (avant recette) |
| **Majeur** | Fonctionnalité altérée mais contournement possible | Sous 48h |
| **Mineur** | Comportement incorrect sans impact majeur | Prochain sprint |
| **Cosmétique** | Problème d'affichage, libellé incorrect | Backlog |

### 7.2 Cycle de vie d'une anomalie

```
Détectée → Saisie → Assignée → En correction → Corrigée → Vérifiée → Fermée
```

---

## 8. Planning indicatif

| Phase | Durée | Activité |
|-------|-------|----------|
| Préparation | 1 jour | Création données de test, accès |
| Tests fonctionnels | 3 jours | Exécution des cas de tests |
| Correction anomalies | 2 jours | Correction + retests |
| Recette UAT | 2 jours | Validation utilisateurs métier |
| Bilan et clôture | 1 jour | Rapport final, go/no-go |

---

## 9. Livrables issus des tests

- `02_cas_de_tests.md` — Matrice des cas de tests avec résultats
- `03_rapport_de_recette.md` — Rapport de recette signé
- Liste des anomalies (fichier suivi)
