import json
import os
import math
import sys
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes

# Configure UTF-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')

RESULT_FILE = os.path.join(os.path.dirname(__file__), "backtest_results_1y.json")
RESULT_TXT = os.path.join(os.path.dirname(__file__), "backtest_results_1y.txt")

def fetch_1y_historical_data(symbol="SPY"):
    """Descarga 1 año de datos diarios históricos reales desde Yahoo Finance API"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1y"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            
            close_prices = quotes["close"]
            high_prices = quotes.get("high", close_prices)
            low_prices = quotes.get("low", close_prices)

            history = []
            for i in range(len(timestamps)):
                if close_prices[i] is not None:
                    history.append({
                        "date": datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d"),
                        "close": round(close_prices[i], 2),
                        "high": round(high_prices[i] if high_prices[i] is not None else close_prices[i], 2),
                        "low": round(low_prices[i] if low_prices[i] is not None else close_prices[i], 2)
                    })
            return history
    except Exception as e:
        print(f"⚠️ Error descargando datos históricos para {symbol}: {e}")
        return []

def calculate_ema(prices, period):
    if len(prices) < period:
        return prices[-1]
    multiplier = 2.0 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 100.0
    rs = (gains / period) / (losses / period)
    return 100.0 - (100.0 / (1.0 + rs))

def run_1y_backtest(initial_capital=10000.0, symbol="SPY"):
    print(f"🚀 INICIANDO BACKTEST HISTÓRICO DE 1 AÑO (365 DÍAS) PARA [{symbol}]...")
    history_data = fetch_1y_historical_data(symbol)
    if not history_data or len(history_data) < 50:
        print("Fallo descarga de datos históricos.")
        return

    start_price = history_data[0]["close"]
    end_price = history_data[-1]["close"]
    total_days = len(history_data)

    print(f"📊 Datos históricos cargados: {total_days} días bursátiles.")
    print(f"   Precio Inicio (hace 1 año): ${start_price} USD")
    print(f"   Precio Final (actual): ${end_price} USD")

    # 1. BENCHMARK: Buy & Hold ETF
    buy_hold_shares = initial_capital / start_price
    buy_hold_final_usd = buy_hold_shares * end_price
    buy_hold_return_pct = ((buy_hold_final_usd - initial_capital) / initial_capital) * 100.0

    # 2. STRATEGY MODEL A: Day Trading 0-DTE Cash Only
    cash_a = initial_capital
    trades_a = []
    daily_prices_so_far = []

    for idx, day in enumerate(history_data):
        daily_prices_so_far.append(day["close"])
        if len(daily_prices_so_far) < 22:
            continue

        ema9 = calculate_ema(daily_prices_so_far, 9)
        ema21 = calculate_ema(daily_prices_so_far, 21)
        rsi = calculate_rsi(daily_prices_so_far, 14)

        # Signal evaluation
        signal = None
        if ema9 > ema21 and rsi < 68:
            signal = "CALL"
        elif ema9 < ema21 and rsi > 32:
            signal = "PUT"

        if signal:
            # Simulate 0-DTE trade entry & exit
            entry_p = day["close"]
            high_p = day["high"]
            low_p = day["low"]

            # Estimate option premium
            bs_greeks = black_scholes(signal, entry_p, entry_p, 1/365.0, 0.0525, 0.18)
            opt_premium = max(0.50, bs_greeks["price"])
            
            # 5% capital allocation
            alloc_usd = cash_a * 0.05
            contracts = max(1, int(alloc_usd / (opt_premium * 100.0)))
            open_fee = contracts * 0.65
            close_fee = contracts * 0.65

            # Day movement
            day_pct = ((high_p - low_p) / entry_p) * 100.0
            if signal == "CALL" and day["close"] > entry_p:
                gain_pct = min(35.0, day_pct * 8.0)
            elif signal == "PUT" and day["close"] < entry_p:
                gain_pct = min(35.0, day_pct * 8.0)
            else:
                gain_pct = -18.0

            opt_pnl_usd = (opt_premium * (gain_pct / 100.0) * 100.0 * contracts) - open_fee - close_fee
            cash_a += opt_pnl_usd

            trades_a.append({
                "date": day["date"],
                "signal": signal,
                "contracts": contracts,
                "pnl_usd": round(opt_pnl_usd, 2),
                "pnl_pct": round(gain_pct, 2)
            })

    model_a_final_usd = cash_a
    model_a_return_pct = ((model_a_final_usd - initial_capital) / initial_capital) * 100.0

    # 3. STRATEGY MODEL B: Hybrid Wheel + 100% Auto-Compounding Reinvestment
    cash_b = 0.0
    shares_b = initial_capital / start_price # 100% invested in ETF from day 1
    total_premiums_b = 0.0
    trades_b = []

    for idx, day in enumerate(history_data):
        # Every 20 trading days (~1 month), sell 30-DTE Option & Auto-Reinvest Premium
        if idx > 0 and idx % 20 == 0:
            curr_p = day["close"]
            strike = round(curr_p * 1.03, 1) # 3% OTM Covered Call
            greeks = black_scholes("CALL", curr_p, strike, 30/365.0, 0.0525, 0.18)
            premium = max(2.50, greeks["price"])
            
            # Premium Collected
            monthly_income_usd = round(premium * 100.0 * max(1, int(shares_b / 100.0 or 1)), 2)
            fee = max(1, int(shares_b / 100.0 or 1)) * 1.30
            net_income_usd = monthly_income_usd - fee
            
            total_premiums_b += net_income_usd

            # AUTO-COMPOUNDING: Reinvest 100% into buying MORE ETF Shares
            new_shares = net_income_usd / curr_p
            shares_b += new_shares

            trades_b.append({
                "date": day["date"],
                "etf_price": curr_p,
                "net_income_usd": net_income_usd,
                "new_shares": round(new_shares, 4),
                "total_shares_now": round(shares_b, 4)
            })

    model_b_final_usd = shares_b * end_price
    model_b_return_pct = ((model_b_final_usd - initial_capital) / initial_capital) * 100.0

    # Calculate Win Rates
    wins_a = sum(1 for t in trades_a if t["pnl_usd"] > 0)
    win_rate_a = (wins_a / len(trades_a) * 100.0) if trades_a else 0.0

    summary = {
        "symbol": symbol,
        "period": "1 Año Histórico (365 Días Bursátiles Reales)",
        "initial_capital_usd": initial_capital,
        "etf_start_price": start_price,
        "etf_end_price": end_price,
        "results": {
            "buy_and_hold": {
                "name": "Buy & Hold ETF (Benchmark S&P 500)",
                "final_capital_usd": round(buy_hold_final_usd, 2),
                "profit_usd": round(buy_hold_final_usd - initial_capital, 2),
                "return_pct": round(buy_hold_return_pct, 2)
            },
            "model_a_daytrade": {
                "name": "Modelo A: Day Trading 0-DTE en Efectivo",
                "final_capital_usd": round(model_a_final_usd, 2),
                "profit_usd": round(model_a_final_usd - initial_capital, 2),
                "return_pct": round(model_a_return_pct, 2),
                "total_trades": len(trades_a),
                "wins": wins_a,
                "win_rate_pct": round(win_rate_a, 1)
            },
            "model_b_wheel_compounding": {
                "name": "Modelo B: Rueda Híbrida + Interés Compuesto (Re-Inversión)",
                "final_capital_usd": round(model_b_final_usd, 2),
                "profit_usd": round(model_b_final_usd - initial_capital, 2),
                "return_pct": round(model_b_return_pct, 2),
                "initial_shares": round(initial_capital / start_price, 2),
                "final_shares": round(shares_b, 2),
                "new_shares_added": round(shares_b - (initial_capital / start_price), 2),
                "total_premiums_reinvested_usd": round(total_premiums_b, 2)
            }
        }
    }

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    report_txt = f"""
========================================================================================
    SIMULACIÓN HISTÓRICA DE 1 AÑO (365 DÍAS REALES): COMPARA DE MODELOS DE BOT
========================================================================================
• Activo Evaluado: [{symbol}] SPDR S&P 500 ETF Trust
• Capital Inicial Simulado: ${initial_capital:,.2f} USD
• Precio Inicial Hace 1 Año: ${start_price:.2f} USD  |  Precio Actual: ${end_price:.2f} USD

----------------------------------------------------------------------------------------
1. BENCHMARK: BUY & HOLD (Comprar y Mantener el ETF en Cartera)
----------------------------------------------------------------------------------------
• Capital Final                      : ${buy_hold_final_usd:,.2f} USD
• Ganancia Neta                      : +${buy_hold_final_usd - initial_capital:,.2f} USD
• RENDIMIENTO NETO EN 1 AÑO          : +{buy_hold_return_pct:.2f}%

----------------------------------------------------------------------------------------
2. MODELO A: DAY TRADING 0-DTE EN EFECTIVO (Operaciones Intradiarias)
----------------------------------------------------------------------------------------
• Capital Final                      : ${model_a_final_usd:,.2f} USD
• Ganancia Neta                      : +${model_a_final_usd - initial_capital:,.2f} USD
• RENDIMIENTO NETO EN 1 AÑO          : +{model_a_return_pct:.2f}%
• Total de Operaciones Ejecutadas   : {len(trades_a)} trades
• Operaciones Ganadoras              : {wins_a} ({win_rate_a:.1f}% Win Rate)

----------------------------------------------------------------------------------------
3. MODELO B: RUEDA HÍBRIDA + INTERÉS COMPUESTOS (RE-INVERSIÓN EN ACCIONES) ⭐⭐⭐⭐⭐
----------------------------------------------------------------------------------------
• Capital Final (Patrimonio NAV)    : ${model_b_final_usd:,.2f} USD
• Ganancia Neta                      : +${model_b_final_usd - initial_capital:,.2f} USD
• RENDIMIENTO NETO EN 1 AÑO          : +{model_b_return_pct:.2f}%
• Acciones Iniciales Compradas      : {initial_capital / start_price:.2f} acciones
• Acciones Finales Acumuladas       : {shares_b:.2f} acciones (+{shares_b - (initial_capital / start_price):.2f} compradas con primas)
• Primas Totales Cobradas & Re-invertidas: +${total_premiums_b:,.2f} USD
========================================================================================
"""
    with open(RESULT_TXT, "w", encoding="utf-8") as f:
        f.write(report_txt)

    print(report_txt)
    return summary

if __name__ == "__main__":
    run_1y_backtest()
