# ══════════════════════════════════════════════════════════════════════════════
# package-deploy.ps1 — Construit l'image et prépare le package pour déploiement
#
# Usage :  .\package-deploy.ps1
# Résultat : dossier  ittis-deploy/
#              ittis-web.tar          image Docker (~400 Mo)
#              ittis-openshift.yaml   manifeste OpenShift prêt à appliquer
#              README.txt             instructions pour le collègue
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$OUT = "ittis-deploy"

Write-Host ""
Write-Host "==> Build de l'image Docker..." -ForegroundColor Cyan
docker build -t ittis-web:latest .

Write-Host ""
Write-Host "==> Export de l'image en fichier tar..." -ForegroundColor Cyan
if (-not (Test-Path $OUT)) { New-Item -ItemType Directory -Path $OUT | Out-Null }
docker save ittis-web:latest -o "$OUT\ittis-web.tar"

Write-Host ""
Write-Host "==> Copie du manifeste OpenShift..." -ForegroundColor Cyan
Copy-Item "openshift\ittis-openshift.yaml" "$OUT\ittis-openshift.yaml"

Write-Host ""
Write-Host "==> Génération du README..." -ForegroundColor Cyan
@"
ITTIS — Package de déploiement OpenShift Local
================================================

Contenu de ce dossier :
  ittis-web.tar          Image Docker de l'application
  ittis-openshift.yaml   Manifeste OpenShift (tous les composants)
  README.txt             Ce fichier

AVANT DE DÉPLOYER — modifier ittis-openshift.yaml :
  1. Ligne ~18 : remplacer SECRET_KEY par une vraie clé
     Générer : python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  2. Vérifier DB_PASSWORD (ligne ~20) correspond à votre MariaDB

DÉPLOIEMENT :

  # 1. Charger l'image
  podman load -i ittis-web.tar

  # 2. Vérifier que l'image est là
  podman images | grep ittis

  # 3. Déployer sur OpenShift (CRC doit être démarré : crc start)
  oc apply -f ittis-openshift.yaml

  # 4. Surveiller le déploiement
  oc get pods -n ittis -w

  # 5. Obtenir l'URL
  oc get route ittis -n ittis

  # 6. Créer le superuser Django (une seule fois)
  oc exec -it deployment/ittis-web -c web -n ittis -- python manage.py createsuperuser

L'app sera accessible sur https://ittis-ittis.apps-crc.testing

IMPORTANT : Vous devez être sur le réseau Orange (bureau ou VPN)
pour que les migrations puissent atteindre la base de données MariaDB.
"@ | Out-File -Encoding UTF8 "$OUT\README.txt"

Write-Host ""
Write-Host "✓ Package prêt dans le dossier : $OUT\" -ForegroundColor Green
Write-Host ""
Write-Host "  Fichiers :" -ForegroundColor White
Get-ChildItem $OUT | ForEach-Object {
    $size = if ($_.Length -gt 1MB) { "{0:N0} Mo" -f ($_.Length / 1MB) } else { "{0:N0} Ko" -f ($_.Length / 1KB) }
    Write-Host ("    {0,-35} {1}" -f $_.Name, $size) -ForegroundColor Gray
}
Write-Host ""
Write-Host "  Transférez le dossier '$OUT\' à votre collègue." -ForegroundColor Yellow
Write-Host ""
