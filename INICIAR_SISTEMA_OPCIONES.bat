@echo off
title Sistema de Opciones D+ARQ - Motor Algoritmico 5 Capas
cls
echo ====================================================================
echo      INICIANDO SISTEMA DE OPCIONES D+ARQ - 5 CAPAS IBKR PAPER
echo ====================================================================
echo.
echo  Conectando con Interactive Brokers Paper Trading (Puerto 4002)...
echo.

cd /d "%~dp0"
python app.py

pause
