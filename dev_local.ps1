# ============================================================
# dev_local.ps1 — Servidor Local de Desarrollo
# Emula exactamente el entorno de Render en tu PC
# Uso: .\dev_local.ps1
# Dashboard: http://localhost:10000
# ============================================================

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "  SERVIDOR LOCAL DE DESARROLLO" -ForegroundColor Magenta
Write-Host "  Emulando entorno Render en modo DEV" -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host ""

# Verificar que estamos en dev (no en main)
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -eq "main") {
    Write-Host "  ADVERTENCIA: Estás en 'main'. Para desarrollo usá 'dev'." -ForegroundColor Yellow
    Write-Host "  Corré: git checkout dev" -ForegroundColor Yellow
    Write-Host ""
}

# Setear variables de entorno que Render inyecta en la nube
$env:PORT = "10000"
$env:RENDER_EXTERNAL_URL = "http://localhost:10000"
$env:PYTHON_VERSION = "3.11.9"

# Leer GITHUB_TOKEN del archivo local si existe
$tokenFile = ".github_token"
if (Test-Path $tokenFile) {
    $env:GITHUB_TOKEN = Get-Content $tokenFile -Raw
    $env:GITHUB_TOKEN = $env:GITHUB_TOKEN.Trim()
    Write-Host "  ✅ GITHUB_TOKEN cargado desde .github_token" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  GITHUB_TOKEN no encontrado (cloud sync desactivado)" -ForegroundColor Yellow
}

Write-Host "  ✅ Variables de entorno configuradas (emulando Render)" -ForegroundColor Green
Write-Host "  📡 Iniciando servidor en http://localhost:10000" -ForegroundColor Cyan
Write-Host "  🔴 Presioná Ctrl+C para detener" -ForegroundColor Red
Write-Host ""

# Arrancar el servidor
python app.py
