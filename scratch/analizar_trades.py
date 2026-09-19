import json
from datetime import datetime

with open('rsi_opportunistic_state.json', 'r', encoding='utf-8') as f:
    rsi = json.load(f)

print('=== ANALISIS RSI TRADES HOY ===\n')
trades = rsi['closed_trades']
bugs_encontrados = []

for t in trades:
    premium = t['premium_collected_usd']
    pnl = t['pnl_usd']
    tp_target = t['take_profit_target_usd']
    pnl_pct = round(pnl / premium * 100, 1)
    
    entry = datetime.strptime(t['entry_date'], '%Y-%m-%d %H:%M:%S')
    exit_dt = datetime.strptime(t['exit_date'], '%Y-%m-%d %H:%M:%S')
    segundos = (exit_dt - entry).seconds
    
    precio_sobre_strike = t['exit_price'] > t['put_strike']
    
    print(f"[{t['symbol']}] RSI_entrada={t['entry_rsi']} | RSI_salida={t['exit_rsi']}")
    print(f"  Strike={t['put_strike']} | Precio_entrada={t['underlying_price']} | Precio_salida={t['exit_price']}")
    print(f"  Prima={premium} | PnL={pnl} ({pnl_pct}% retenido) | TP_target(50%)={tp_target}")
    print(f"  Duracion: {segundos} segundos | Razon: {t['exit_reason']}")
    print(f"  Precio > Strike al cerrar: {precio_sobre_strike}")
    
    # Deteccion de bugs
    if segundos <= 65:
        bugs_encontrados.append(f"BUG: Trade {t['symbol']} cerrado en {segundos}s (1 ciclo de bot = ciclo instantaneo)")
    if pnl_pct > 60:
        bugs_encontrados.append(f"BUG: PnL de {pnl_pct}% cuando target es 50% -> cierre NO fue por TP real")
    if t['entry_rsi'] > 25:
        bugs_encontrados.append(f"BUG: Trade abierto con RSI={t['entry_rsi']} (regla: RSI < 25)")
    print()

print(f"TOTAL PnL: ${rsi['total_pnl_usd']} | Primas cobradas: ${rsi['total_premiums_collected']}")
print(f"Trades cerrados: {len(trades)} | Win rate: 100%")
print()
print("=== BUGS DETECTADOS ===")
for b in bugs_encontrados:
    print(f"  [!] {b}")
