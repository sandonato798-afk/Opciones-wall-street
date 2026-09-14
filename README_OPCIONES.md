# Sistema de Opciones sobre ETFs de Wall Street

Módulo especializado para el análisis, modelado Black-Scholes, simulación de curva de rendimiento (Payoff) y Paper Trading de opciones sobre los principales ETFs de Wall Street:

- **SPY** (S&P 500 Index)
- **QQQ** (Nasdaq 100 Index)
- **IWM** (Russell 2000 Small Caps)
- **TLT** (Bonos del Tesoro EE.UU. a 20+ Años)
- **GLD** (Oro Físico)

---

## 🚀 Características Principales

1. **Motor de Valoración Black-Scholes Integrado**:
   - Cálculo exacto de precio teórico de Calls y Puts.
   - Cálculo de Griegas en tiempo real: **Delta ($\Delta$)**, **Gamma ($\Gamma$)**, **Theta ($\Theta$)**, **Vega ($\nu$)** y **Rho ($\rho$)**.
   - Estimación de IV Rank (Rango de Volatilidad Implícita) para seleccionar entre compra vs venta de opciones.

2. **Cadenas de Opciones (Option Chains)**:
   - Selección dinámica de vencimientos / DTE (7, 15, 30, 45, 60 Días).
   - Matriz comparativa de Calls & Puts clasificados por moneyness (ITM, ATM, OTM), deltas y decay de theta.

3. **Arquitecto de Estrategias y Gráfico de Rendimiento (Payoff Curve)**:
   - Simulación visual de curvas de ganancia/pérdida al vencimiento.
   - Presets integrados de estrategias profesionales:
     - **Covered Call** (Venta de Call cubierta sobre tenencia de ETF).
     - **Cash-Secured Put** (Venta de Put para compra con descuento).
     - **Bull Put Spread (Credit Spread)** (Cobro de prima con riesgo acotado).
     - **Iron Condor** (Estrategia neutral de alta probabilidad de cobro por colapso de IV).

4. **Portafolio Simulado (Paper Trading)**:
   - Medición de la exposición neta de griegas del portafolio (Net Delta y Net Theta decay diario).
   - Registro de prima neta cobrada/pagada en USD.

---

## 💻 Cómo Iniciar el Sistema

1. **Hacer doble clic** en `INICIAR_SISTEMA_OPCIONES.bat`.
2. O ejecutar directamente desde la terminal:
   ```bash
   python app.py
   ```
3. Se abrirá automáticamente el panel web en tu navegador en `http://localhost:5050`.
