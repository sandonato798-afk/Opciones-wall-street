# ============================================================
# deploy.ps1 — Script de Deploy a Producción
# Uso: .\deploy.ps1
#
# FLUJO:
#   1. Valida que el código Python no tiene errores
#   2. Commitea y pushea dev → GitHub (backup de código, sin build)
#   3. Llama al Deploy Hook de Render → 1 solo build en la nube
# ============================================================

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  DEPLOY A PRODUCCION" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que estamos en dev
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -eq "main") {
    Write-Host "  ERROR: Tenes que estar en la rama 'dev' para hacer deploy." -ForegroundColor Red
    Write-Host "  Corré: git checkout dev" -ForegroundColor Yellow
    exit 1
}

# 2. Verificar que el código Python es válido antes de deployar
Write-Host "  [1/4] Verificando codigo Python..." -ForegroundColor Yellow
$check = python -c "import app; print('OK')" 2>&1
if ($check[-1] -notmatch "OK") {
    Write-Host "  ERROR: El codigo tiene errores. Corregi los bugs antes de deployar:" -ForegroundColor Red
    Write-Host "  $check" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Codigo Python valido" -ForegroundColor Green

# 3. Commitear cambios pendientes en dev
$status = git status --porcelain
if ($status) {
    Write-Host "  [2/4] Commiteando cambios en rama 'dev'..." -ForegroundColor Yellow
    git add .
    $msg = Read-Host "  Descripcion del deploy (Enter para fecha automatica)"
    if ([string]::IsNullOrWhiteSpace($msg)) {
        $msg = "deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    }
    git commit -m $msg
} else {
    Write-Host "  [2/4] Sin cambios pendientes" -ForegroundColor Green
}

# 4. Pushear dev a GitHub (solo backup de código, NO dispara build en Render)
Write-Host "  [3/4] Pusheando rama 'dev' a GitHub (sin build en Render)..." -ForegroundColor Yellow
git push origin dev
Write-Host "  ✅ Código respaldado en GitHub rama 'dev'" -ForegroundColor Green

# 5. Disparar el build en Render via Deploy Hook
Write-Host "  [4/4] Disparando build en Render via Deploy Hook..." -ForegroundColor Yellow
$hookFile = ".render_hook"
if (-not (Test-Path $hookFile)) {
    Write-Host "  ERROR: No se encontró el archivo '.render_hook'." -ForegroundColor Red
    Write-Host "  Crealo con la URL del Deploy Hook de Render." -ForegroundColor Yellow
    exit 1
}

$hookUrl = (Get-Content $hookFile -Raw).Trim()

try {
    $response = Invoke-WebRequest -Uri $hookUrl -Method POST -UseBasicParsing -TimeoutSec 15
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 201) {
        Write-Host "  ✅ Deploy iniciado en Render correctamente" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Render respondió con código $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR llamando al Deploy Hook: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  OK DEPLOY COMPLETADO" -ForegroundColor Green
Write-Host "  Render va a construir el nuevo deploy en ~3-5 minutos." -ForegroundColor Green
Write-Host "  El codigo en 'main' NO fue tocado, solo 'dev' se pusheo." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
