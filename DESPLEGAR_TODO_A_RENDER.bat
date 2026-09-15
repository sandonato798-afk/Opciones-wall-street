@echo off
title Autoconfigurador y Desplegador a Render (Opciones Wall Street)
cls
echo ====================================================================
echo    AUTOCONFIGURADOR Y DESPLEGADOR AUTOMATICO A RENDER.COM
echo ====================================================================
echo.
echo  1. Verificando estructura de archivos (render.yaml, app.py, Procfile)...
echo  2. Inicializando Git y vinculando a GitHub...
echo  3. Subiendo cambios a https://github.com/sandonato798-afk/Opciones-wall-street.git
echo.

cd /d "%~dp0"

:: Initialize and push to GitHub
git init >nul 2>&1
git config --global user.name "Santiago Donato" >nul 2>&1
git config --global user.email "sandonato798@gmail.com" >nul 2>&1
git add .
git commit -m "Auto-deploy Render configuration and Options Web Dashboard" >nul 2>&1
git branch -M main >nul 2>&1
git remote remove origin >nul 2>&1
git remote add origin https://github.com/sandonato798-afk/Opciones-wall-street.git >nul 2>&1
git push -u origin main --force

echo ====================================================================
echo  ¡EXITO! Todo el codigo ha sido subido a tu GitHub.
echo.
echo  Abriendo Render.com en tu navegador...
echo  Solo haz clic en "Connect" junto a tu repo 'Opciones-wall-street'.
echo ====================================================================
echo.

start https://dashboard.render.com/select-repo?type=web

pause
