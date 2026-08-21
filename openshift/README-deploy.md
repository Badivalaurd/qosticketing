# ITTIS — Déploiement OpenShift Local (CRC)

Guide pas-à-pas pour déployer ITTIS sur OpenShift Local (Code Ready Containers).

---

## Pré-requis

| Outil | Version minimale |
|-------|-----------------|
| CRC (OpenShift Local) | ≥ 2.32 |
| `oc` CLI | ≥ 4.14 |
| `docker` ou `podman` | dernière stable |

```bash
# Vérifier que CRC est démarré
crc status
# Si ce n'est pas le cas :
crc start
```

---

## Étape 1 — Build de l'image

```bash
# Se connecter au registre interne CRC
eval $(crc podman-env)         # ou : eval $(crc docker-env)

# Login au registre OpenShift (CRC)
oc login -u kubeadmin https://api.crc.testing:6443
oc login -u kubeadmin -p $(crc console --credentials | grep kubeadmin | awk '{print $NF}')

# Créer d'abord le namespace (pour que le registre accepte le push)
oc apply -f openshift/00-namespace.yaml

# Login au registre interne
podman login -u kubeadmin -p $(oc whoami -t) \
  default-route-openshift-image-registry.apps-crc.testing --tls-verify=false

# Build et push depuis la racine du projet
IMAGE="default-route-openshift-image-registry.apps-crc.testing/ittis/ittis-web:latest"

podman build -t $IMAGE .
podman push $IMAGE --tls-verify=false
```

> **Note** : Remplacez `podman` par `docker` si vous utilisez Docker Desktop.

---

## Étape 2 — Configurer les secrets

Éditez `openshift/01-secret.yaml` et remplacez les valeurs placeholder :

```yaml
stringData:
  SECRET_KEY: "VOTRE-CLE-DJANGO-LONGUE-ET-ALEATOIRE"
  DB_PASSWORD: "2BwJ713gHIB8rkW"          # mot de passe MariaDB
  OIDC_RP_CLIENT_SECRET: "ac58ed16-..."   # secret Keycloak
  EMAIL_HOST_USER: ""                     # relay Orange — pas d'auth
  EMAIL_HOST_PASSWORD: ""
```

Générer une SECRET_KEY Django :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Étape 3 — Vérifier la ConfigMap

Éditez `openshift/02-configmap.yaml` si nécessaire :

- `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` → votre MariaDB externe
- `OIDC_KEYCLOAK_URL` / `OIDC_KEYCLOAK_REALM` → votre Keycloak
- `EMAIL_HOST` → relay SMTP Orange
- `ALLOWED_HOSTS` : le hostname de la Route sera affiché après l'étape 4

---

## Étape 4 — Remplacer `<IMAGE>` dans les Deployments

```bash
IMAGE="default-route-openshift-image-registry.apps-crc.testing/ittis/ittis-web:latest"

# Sur Linux/Mac :
sed -i "s|<IMAGE>|$IMAGE|g" openshift/05-deployment-web.yaml
sed -i "s|<IMAGE>|$IMAGE|g" openshift/06-deployment-celery.yaml
sed -i "s|<IMAGE>|$IMAGE|g" openshift/07-cronjob-celery-beat.yaml

# Sur Windows PowerShell :
# (Get-Content openshift/05-deployment-web.yaml) -replace '<IMAGE>', $IMAGE | Set-Content openshift/05-deployment-web.yaml
```

---

## Étape 5 — Appliquer tous les manifestes

```bash
# Ordre important : namespace → secrets → config → stockage → workloads → réseau
oc apply -f openshift/00-namespace.yaml
oc apply -f openshift/01-secret.yaml
oc apply -f openshift/02-configmap.yaml
oc apply -f openshift/03-pvc-media.yaml
oc apply -f openshift/04-deployment-redis.yaml
oc apply -f openshift/05-deployment-web.yaml
oc apply -f openshift/06-deployment-celery.yaml
oc apply -f openshift/07-cronjob-celery-beat.yaml
oc apply -f openshift/08-route.yaml
```

Ou tout d'un coup :
```bash
oc apply -f openshift/
```

---

## Étape 6 — Vérifier le déploiement

```bash
# Passer dans le namespace ittis
oc project ittis

# Surveiller les pods
oc get pods -w

# Logs du web
oc logs -f deployment/ittis-web -c web

# Logs des migrations (initContainer)
oc logs deployment/ittis-web -c migrate

# Obtenir l'URL de la Route
oc get route ittis
```

L'application sera accessible sur `https://ittis-ittis.apps-crc.testing`

---

## Étape 7 — Créer le superuser Django

```bash
# Entrer dans le pod web
oc exec -it deployment/ittis-web -c web -- bash

# Dans le pod :
python manage.py createsuperuser
```

---

## Mettre à jour l'image (re-déploiement)

```bash
podman build -t $IMAGE .
podman push $IMAGE --tls-verify=false

# Forcer le redémarrage des pods
oc rollout restart deployment/ittis-web
oc rollout restart deployment/ittis-celery
```

---

## Résolution de problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| Pod en `CrashLoopBackOff` | SECRET_KEY ou DB_PASSWORD incorrect | `oc logs pod/<nom>` → vérifier 01-secret.yaml |
| `403 Forbidden` sur `/` | ALLOWED_HOSTS ne contient pas le hostname CRC | Mettre à jour 02-configmap.yaml + `oc rollout restart` |
| Pod en `Pending` | PVC non provisionné | `oc describe pvc ittis-media` → vérifier StorageClass |
| Celery ne démarre pas | Redis non prêt | Attendre que le pod Redis soit `Running` |
| Migration échoue | BD externe inaccessible depuis CRC | Vérifier la connectivité réseau CRC → 172.26.76.252:3323 |

---

## Retour à la branche de développement

Ce déploiement est sur la branche `deploy/openshift-local`.  
Pour revenir au développement :

```bash
git checkout develop-keyclock
```

Les fichiers de déploiement (`Dockerfile`, `.dockerignore`, `openshift/`) ne sont **pas** présents sur `develop-keyclock` et n'interféreront pas avec votre workflow habituel.
