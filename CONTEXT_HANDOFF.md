# 🧠 MASTER CONTEXT & SYSTEM HANDOFF (SISTEMA DE OPCIONES INSTITUCIONAL)
*Fecha de actualización:* 21 de Septiembre de 2026
*Ubicación:* Carpeta compartida de Dropbox / Repositorio Git (Sistema de opciones)
*Rama activa de trabajo:* dev

---

## 🛑 1. REGLA OPERATIVA FUNDAMENTAL (LEER ANTES DE TOCAR NADA)

> [!CAUTION]
> **PROHIBIDO PUSHEAR A GITHUB O RENDER SIN AUTORIZACIÓN EXPRESA DEL USUARIO.**
> * No sobrecargar los minutos de build de Render.
> * Todo el trabajo de desarrollo, ajustes matemáticos y pruebas se realiza **100% EN FORMA LOCAL** en la rama dev.
> * Para probar el dashboard y los bots localmente, ejecutar en PowerShell:
>   `powershell
>   .\dev_local.ps1
>   `
>   Acceso al dashboard local: **http://localhost:10000**.
> * **Solo se hace UN ÚNICO PUSH consolidado** vía .\deploy.ps1 cuando el usuario termine toda la sesión de trabajo y dé la orden explícita.

---

## 📌 2. VISIÓN GENERAL DEL SISTEMA

El sistema es un **Fondo de Inversión Híbrido Cuantitativo de Opciones en Wall Street** con una Cuenta Maestra base de **,000.00 USD**:
1. **Colateral Institucional (100% NAV en 5 Bloques):**
   * **40% Bonos del Tesoro / Liquidez Ultra-Corta:** SGOV, BOXX, TBIL, CSHI, VTIP, IBTG (5.1% APY). Requisito de margen: 2.0%.
   * **20% Bonos Corporativos AAA / Acciones Preferidas:** IGSB, VCSH, PFF (5.8% APY). Requisito de margen: 7.5%.
   * **20% Core Equity S&P 500:** SPY / VOO (1.5% APY + Covered Calls). Requisito de margen: 15.0%.
   * **15% Tech Growth Nasdaq 100:** QQQ (0.8% APY + LEAPS Overlay). Requisito de margen: 15.0%.
   * **5% Oro Físico:** GLD (4.5% APY con Covered Calls). Requisito de margen: 15.0%.
   * **Poder de Compra Desbloqueado (Buying Power):** **~,400+ USD (90.4%)**.
   * **Rendimiento Pasivo Base del Colateral:** **+,350.00 USD / año** (~.50 USD / mes).

2. **Garantías Cruzadas (Portfolio Margin):**
   * Las 4 capas de opciones operan aprovechando el poder de compra liberado por el colateral sin desarmar las tenencias.

3. **Motor de Reinversión Automática (Split 50/30/20):**
   * Cada vez que se acumulan **+ USD** de primas cobradas:
     * **50%** se destina a acumular más Bonos del Tesoro (SGOV).
     * **30%** se transfiere a comprar más acciones de SPY en la Rueda para generar interés compuesto.
     * **20%** se acumula para recomprar (desacoplar) la pata Short Put de Alpha Trade.

---

## 🚀 3. LAS 4 CAPAS ESTRATÉGICAS INTEGRADAS

### 🎡 Capa 1: The Wheel & Compounding (wheel_compounding_engine.py)
* **Rol:** Overlay de renta y capitalización compuesta al 100% sobre colateral.
* **Mecánica:** Venta de Cash-Secured Puts a 30 DTE (Delta ~0.25, 3% OTM). Si es asignado, venta de Covered Calls.
* **Compounding:** 100% de las primas cobradas compran automáticamente acciones fraccionadas de SPY.
* **Defensa:** Matriz de auto-roleo defensivo (*Roll Down & Out*) ante caídas >5%, >15% o Cisnes Negros (>20%).
* **Estado Actual:**
  * **1 posición activa:** SPY Cash-Secured Put K.2 (30 DTE, vence 2026-10-21). Prima: +.00 USD.
  * **Tenencia en cartera:** **1.0606 acciones de SPY** acumuladas.
  * **PnL:** **+.99 USD** (+ apreciación de acciones).

### 🚀 Capa 2: Alpha Trade Macro LEAPS 2 Años (lpha_trade_bot.py)
* **Rol:** Multiplicador alcista a largo plazo sin costo neto (Zero-Cost).
* **Mecánica:** Sintéticos a 2 años (730 DTE) combinando 2 Short Puts (strike 0.85) + 2 Long Calls (strike 1.05).
* **Gatillo de Entrada:** Confirmación macro por cruce alcista de Media Móvil **DMA200** y **RSI Semanal > 45**.
* **Mecanismo de Desacople (Decouple / Free Runner):** Cuando hay fondos de reinversión o cuando el valor de la mitad de los calls supera el costo de recompra del put, se recompra el Short Put por  USD.
* **Estado Actual:**
  * **1 posición desacoplada 100% LIBRE DE RIESGO:** Long Call QQQ K (2 contratos, 104 DTE restantes).
  * **Riesgo Short Put:** **.00 USD**.
  * **PnL Flotante no realizado:** **+,434.00 USD** (Subyacente actual .34 > Strike ).

### ⚡ Capa 3: RSI Oportunista 1-DTE (
si_opportunistic_bot.py)
* **Rol:** Explotación de pánico extremo y picos de Volatilidad Implícita (IV Spikes).
* **Mecánica:** Venta de Naked Puts / Bull Put Spreads a 1-DTE en SPY, QQQ o DIA cuando el RSI intradía cae por debajo de 25-30 y el precio es inferior al cierre anterior.
* **Salida:** Take profit al 90-95%, rebote de RSI > 55, o expiración OTM.
* **Estado Actual:**
  * **Modo:** IDLE_MONITORING (Escaneando mercado).
  * **Historial cerrado:** 1 trade en DIA Put K.7 (expiró OTM sin valor).
  * **PnL Realizado:** **+.00 USD** (100% prima retenida).

### 🎯 Capa 4: Day Trading ITM 1-DTE (daytrade_options_bot.py)
* **Rol:** Scalp intradía por rebote y ruptura.
* **Mecánica:** Venta de Puts ITM (Strike +1%) a 1-DTE en SPY/QQQ ante caídas >= 1% o cruce alcista de RSI 30.
* **Salida:** Take Profit estricto al **50% de la prima cobrada** o expiración.
* **Estado Actual:**
  * **1 trade cerrado:** SPY Put K.7 (cerrado por Take Profit 50%).
  * **PnL Realizado:** **+.00 USD** (+4.93% ROI sobre capital en riesgo).
  * **Modo:** SCANNING_INTRADAY (Escaneando nuevas señales).

---

## 📊 4. MÉTRICAS CONSOLIDADAS AUDITADAS (EN VIVO)

* **Capital Inicial Maestro:** ,000.00 USD
* **NAV Consolidado:** **,968.99 USD** (**+10.97% ROI**)
* **PnL Neto Total:** **+,968.99 USD**
  * Capa 1 (Rueda SPY): +.99 USD (+ 1.0606 acciones SPY)
  * Capa 2 (Alpha LEAPS QQQ): +,434.00 USD (Call 100% Risk-Free)
  * Capa 3 (RSI Oportunista DIA): +.00 USD
  * Capa 4 (Day Trading SPY): +.00 USD
* **Utilización de Margen:** **18.5%** (**ÓPTIMO**, sin sobreapalancamiento)
* **Margen Libre Disponible:** **,443.00 USD**
* **Dashboard Live en Producción:** **https://opciones-wall-street-xmz0.onrender.com/**
* **Repositorio Git:** sandonato798-afk/Opciones-wall-street.git (Rama dev para trabajar, rama main para producción).

---

## 🔑 5. GUÍA PARA EL AGENTE DE IA EN LA OTRA PC

Si estás asistiendo al usuario desde la otra computadora:
1. **Verificar rama de trabajo:** Asegurarse de estar en git checkout dev.
2. **NO EJECUTAR git push NI .\deploy.ps1:** Trabajar de manera 100% local. El usuario pidió explícitamente no sobrecargar Render con builds continuos.
3. **Probar localmente:** Utilizar .\dev_local.ps1 y verificar en http://localhost:10000.
4. **Sincronización:** Los archivos de código y estado (.json) se sincronizan automáticamente entre las PCs vía Dropbox.
5. **Persistencia en la Nube:** Cada bot utiliza cloud_persistence.py con fallbacks seguros que protegen el historial local contra sobreescrituras accidentales.
6. **Despliegue final:** Solo cuando el usuario diga que todo está listo y dé la orden explícita de push, se corre .\deploy.ps1.