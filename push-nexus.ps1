# ── Configuration ────────────────────────────────────────────────────────────
$NEXUS_HOST  = "nexus.orange.cm"
$NEXUS_PORT  = "5001"
$IMAGE_NAME  = "ittis-web"

# Tag versionné automatique : YYYY-MM-DD-HHmm  (ex: 2026-10-02-1430)
$VERSION_TAG = (Get-Date -Format "yyyy-MM-dd-HHmm")

$REGISTRY    = "${NEXUS_HOST}:${NEXUS_PORT}"
$VERSIONED   = "${REGISTRY}/${IMAGE_NAME}:${VERSION_TAG}"
$LATEST      = "${REGISTRY}/${IMAGE_NAME}:latest"

# ── Couleurs ─────────────────────────────────────────────────────────────────
function Ok($msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Err($msg)  { Write-Host "  [FAIL] $msg" -ForegroundColor Red }
function Info($msg) { Write-Host "  [INFO] $msg" -ForegroundColor Cyan }
function Step($msg) { Write-Host "`n── $msg ──" -ForegroundColor Yellow }

# ── 1. Build ─────────────────────────────────────────────────────────────────
Step "Build de l'image Docker"
Info "Version : $VERSION_TAG"

docker build --provenance=false -t "${IMAGE_NAME}:${VERSION_TAG}" .
if ($LASTEXITCODE -ne 0) { Err "Build échoué."; exit 1 }
Ok "Build réussi."

# ── 2. Tag ───────────────────────────────────────────────────────────────────
Step "Tag pour Nexus"
docker tag "${IMAGE_NAME}:${VERSION_TAG}" $VERSIONED
if ($LASTEXITCODE -ne 0) { Err "Tag versionné échoué."; exit 1 }
docker tag "${IMAGE_NAME}:${VERSION_TAG}" $LATEST
if ($LASTEXITCODE -ne 0) { Err "Tag latest échoué."; exit 1 }
Ok "Tags créés : $VERSION_TAG  +  latest"

# ── 3. Login ─────────────────────────────────────────────────────────────────
Step "Connexion au registry Nexus"
Info "Registry : $REGISTRY"
docker login $REGISTRY
if ($LASTEXITCODE -ne 0) { Err "Login échoué. Vérifiez vos identifiants Nexus."; exit 1 }
Ok "Connecté."

# ── 4. Push ──────────────────────────────────────────────────────────────────
Step "Push vers Nexus"
docker push $VERSIONED
if ($LASTEXITCODE -ne 0) { Err "Push versionné échoué."; exit 1 }
Ok "Poussé : $VERSIONED"

docker push $LATEST
if ($LASTEXITCODE -ne 0) { Err "Push latest échoué."; exit 1 }
Ok "Poussé : $LATEST"

# ── Résumé ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Ok "Déploiement Nexus terminé."
Info "Version  : $VERSIONED"
Info "Latest   : $LATEST"
Write-Host ""
Info "Pour déployer cette version précise dans OpenShift :"
Write-Host "  image: $VERSIONED" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
