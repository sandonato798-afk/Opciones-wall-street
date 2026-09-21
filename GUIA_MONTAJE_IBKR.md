# 📘 GUÍA PASO A PASO: MONTAJE Y CONEXIÓN DEL BOT A INTERACTIVE BROKERS (IBKR)

Esta guía explica en detalle cómo configurar y conectar el bot a una cuenta de **Interactive Brokers (IBKR)** en modo **Paper Trading** (simulación oficial con cotizaciones y libro de órdenes real de Wall Street), para probar ejecuciones reales con ** riesgo**.

---

## 📋 ÍNDICE DE PASOS
1. [Requisitos Previos de la Cuenta](#1-requisitos-previos-de-la-cuenta)
2. [Instalación y Configuración de TWS / IB Gateway](#2-instalación-y-configuración-de-tws--ib-gateway)
3. [Instalación de Dependencias de Python](#3-instalación-de-dependencias-de-python)
4. [Estructura del Conector ibkr_adapter.py](#4-estructura-del-conector-ibkr_adapterpy)
5. [Prueba de Conexión y Handshake (Paso de Validación)](#5-prueba-de-conexión-y-handshake)
6. [Flujo Operativo Diario](#6-flujo-operativo-diario)
7. [Protocolos de Seguridad y Fail-Safes](#7-protocolos-de-seguridad-y-fail-safes)

---

## 1. REQUISITOS PREVIOS DE LA CUENTA

1. **Cuenta en Interactive Brokers:**
   * Tener usuario activo en [interactivebrokers.com](https://www.interactivebrokers.com).
2. **Cuenta de Paper Trading Habilitada:**
   * En el portal web de IBKR, ir a: *Settings -> Account Settings -> Paper Trading Account*.
   * IBKR asigna un usuario específico de Paper Trading (ejemplo: du1234567) con su propia contraseña.
   * La cuenta Paper tiene típicamente un saldo ficticio de **,000,000 USD** para pruebas.
3. **Permisos de Trading de Opciones:**
   * Verificar en *Settings -> Trading Permissions -> Options*:
   * Debe tener habilitado **Nivel 3 o Nivel 4 (Trading de Opciones Completo / Margin Account)** para permitir venta de Cash-Secured Puts, Spreads y LEAPS.

---

## 2. INSTALACIÓN Y CONFIGURACIÓN DE TWS / IB GATEWAY

Tienes dos opciones de software oficial de IBKR:
* **Opción A (Recomendada para PC):** **Trader Workstation (TWS)** — Tiene interfaz visual para ver las órdenes y gráficos.
* **Opción B (Para servidores / consumo mínimo de RAM):** **IB Gateway** — Solo abre la pasarela de conexión en segundo plano sin gráficos pesados.

### Pasos de Configuración en TWS:
1. Descargar e instalar **TWS (Offline / Standalone)** desde la web de IBKR.
2. Abrir TWS y seleccionar la pestaña **Paper Trading** (color rojo/granate, NO la pestaña Live azul).
3. Ingresar con las credenciales de Paper Trading.
4. En el menú superior de TWS, ir a:
   * **Edit** -> **Global Configuration** (o *File -> Global Configuration*).
5. En el panel lateral izquierdo, seleccionar: **API** -> **Settings**.
6. Configurar exactamente estas casillas:
   * ✅ **Enable ActiveX and Socket Clients** (Habilitado).
   * **Socket Port:** Colocar **4002** (o 7497 para TWS Paper). *Anotar este número*.
   * ❌ **Read-Only API:** **DESMARCAR** esta casilla (debe quedar desmarcada para que el bot pueda enviar órdenes de compra y venta).
   * ✅ **Allow connections from localhost only** (Habilitado por seguridad para aceptar solo 127.0.0.1).
   * ✅ **Create API message log file** (Habilitado para registrar auditorías).
7. Clic en **Apply** y luego en **OK**.

---

## 3. INSTALACIÓN DE DEPENDENCIAS DE PYTHON

En la terminal (PowerShell o CMD) de la máquina donde correrá el bot:

`powershell
# 1. Asegurarse de estar en el entorno virtual o Python global
pip install ib_insync yfinance
`

* ib_insync: Es la librería Python estándar de la industria financiera para interactuar de forma asíncrona con TWS / IB Gateway sin bloqueos de red.

---

## 4. ESTRUCTURA DEL CONECTOR ibkr_adapter.py

El archivo ibkr_adapter.py en la raíz del proyecto es el puente de comunicación entre las 4 capas del bot y el broker:

* **Host:** 127.0.0.1 (localhost).
* **Puerto:** 4002 (IB Gateway Paper) o 7497 (TWS Paper).
* **Client ID:** 1 (identificador del bot ante TWS).
* **Trading Mode:** is_paper = True.

### Parámetros de Riesgo Preconfigurados:
* **Pérdida máxima diaria permitida:** 2.0% del NAV (si se alcanza, el bot bloquea nuevas entradas automáticamente).
* **Máximo de posiciones simultáneas:** 4 operaciones.
* **Órdenes Bracket:** Cada orden emitida envía en el mismo paquete:
  * Orden de entrada límite (LMT).
  * **Take Profit:** Orden límite al +50% (Day Trading) o +70% (Spreads).
  * **Stop Loss:** Orden Stop (STP) al -18% (que vive en los servidores de IBKR).

---

## 5. PRUEBA DE CONEXIÓN Y HANDSHAKE

Antes de activar el trading automático de las 4 capas, hacer el test de conectividad:

1. Asegurarse de que **TWS esté abierto y con la sesión iniciada en Paper Trading**.
2. Abrir PowerShell en la carpeta del proyecto y correr:

`powershell
python ibkr_adapter.py
`

### Salida esperada de éxito:
`	ext
[INFO] Conectando a IBKR (PAPER) en 127.0.0.1:4002...
[INFO] ✅ Conexión establecida exitosamente con Interactive Brokers.
Resumen de Cuenta IBKR:
 - NetLiquidation: ,000,000.00 USD
 - SettledCash: ,000,000.00 USD
 - BuyingPower: ,000,000.00 USD
[INFO] 🚀 [IBKR Order Sent] BUY 2x SPY Strike 560.0 (2026-09-18) | Limit: .50 | TP: .72 | SL: .87
`

Si este comando completa sin errores y en TWS ves aparecer la orden de prueba en la pestaña **Orders / Trades**, ¡la conexión de hardware y software está 100% lista!

---

## 6. FLUJO OPERATIVO DIARIO

`mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant TWS as IBKR TWS / Gateway
    participant Bot as Bot 4 Capas (Local)
    participant Dash as Dashboard Local (dev_local.ps1)

    Usuario->>TWS: Inicia sesión Paper Trading (10:15 hs)
    Usuario->>Bot: Ejecuta .\dev_local.ps1
    Bot->>TWS: Handshake API (Socket 4002)
    Note over Bot,TWS: Mercado abre 10:30 hs (Wall Street 9:30 AM)
    Bot->>TWS: Escaneo cada 60s & Envío de Órdenes Bracket
    Bot->>Dash: Actualiza NAV, Colateral y Métricas en vivo
    Note over Bot,TWS: Mercado cierra 17:00 hs (Wall Street 4:00 PM)
    Bot->>Bot: Liquidación de vencimientos del día
`

1. **10:15 hs (Argentina) / 9:15 AM (Nueva York):**
   * Abrir TWS en Paper Trading.
2. **10:20 hs:**
   * Abrir PowerShell en la carpeta del sistema y ejecutar:
     `powershell
     .\dev_local.ps1
     `
   * Abrir en el navegador http://localhost:10000 para monitorear el panel en vivo.
3. **10:30 hs a 17:00 hs (Horario de Mercado):**
   * El bot escanea las oportunidades de la Rueda (SPY), Alpha LEAPS (QQQ), RSI Pánico (DIA) y Day Trading ITM.
   * Cualquier orden que cumpla los gatillos se transmite automáticamente a TWS.
4. **17:00 hs:**
   * Cierre de mercado. El bot registra el cierre de ciclo y calcula el PnL final del día.

---

## 7. PROTOCOLOS DE SEGURIDAD Y FAIL-SAFES

1. **Desconexión de Internet en tu PC:**
   * Debido a que usamos **Bracket Orders**, el Stop Loss y el Take Profit se transmiten al servidor de Interactive Brokers al momento de entrar. Si se te corta el WiFi o la luz, **el Stop Loss se ejecuta igualmente en Wall Street** desde los servidores de IBKR.
2. **Reconexión Automática:**
   * El adaptador incluye un bucle de reintento (	ry/except con backoff de 5s) si TWS se reinicia.
3. **Regla de No-Sobreapalancamiento:**
   * El bot valida antes de cada orden que la utilización de margen no exceda el **65%**. Si el margen supera ese umbral, congela automáticamente nuevas aperturas para preservar el colateral de Bonos del Tesoro (SGOV).

---
*Documento preparado y sincronizado automáticamente vía Dropbox para uso en todas las estaciones de trabajo.*