@echo off
title Subir Sistema de Opciones a GitHub
cls
echo ====================================================================
echo      SUBIENDO SISTEMA DE OPCIONES A GITHUB
echo ====================================================================
echo.
echo  Repositorio: https://github.com/sandonato798-afk/Opciones-wall-street.git
echo.

cd /d "%~dp0"

git init
git add .
git commit -m "Initial commit - Sistema de Opciones Wall Street ETFs"
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin https://github.com/sandonato798-afk/Opciones-wall-street.git
git push -u origin main

echo.
echo ====================================================================
echo  ¡Listo! Archivos subidos exitosamente a GitHub.
echo ====================================================================
pause
