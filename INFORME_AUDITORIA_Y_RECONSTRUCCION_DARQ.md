# INFORME DE AUDITORÍA GLOBAL Y PLAN DE RECONSTRUCCIÓN
## Sistema de Trading de Opciones D+ARQ

> **Fecha de Auditoría:** Octubre 2026  
> **Estado:** AUDITORÍA COMPLETADA - EN FASE DE RECONSTRUCCIÓN INSTITUCIONAL  
> **Veredicto:** El sistema NO estaba listo para operar (ni en real ni en paper). Se ordenó la contención inmediata y la reconstrucción desde el núcleo.

---

### 1. DIAGNÓSTICO Y HALLAZGOS CRÍTICOS (LOS 3 AUDITORES)

#### A. Motor de Ejecución (Afectaba a todas las capas)
- **Fills Inventados y Falsos Positivos:** El sistema registraba el trade en el JSON incluso si la orden fallaba o no se enviaba. En modo simulación o sin conexión, `execute_option_order_sync` devolvía `FILLED` a $1.00 fijo (registrado en `wheel_compounding.log`).
- **Salidas Nunca Enviadas al Broker:** Los mecanismos de Take-Profit, Stop-Loss, Roll defensivo, Desacople de Alpha y cierre por vencimiento solo editaban el archivo JSON local. Si una orden de apertura se ejecutaba en IBKR, la posición corta quedaba **abierta en el broker para siempre**.
- **Contratos Inválidos e Inexistentes:** Los strikes se redondeaban matemáticamente a 0.1 y los vencimientos se calculaban con fechas calendario simples, sin consultar la cadena real de IBKR (`reqSecDefOptParams`). Nunca se calificaban los contratos (`qualifyContracts`).
- **Órdenes a Mercado (MKT):** En opciones de baja liquidez y LEAPS de 25 lotes se enviaban órdenes `MKT`, con riesgo de *slippage* extremo.
- **Cotizaciones y Precios Ficticios:** Se usaban datos con 15-20 min de retraso (`reqMarketDataType(3)`). Cuando IBKR devolvía `$0.00` por falta de suscripción u oferta, el bot usaba `$0.00` o el cierre anterior, provocando pérdidas ficticias de hasta -$74.000 USD en los registros.
- **RSI Falso:** Se calculaba como `50 + %cambio * 15`, en lugar de usar velas de 14 períodos de Wilder sobre datos históricos reales.
- **Primas Fijas Black-Scholes:** Las primas se estimaban con volatilidad implícita fija (0.16-0.18) en lugar de consultar la oferta real (*Bid/Ask*) de la bolsa.
- **Límites de Riesgo Inactivos:** `check_risk_limits()` nunca se llamaba. No había Stop-Loss real en ninguna capa y Daytrading realizaba rolls infinitos.
- **Sin Reconciliación:** Ninguna capa comparaba su estado local con `ib.positions()` ni detectaba asignaciones verdaderas del broker.

#### B. Hilos y Conexión Socket
- **Escritura Concurrente al Socket:** Los endpoints HTTP `POST` (`run-cycle`, `buy-collateral`, `daytrade/scan`, `bullmarket/open`) llamaban a `ib_insync` desde hilos secundarios del servidor web, provocando errores silenciosos de `asyncio` y corrupción de llamadas en el socket.
- **Heartbeat Falso:** El watchdog verificaba `serverVersion()`, un valor estático guardado en caché que no probaba si el socket real estaba vivo. No se manejaban eventos de reconexión `1100/1101/1102` ni errores de ClientID duplicado `326`.
- **Watchdog Frágil:** Diseñado solo para Windows (`StartGateway.bat`), pudiendo abrir múltiples instancias concurrentes de IB Gateway.

#### C. Estado, Persistencia y Datos Fantasma
- **$14.3M Reinvertidos Fantasma:** Los $14.3M reinvertidos registrados en el JSON eran producto del bucle infinito de la Capa 2 (Alpha), donde la señal de entrada daba `True` constantemente y "desacoplaba" sin enviar órdenes cada 1.5 minutos.
- **Reinversión Simulada:** El motor de reinversión solo sumaba números en el JSON sin ejecutar compras de activos.
- **Pisado de Estado en la Nube:** La sincronización con GitHub cargaba copias viejas sobre estados locales actualizados. Los endpoints `GET` del dashboard leían disco sin locks.

#### D. Seguridad y Credenciales
- **Credenciales en Texto Plano:** Usuario y clave de IBKR en `config.ini` dentro de Dropbox, token de GitHub en `.github_token` y `.git/config`.
- **API Expuesta:** Servidor escuchando en `0.0.0.0` con `Access-Control-Allow-Origin: *` sin autenticación, vulnerable a ataques CSRF.

#### E. Dashboard
- **Valores Inventados (Mocks):** Más de 40 valores fijos mostrados como "reales" en el frontend (NAV, PnL, unidades, precios).
- **Campos Descalzados:** Más de 25 campos entre backend y frontend con nombres diferentes, apareciendo vacíos o en 0.

#### F. Diagnóstico por Capa
1. **Capa 1 (La Rueda):** 1 CSP cada 30 días sin detectar asignación real. Rolls y asignación existían solo en JSON.
2. **Capa 2 (Alpha):** Señal siempre `True`, desacople fantasma, patas no atómicas (riesgo de 25 puts desnudas).
3. **Capa 3 (RSI):** RSI falso, salidas solo en JSON, vencimiento del viernes convertido en 0DTE por error de zona horaria.
4. **Capa 4 (Daytrading):** Puts ITM desnudas por ~4.7x el capital, sin stop, ventana de hora local en vez de EST.
5. **Capa 5 (PMCC):** Strikes no listados, rolls solo en JSON, pata larga abandonada sin gestión.

---

### 2. PLAN DE RECONSTRUCCIÓN INSTITUCIONAL (FASE 0 A FASE 5)

#### Fase 0 — Contención Inmediata (EJECUTADO)
- [x] Detención de `app.py`.
- [x] Kill-switch global implementado (`TRADING_ENABLED: false`).
- [x] Purgado y reseteo a 0 de todos los estados JSON contaminados (`alpha_trade_state.json`, `reinvestment_state.json`, `wheel_compounding_state.json`, `bull_market_state.json`, `rsi_opportunistic_state.json`).

#### Fase 1 — Núcleo de Ejecución Institucional (`core/`) (EJECUTADO)
- [x] `core/clock.py`: Hora ET nativa (`America/New_York`) + Feriados NYSE (2026-2030) + Cierres tempranos.
- [x] `core/contracts.py`: Calificación oficial de opciones (`reqSecDefOptParams` + `qualifyContracts`).
- [x] `core/orders.py`: Motor estricto de órdenes `LIMIT` (Mid ± 1 tick), monitoreo hasta `Filled`, prohibido `FILLED` simulado.
- [x] `core/ledger.py`: Libro mayor atómico (escritura `.tmp` -> `replace`) y reconciliación 1:1 contra `ib.positions()`.
- [x] `core/risk.py`: Guardián de margen, drawdown y kill-switch.
- [x] `core/broker.py`: Socket thread-safe con Heartbeat real (`reqCurrentTime`) e inspección de errores `1100/1101/326`.

#### Fase 2 — Configuración Modular Centralizada (EJECUTADO)
- [x] `config/strategies.yaml`: Único archivo centralizado de parámetros por capa y reglas globales.
- [x] Reconfiguración del Portafolio de Colateral (100% NAV): 60% Bonos del Tesoro EE.UU. directos escalonados (12/2027 a 12/2032, precio < 100, ~5% APY) + 20% VOO + 15% QQQ + 5% GLD.

#### Fase 3 — Reescritura de Capas sobre el Nuevo Núcleo (EN PROGRESO)
- Reescritura de cada estrategia sobre la interfaz común: `evaluate() -> risk.check() -> orders.place() -> ledger.record_fill()`.
- **Capa 1 (La Rueda):** Puts por delta real, detección de asignación y covered calls.
- **Capa 2 (Alpha):** Señal SMA-200 + RSI semanal, orden combo BAG atómica, desacople con compras reales.
- **Capa 3 (RSI Oportunista):** RSI-14 de Wilder real, stop-loss obligatorio, requiere datos en vivo (OPRA).
- **Capa 4 (Daytrading):** Rupturas ORB 15 min, órdenes limit, roll a 30 DTE.
- **Capa 5 (PMCC):** Combo diagonal con strikes listados, roll semanal real.

#### Fase 4 — API y Dashboard
- API escuchando solo en `127.0.0.1`.
- Autenticación por Token en POSTs.
- Eliminación de todos los mocks/valores fijos. Si no hay dato se muestra `-- / OFFLINE`.
- Corrección de mapeo de campos backend-frontend.
- Nueva vista de Reconciliación Bot vs IBKR.

#### Fase 5 — Despliegue en VM Ubuntu (Docker)
- `Dockerfile` aislado (Python 3.11-slim).
- `docker-compose.yml` con `ib-gateway` (`gnzsnz/ib-gateway:latest`) + `darq-bot`.
- Secretos en `.env` fuera de Git.
- Puerto `4002` aislado en la red interna de Docker (`127.0.0.1:4002`).

---

### 3. PROTOCOLO DE VERIFICACIÓN Y TESTING

1. **Pruebas de Unidad (pytest):**
   - Cobertura con mock broker para probar rechazos, timeouts, cancelaciones y cierres.
   - Verificación de que **ningún trade se guarda sin Fill confirmado**.
2. **Pruebas en Seco (Dry Run):**
   - Ejecución con `TRADING_ENABLED: false` logueando señales y contratos calculados.
3. **Paper Trading Staged Rollout:**
   - Activación por etapas (1 semana por capa con 0 discrepancias de reconciliación antes de habilitar la siguiente).
