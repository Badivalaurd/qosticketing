# Plan de Maintenance — QoS Ticketing

**Version :** 1.0 | **Date :** Juin 2026  
**Auteur :** Équipe DSI

---

## 1. Objectif

Ce document décrit les procédures de maintenance préventive, corrective et évolutive de la plateforme QoS Ticketing, ainsi que les responsabilités associées.

---

## 2. Environnements

| Environnement | URL | Base de données | Responsable |
|---------------|-----|-----------------|-------------|
| Développement | `localhost:8000` | SQLite (local) | Développeurs |
| Test/Recette | `username.pythonanywhere.com` | SQLite | DSI |
| Production | `qos.omcm.dz` (à configurer) | PostgreSQL | DSI + Admin |

---

## 3. Sauvegardes

### 3.1 Base de données SQLite (test)

```bash
# Sauvegarde manuelle
cp ~/qos-ticketing/db.sqlite3 ~/backups/db_$(date +%Y%m%d).sqlite3
```

Fréquence recommandée : **quotidienne**.

### 3.2 Base de données PostgreSQL (production)

```bash
# Dump complet
pg_dump -U qos_user -h localhost qos_ticketing > ~/backups/db_$(date +%Y%m%d).sql

# Restauration
psql -U qos_user -h localhost qos_ticketing < ~/backups/db_20260605.sql
```

Fréquence recommandée : **quotidienne** (automatisée via cron).

### 3.3 Fichiers media (uploads)

```bash
# Copie du répertoire media
cp -r ~/qos-ticketing/media/ ~/backups/media_$(date +%Y%m%d)/
```

Fréquence recommandée : **hebdomadaire**.

### 3.4 Rétention des sauvegardes

| Type | Durée de rétention |
|------|--------------------|
| Sauvegardes quotidiennes | 30 jours |
| Sauvegardes hebdomadaires | 6 mois |
| Sauvegardes mensuelles | 2 ans |

---

## 4. Mises à jour

### 4.1 Mise à jour de l'application (code)

```bash
cd ~/qos-ticketing
source venv/bin/activate
git pull origin master          # ou develop selon l'environnement

pip install -r requirements.txt # Si nouvelles dépendances
python manage.py migrate        # Si nouvelles migrations
python manage.py collectstatic --noinput
```

Puis recharger via le tableau de bord PythonAnywhere.

**Avant toute mise à jour en production :**
1. Effectuer une sauvegarde complète (DB + media)
2. Tester en environnement de recette d'abord
3. Planifier une fenêtre de maintenance (notifier les utilisateurs)

### 4.2 Mise à jour des dépendances Python

```bash
pip list --outdated                         # Lister les packages à jour
pip install --upgrade nom-du-package        # Mettre à jour un package
pip freeze > requirements.txt               # Mettre à jour le fichier
```

**Fréquence recommandée :** Mensuelle pour les correctifs de sécurité ; trimestrielle pour les mises à jour mineures.

### 4.3 Mise à jour de Django

Toute mise à jour majeure de Django (ex. 5.x → 6.x) doit faire l'objet d'une branche dédiée, de tests complets, et d'une recette avant déploiement.

---

## 5. Surveillance

### 5.1 Logs d'erreur

Sur PythonAnywhere, les logs sont accessibles dans :
- **Tableau de bord → Files** : `var/log/username.pythonanywhere.com.error.log`
- **Tableau de bord → Files** : `var/log/username.pythonanywhere.com.access.log`

### 5.2 Indicateurs à surveiller

| Indicateur | Seuil d'alerte | Action |
|------------|---------------|--------|
| Tickets en dépassement SLA | > 10% du total | Revoir la charge/priorités |
| Tickets NOUVEAU sans affectation depuis > 4h | > 5 | Relancer l'agent support |
| Erreurs 500 dans les logs | > 5/heure | Investigation immédiate |
| Espace disque utilisé | > 80% | Archivage ou extension |
| Temps de réponse moyen des pages | > 3 secondes | Optimisation requêtes |

### 5.3 Commandes de diagnostic

```bash
# Vérifier la configuration de déploiement
python manage.py check --deploy

# Lister les migrations en attente
python manage.py showmigrations | grep '\[ \]'

# Compter les sessions actives
python manage.py shell -c "from django.contrib.sessions.models import Session; print(Session.objects.count())"

# Vider les sessions expirées
python manage.py clearsessions
```

---

## 6. Procédures de maintenance

### 6.1 Maintenance planifiée (mensuelle)

Checklist à effectuer le premier lundi de chaque mois :

- [ ] Vérifier les logs d'erreur du mois écoulé
- [ ] Vérifier l'espace disque (DB + media)
- [ ] Appliquer les correctifs de sécurité des dépendances
- [ ] Vider les sessions expirées (`clearsessions`)
- [ ] Vérifier que les sauvegardes automatiques fonctionnent
- [ ] Revoir les comptes utilisateurs inactifs (désactiver si nécessaire)
- [ ] Consulter les KPIs SLA du mois (tableau de bord)

### 6.2 Maintenance corrective (incidents)

**Procédure de gestion d'incident :**

1. **Détection** : log d'erreur, signalement utilisateur, alerte monitoring
2. **Qualification** : sévérité (critique, haute, normale), périmètre impacté
3. **Restauration** : rollback si nécessaire (git revert + restauration DB)
4. **Investigation** : lecture des logs, reproduction en environnement de test
5. **Correction** : correction sur branche dédiée, tests, déploiement
6. **Post-mortem** : documenter l'incident et les mesures correctives

### 6.3 Rollback d'urgence

```bash
# Revenir au dernier commit stable
git log --oneline -10      # Identifier le commit cible
git checkout <commit-hash>  # Ou git revert HEAD

# Puis re-déployer
python manage.py migrate
python manage.py collectstatic --noinput
# Recharger PythonAnywhere
```

---

## 7. Gestion des accès

| Action | Fréquence | Responsable |
|--------|-----------|-------------|
| Revue des comptes actifs | Mensuelle | Admin |
| Révocation des comptes départ | Immédiate | Admin |
| Rotation des credentials SMTP | Semestrielle | DSI |
| Rotation de la SECRET_KEY | Annuelle | DSI |
| Audit des rôles attribués | Trimestrielle | Admin |

---

## 8. Contacts et escalade

| Niveau | Rôle | Déclencheur |
|--------|------|-------------|
| N1 | Agent de support | Signalement utilisateur standard |
| N2 | Administrateur système | Bug critique, accès impossible |
| N3 | Développeur | Incident applicatif nécessitant un correctif code |

---

## 9. Évolutions planifiées

| Version | Fonctionnalité | Priorité | Horizon |
|---------|----------------|----------|---------|
| v1.1 | Module projets IT complet (sprints, épics) | Haute | T3 2026 |
| v1.2 | Portail self-service demandeurs (FAQ, statuts) | Normale | T4 2026 |
| v1.3 | Tableaux de bord avancés (graphiques, export PDF) | Normale | T1 2027 |
| v2.0 | Migration PostgreSQL + déploiement production | Haute | T3 2026 |
