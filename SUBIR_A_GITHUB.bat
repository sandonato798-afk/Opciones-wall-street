@echo off
title Subir Sistema de Opciones a GitHub (Deploy a Render)
cls
echo ====================================================================
echo      SUBIENDO SISTEMA DE OPCIONES A GITHUB Y DEPLOY A RENDER
echo ====================================================================
echo.
echo  Repositorio: https://github.com/sandonato798-afk/Opciones-wall-street.git
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File .\deploy.ps1

echo.
pause

