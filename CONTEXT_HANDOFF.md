# 🧠 MASTER CONTEXT & SYSTEM HANDOFF (SISTEMA DE OPCIONES INSTITUCIONAL)
*Fecha de actualización:* 22 de Septiembre de 2026  
*Ubicación:* Carpeta compartida de Dropbox / Repositorio Git (`Sistema de opciones`)  
*Rama activa de trabajo:* `dev`  

---

## 🛑 1. REGLA OPERATIVA FUNDAMENTAL (LEER ANTES DE TOCAR NADA)

> [!CAUTION]
> **PROHIBIDO PUSHEAR A GITHUB O RENDER SIN AUTORIZACIÓN EXPRESA DEL USUARIO.**
> * No sobrecargar los minutos de build de Render.
> * Todo el trabajo de desarrollo, ajustes matemáticos y pruebas se realiza **100% EN FORMA LOCAL** en la rama `dev`.
> * Para probar el dashboard y los bots localmente, ejecutar en PowerShell:
>   ```powershell
>   .\dev_local.ps1
>   ```
>   O directamente:
>   ```powershell
>   $env:PORT='10000'; $env:RENDER_EXTERNAL_URL='http://localhost:10000'; python app.py
>   ```
>   Acceso al dashboard local: **http://localhost:10000**.
> * **Solo se hace UN ÚNICO PUSH consolidado** vía `.\deploy.ps1` cuando el usuario termine toda la sesión de trabajo y dé la orden explícita.

---

## 📌 2. ARQUITECTURA DE FONDOS: SINGLE MARGIN POOL (100% UNIFICADO)

El sistema opera como un **Fondo de Inversión Híbrido Cuantitativo de Opciones en Wall Street** bajo Portfolio Margin institucional:

1. **Garantía / Colateral Base Intocable ($100,000.00 USD NAV Base):**
   * **40% Bonos del Tesoro / Liquidez Ultra-Corta:** SGOV, BOXX, TBIL, CSHI, VTIP, IBTG (~5.1% APY). Requisito de margen: 2.0%.
   * **20% Bonos Corporativos AAA / Acciones Preferidas:** IGSB, VCSH, PFF (~5.8% APY). Requisito de margen: 7.5%.
   * **20% Core Equity S&P 500:** SPY / VOO (~1.5% APY). Requisito de margen: 15.0%.
   * **15% Tech Growth Nasdaq 100:** QQQ (~0.8% APY). Requisito de margen: 15.0%.
   * **5% Oro Físico:** GLD (~0.0% APY). Requisito de margen: 15.0%.
   * **Poder de Compra Desbloqueado (Buying Power):** **~$85,000+ USD (~85.4%)**.
   * **Renta Pasiva Base Garantizada:** **+$4,350.00 USD / año** (~$362.50 USD / mes).

2. **Pool Unificado de Margen al 100% (Single Margin Pool):**
   * **Cero Silos Estáticos:** Se eliminaron los presupuestos artificiales (`allocated_capital = $20,000`, etc.).
   * Las 5 capas de opciones compiten en tiempo real consumiendo del **Margen Libre Disponible Global (~$81,000 USD)** bajo la regla *First-Come, First-Served*.

3. **Motor de Reinversión Proporcional (40 / 20 / 20 / 15 / 5) con Regla de Liquidez:**
   * Al superar **+$500 USD de ganancia neta en operaciones 100% CERRADAS**:
     * **40%** $\rightarrow$ Bonos del Tesoro (SGOV)
     * **20%** $\rightarrow$ Bonos Corporativos AAA (IGSB)
     * **20%** $\rightarrow$ S&P 500 (SPY)
     * **15%** $\rightarrow$ Nasdaq 100 (QQQ)
     * **5%** $\rightarrow$ Oro Físico (GLD)
   * **Regla de Liquidez de Andrés Weisz**: Si una posición es rolleada o permanece abierta, sus primas quedan bloqueadas en el búfer de trading para fondear recompras. **Nunca se retiran a la garantía hasta que el trade esté totalmente cerrado**.

---

## 🚀 3. LAS 5 CAPAS ESTRATÉGICAS Y SUS PROTOCOLOS INSTITUCIONALES

### 🎡 Capa 1: La Rueda (Yield Overlay sobre Margen) — `wheel_compounding_engine.py`
* **Colateral Intocable**: Se eliminó la acumulación fraccionaria que gatillaba Covered Calls sobre la garantía base. Opera puramente como un **Overlay Sistemático de Cash/Margin-Secured Puts** (SPY, QQQ, IWM) a 30-45 DTE (Delta 0.20-0.25).
* **Protocolo de Asignación Física de Andrés Weisz**:
  * Si la cuenta es asignada con 100 acciones:
    1. A la apertura siguiente (**09:30 EST**) se venden las 100 acciones a mercado de forma inmediata.
    2. Simultáneamente se vende 1 Put por cada 100 acciones a **6-8 semanas (42-56 DTE)** con el mismo strike.
    3. Si el subyacente cayó $>15\%$, se reduce el strike entre 5% y 10% cobrando crédito neto.

### 🚀 Capa 2: Alpha Trade Macro LEAPS — `alpha_trade_bot.py`
* **Mecánica**: Sintéticos a 2-3 años (730 a 850 DTE) a **Costo Cero Neto ($0.00)** combinando 1-2 Short Puts (Strike -15% OTM) + 2 Long Calls (Strike +5% OTM).
* **Desacople Autónomo (*Self-Funded Free Runner*)**: Monitoreado cada 60s en segundo plano con Black-Scholes. En cuanto la mitad de los Long Calls gana suficiente valor para recomprar y extinguir el Short Put, **el bot lo desacopla solo**, dejando Long Calls vivos sin riesgo y con subida ilimitada.

### ⚡ Capa 3: RSI Oportunista 1-DTE — `rsi_opportunistic_bot.py`
* **Rol**: Explotación de pánico extremo y picos de Volatilidad Implícita.
* **Mecánica**: Venta de Puts a 1DTE cuando RSI intradía cae por debajo de 30.
* **Protocolo**: TP al 50%. En caso de asignación, sigue idéntico protocolo de salida a las 09:30 EST + venta de Put a 6-8 semanas.

### 🎯 Capa 4: Day Trading ITM 1-DTE — `daytrade_options_bot.py`
* **Rol**: Scalp intradía de alta probabilidad (SPY / QQQ).
* **Protocolo de Salida y Roll Defensivo de Andrés Weisz**:
  * Take Profit automático al 50%.
  * **A las 15:55 EST (fin de sesión de D+1)**:
    * Si la recompra deja ganancia neta tras comisiones $\rightarrow$ **Cierra inmediatamente (`CLOSED_EOD_PROFIT`)**.
    * Si la recompra resultaría en pérdida $\rightarrow$ **Ejecuta ROLL DEFENSIVO** a vencimiento posterior cobrando crédito neto sin asumir pérdidas ni tocar el colateral base.

### 📈 Capa 5: Bull Market PMCC (Diagonal Spread Alcista) — `bull_market_bot.py`
* **Rol**: Sustitución de acciones por Poor Man's Covered Call.
* **Mecánica**: Long Call ITM LEAP (Delta ~0.80) a más de 180 DTE + Short Call semanal OTM (Delta ~0.20).
* **Manejo**: Extracción sistemática de renta semanal mediante rolleos continuos de la pata corta.

---

## 🏗️ 4. MODULARIZACIÓN COMPLETA DEL SISTEMA

El proyecto está 100% desacoplado y estructurado:

```
Sistema de opciones/
├── app.py                         <-- Servidor HTTP (<200 líneas) + bucle de trading de 60s
├── routes/                        <-- Enrutador modular desacoplado
│   ├── __init__.py                <-- Despachador central (dispatch_get, dispatch_post)
│   ├── master_routes.py           <-- Endpoints Portafolio Maestro, Colateral y Reinversión
│   ├── wheel_routes.py            <-- Endpoints Capa 1: Rueda
│   ├── alpha_routes.py            <-- Endpoints Capa 2: Alpha LEAPS
│   ├── rsi_routes.py              <-- Endpoints Capa 3: RSI Oportunista
│   ├── daytrade_routes.py         <-- Endpoints Capa 4: Daytrading
│   └── bullmarket_routes.py       <-- Endpoints Capa 5: Bull Market
├── js/
│   ├── formatters.js              <-- Funciones puras de formato monetario y estilos
│   ├── components/
│   │   ├── table_15_metrics.js    <-- Tabla auditada de 15 métricas + Tarjetas de Trade Activo con TP 50%
│   │   └── matrix_table.js        <-- Estructura de matrices multileg (Short/Long/Neto)
│   └── tabs/
│       ├── tab_master.js          <-- Lógica de Home, Colateral y Semáforos de Salud
│       ├── tab_wheel.js           <-- Lógica y eventos de Rueda
│       ├── tab_alpha.js           <-- Lógica y eventos de Alpha
│       ├── tab_rsi.js             <-- Lógica y eventos de RSI
│       ├── tab_daytrade.js        <-- Lógica y eventos de Daytrading
│       └── tab_bullmarket.js      <-- Lógica y eventos de Bull Market
├── app.js                         <-- Orquestador frontend de 44 líneas (navegación y polling concurrente)
└── index.html                     <-- Dashboard moderno con las 6 solapas y sin presupuestos estáticos
```

---

## 📊 5. MÉTRICAS CONSOLIDADAS Y AUDITORÍA EN VIVO

* **Capital Maestro Inicial:** $100,000.00 USD
* **NAV Consolidado:** **~$112,000+ USD**
* **Margen Libre Disponible:** **~$81,000.00 USD** (Estado: `OPTIMAL`)
* **Utilización de Margen:** **~27%**
* **Dashboard Local:** `http://localhost:10000`
* **Dashboard Live en Producción:** `https://opciones-wall-street-xmz0.onrender.com/`
* **Repositorio Git:** `sandonato798-afk/Opciones-wall-street.git`
  * Rama `dev`: Para trabajar en local.
  * Rama `main`: Solo para producción al desplegar.

---

## 🔑 6. GUÍA EXACTA PARA CONTINUAR EN OTRA PC

Si abres el proyecto en otra computadora:

1. **Sincronización de Archivos**:
   * Todos los archivos modificados y commits locales se sincronizan inmediatamente vía **Dropbox**.
2. **Verificar Git**:
   * Abrir PowerShell en la carpeta `Sistema de opciones`:
     ```powershell
     git status
     git branch
     ```
   * Confirmar que estás en la rama `dev`.
3. **Iniciar el Servidor Local**:
   * Ejecutar:
     ```powershell
     powershell -ExecutionPolicy Bypass -File .\dev_local.ps1
     ```
     O alternativamente:
     ```powershell
     $env:PORT='10000'; $env:RENDER_EXTERNAL_URL='http://localhost:10000'; python app.py
     ```
4. **Abrir en el Navegador**:
   * Ingresar a: `http://localhost:10000`
   * Notarás que el Home ya no muestra presupuestos fijos de $20k/$15k, sino **MARGEN EN USO (POOL 100%)**, tarjetas interactivas de trade activo con barra de Take Profit al 50% y semáforos de riesgo.
5. **Regla de Oro**:
   * **NUNCA hacer `git push`** ni correr `.\deploy.ps1` hasta que el usuario dé la orden explícita de subir a producción.