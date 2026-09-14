@echo off
title Sistema de Opciones sobre ETFs (Wall Street) - D+ARQ
cls
echo ====================================================================
echo      INICIANDO SISTEMA DE OPCIONES SOBRE ETFs DE WALL STREET
echo ====================================================================
echo.
echo  Conectando con Yahoo Finance y cargando motor Black-Scholes...
echo.

cd /d "%~dp0"
python app.py

pause
