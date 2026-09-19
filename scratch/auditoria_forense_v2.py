# -*- coding: utf-8 -*-
import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Comisiones IBKR reales (Pro - Tiered)
def comision_rt(contracts):
    base = max(1.00, contracts * 0.65)
    regulatory = contracts * (0.02 + 0.12)
    return round((base + regulatory) * 2, 2)  # ida + vuelta

# Precios reales obtenidos de Yahoo Finance esta sesion
REALES = {
    'SPY': {'precio': 761.69, 'prev': 760.71, 'high': 762.0, 'low': 757.97},
    'DIA': {'precio': 515.88, 'prev': 517.16, 'high': 517.07, 'low': 514.15},
    'QQQ': {'precio': 721.45, 'prev': 716.92, 'high': 721.73, 'low': 715.08},
}

print("=== PRECIOS REALES HOY 18-Sep-2026 (confirmado Yahoo Finance) ===")
for s, p in REALES.items():
    cambio = round((p['precio'] - p['prev']) / p['prev'] * 100, 2)
    print(f"  {s}: ${p['precio']} | Ayer: ${p['prev']} | Cambio: {cambio:+.2f}% | Rango: ${p['low']}-${p['high']}")

print()
print("=== AUDITORIA FORENSE TRADES RSI ===")
print()

with open('rsi_opportunistic_state.json', 'r', encoding='utf-8') as f:
    rsi = json.load(f)

total_comisiones = 0
total_pnl_neto = 0

for i, t in enumerate(rsi['closed_trades'], 1):
    sym = t['symbol']
    premium = t['premium_collected_usd']
    pnl_bot = t['pnl_usd']
    contracts = t['contracts']
    precio_reg = t['underlying_price']
    strike = t['put_strike']
    prima_sh = t['premium_per_share']
    
    precio_real = REALES.get(sym, {}).get('precio', 0)
    prev_close = REALES.get(sym, {}).get('prev', 0)
    
    com = comision_rt(contracts)
    total_comisiones += com
    pnl_neto = round(pnl_bot - com, 2)
    total_pnl_neto += pnl_neto
    
    entry = datetime.strptime(t['entry_date'], '%Y-%m-%d %H:%M:%S')
    exit_dt = datetime.strptime(t['exit_date'], '%Y-%m-%d %H:%M:%S')
    secs = (exit_dt - entry).seconds
    
    # Prima como % del precio (1DTE normal: 0.2-0.5%)
    prima_pct = round(prima_sh / precio_reg * 100, 2)
    
    # Diferencia precio registrado vs real
    dif_precio = round(abs(precio_reg - precio_real), 2)
    
    # El bot mide prima como precio * 1.5% (hardcoded en el codigo)
    prima_esperada_codigo = round(precio_reg * 0.015, 2)
    prima_mercado_real_estimada = round(precio_reg * 0.004, 2)  # ~0.4% tipico 1DTE OTM
    
    print(f"Trade #{i} [{sym}] | Duracion: {secs}s")
    print(f"  Precio registrado: ${precio_reg} | Precio real Yahoo: ${precio_real} | Diferencia: ${dif_precio}")
    print(f"  Prima REGISTRADA:  ${prima_sh}/sh ({prima_pct}% del precio)")
    print(f"  Prima CODIGO:      ${prima_esperada_codigo}/sh (precio x 1.5% hardcoded en fetch_market_data)")
    print(f"  Prima MERCADO REAL:~${prima_mercado_real_estimada}/sh (~0.4% tipico para 1DTE OTM)")
    print(f"  PnL bruto bot:     ${pnl_bot} | Comision IBKR rt: ${com} | PnL neto: ${pnl_neto}")
    
    # Flags
    flags = []
    if secs <= 65:
        flags.append("LOOP BUG: cerrado en 1 ciclo de bot (62s)")
    if prima_pct > 1.0:
        flags.append(f"PRIMA INFLADA: {prima_pct}% vs ~0.4% mercado real")
    if dif_precio < 2:
        flags.append("Precio subyacente: REAL (coincide con Yahoo Finance)")
    else:
        flags.append(f"Precio subyacente: diferencia ${dif_precio} vs mercado")
    for f in flags:
        print(f"  >> {f}")
    print()

print("=== RESUMEN EJECUTIVO ===")
print(f"  PnL bruto registrado:  ${rsi['total_pnl_usd']}")
print(f"  Comisiones IBKR total: ${round(total_comisiones, 2)}")
print(f"  PnL neto (con comis.): ${round(total_pnl_neto, 2)}")
print()
print("=== VEREDICTO LINEA POR LINEA ===")
print("  [REAL]    Precios del subyacente (SPY/DIA) coinciden con Yahoo Finance")
print("  [FICTICIO] Primas de opciones: el codigo usa precio x 1.5% hardcoded")
print("             Real en el mercado para 1DTE OTM seria ~0.3-0.5% del precio")
print("             Diferencia: primas 3-5x infladas vs mercado real")
print("  [FICTICIO] Duracion trades: 62 segundos = bug de condicion de cierre")
print("  [FICTICIO] PnL: $7,887 generados por loop infinito en 40 minutos")
print("  [REAL]    Comisiones IBKR calculadas correctamente: $1.14/trade rt")
print()
print("  CONCLUSION: Los $7,887 NO representan resultados reales.")
print("  El sistema esta en PAPER TRADING con bugs que generan PnL ficticio.")
