# ============================================================
# deploy.ps1 — Script de Deploy a Producción
# Uso: .\deploy.ps1
# Mergea dev → main y pushea UNA SOLA VEZ a GitHub/Render
# ============================================================

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEPLOY A PRODUCCION (dev → main)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que estamos en dev
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -ne "dev") {
    Write-Host "  ERROR: Tenes que estar en la rama 'dev' para hacer deploy." -ForegroundColor Red
    Write-Host "  Corré: git checkout dev" -ForegroundColor Yellow
    exit 1
}

# 2. Verificar que el servidor local funciona
Write-Host "  [1/4] Verificando que el codigo Python es valido..." -ForegroundColor Yellow
$check = python -c "import app; print('OK')" 2>&1
if ($check -notmatch "OK") {
    Write-Host "  ERROR: El codigo tiene errores de Python. Corregi los bugs antes de deployar." -ForegroundColor Red
    Write-Host "  $check" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Codigo Python valido" -ForegroundColor Green

# 3. Commitear cualquier cambio pendiente en dev
$status = git status --porcelain
if ($status) {
    Write-Host "  [2/4] Commiteando cambios pendientes en dev..." -ForegroundColor Yellow
    git add .
    $msg = Read-Host "  Descripcion del deploy (Enter para usar fecha)"
    if ([string]::IsNullOrWhiteSpace($msg)) {
        $msg = "deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    git commit -m $msg
} else {
    Write-Host "  [2/4] Sin cambios pendientes en dev" -ForegroundColor Green
}

# 4. Merge dev → main y push
Write-Host "  [3/4] Mergeando dev → main..." -ForegroundColor Yellow
git checkout main
git pull --rebase origin main
git merge dev --no-ff -m "deploy: merge dev → main ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"

Write-Host "  [4/4] Pusheando a GitHub (1 solo deploy en Render)..." -ForegroundColor Yellow
git push origin main

# 5. Volver a dev para seguir trabajando
git checkout dev

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  ✅ DEPLOY COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "  Render va a construir el nuevo deploy en ~3-5 minutos." -ForegroundColor Green
Write-Host "  Ya estás de vuelta en la rama 'dev' para seguir." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
