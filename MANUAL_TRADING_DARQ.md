# MANUAL MAESTRO DE ESTRATEGIAS Y REGLAS DE TRADING
**Sistema D+ARQ - Motor Híbrido 5 Capas (Portfolio Margin)**

---

## 🌐 CONFIGURACIÓN GLOBAL Y COLATERAL
- **Capital Base (Global NAV):** $1.000.000 USD
- **Arquitectura de Cuenta:** Portfolio Margin (Overlay Institucional).
- **Colateral Base (El millón inmovilizado genera interés):**
  - 40% SGOV / Bonos Tesoro 0-3M (Yield ~5.1%)
  - 20% IGSB / Corp AAA (Yield ~5.8%)
  - 20% SPY / S&P 500
  - 15% QQQ / Nasdaq 100
  - 5% GLD / Oro
- **Regla de Reinversión (Compound Engine):** Todo excedente mayor a $500 USD de ganancias realizadas se reinvierte proporcionalmente en la cartera base para generar Interés Compuesto.
- **Horario Operativo:** Lunes a Viernes, de 09:30 AM a 16:00 PM EST.

---

## ⚙️ CAPA 1: LA RUEDA (WHEEL STRATEGY)
*Recolección sistemática de primas IV sobre ETF subyacente.*
- **Presupuesto Asignado:** El 100% del NAV (Overlay sobre colateral).
- **Activos Operados:** `SPY`, `QQQ`.
- **Reglas de Entrada (Short Put):** 
  - **Delta Objetivo:** 0.25 (Alta probabilidad, 75%+ OTM).
  - **Vencimiento (DTE):** 30 a 45 días (Punto dulce de decaimiento Theta).
- **Gestión de Asignación:** Si la Put expira ITM, se asumen las acciones.
- **Regla de Salida (Covered Call):** Si hay acciones asignadas, se venden Calls contra esas acciones (Delta 0.20-0.25) para recuperar liquidez y forzar salida neta positiva.
- **Protocolo Andrés (Cut-off):** Colateral intocable. Ante asignación forzosa de equity, se venden las acciones de inmediato a las 09:30 EST y se emite un nuevo PUT a 6-8 semanas para recuperar crédito.

---

## ⚙️ CAPA 2: ALPHA TRADE
*Posicionamiento macro a largo plazo sin inmovilizar capital en acciones.*
- **Presupuesto Asignado:** $200.000 USD (Consumo de Margen).
- **Estrategia:** Sintético Alcista a Costo Cero (Zero-Cost LEAPS).
- **Reglas de Entrada:** 
  - Compra de `CALL` (Long) profundo ITM o ATM a 6-12 meses.
  - Venta de `PUT` (Short) OTM para financiar exactamente el 100% de la prima del Call.
- **Gestión de Riesgo:** El riesgo está en el Short Put. El sistema monitorea la paridad para asegurar que el débito inicial sea cercano a $0.00.

---

## ⚙️ CAPA 3: RSI OPORTUNISTA
*Venta de volatilidad extrema durante caídas en picada.*
- **Presupuesto Asignado:** $150.000 USD (Consumo de Margen).
- **Activos Operados:** `SPY`, `QQQ`, `IWM`.
- **Reglas de Entrada (Escáner):**
  - El bot escanea el RSI (Relative Strength Index).
  - Solo entra si el **RSI es MENOR a 30** (Condición de sobreventa severa/pánico).
  - Vende un `PUT` agresivo a 1 día de expiración (1 DTE).
- **Reglas de Salida (Take Profit & Time Stop):**
  - **TP Automático:** Se cierra el trade al alcanzar el 50% de la prima cobrada (V-Crush).
  - **Time Stop:** Cierre obligatorio a las 15:55 PM EST el día de la expiración. Nunca se cruza la noche con riesgo de asignación.

---

## ⚙️ CAPA 4: DAYTRADING INTRADÍA
*Scalping puro y extracción diaria de flujo de caja.*
- **Presupuesto Asignado:** $150.000 USD (Consumo de Margen).
- **Estrategia:** Venta de Puts 0-DTE o 1-DTE buscando decaimiento rápido.
- **Gestión de Riesgo (Protocolo Táctico 15:55):**
  - **PROHIBIDO** cruzar la liquidación nocturna en un contrato ITM intradía.
  - Si a las 15:55 EST el contrato está ITM (en pérdida), el algoritmo ejecuta obligatoriamente un **Roll Defensivo**: recompra el contrato perdedor y vende uno nuevo a 30-45 días con un "Strike" más bajo (Roll Out & Down), garantizando un **Crédito Neto (Net Credit)** para no perder dinero en efectivo.

---

## ⚙️ CAPA 5: BULL MARKET (PMCC)
*Poor Man's Covered Call.*
- **Presupuesto Asignado:** $150.000 USD.
- **Estrategia:** Diagonal Spread Alcista (PMCC).
- **Reglas de Entrada:**
  - Pata Larga (Long LEAPS): Compra un Call profundo ITM (Delta > 0.80) con vencimiento lejano (> 120 días). Actúa como reemplazo de acciones reales.
  - Pata Corta (Short Call): Vende un Call OTM (Delta < 0.30) a corto plazo (7-14 días).
- **Gestión:** La prima cobrada de las opciones cortas reduce constantemente el costo base de la posición larga original.
