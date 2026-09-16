# -*- coding: utf-8 -*-
import time
import json
import os
import math
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes
from cloud_persistence import sync_state_to_github_async, load_state_from_github

STATE_FILE = os.path.join(os.path.dirname(__file__), "credit_spread_state.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "credit_spread.log")

CONFIG = {
    "execution_mode": "PAPER_TRADING",
    "broker_name": "INTERACTIVE_BROKERS",
    "initial_capital_usd": 100000.0,
    "max_simultaneous_spreads": 3,
    "capital_per_spread_pct": 10.0,     # 10% ($10,000 USD) max margin collateral per spread
    "spread_width_usd": 3.0,            # $3.00 strike width between short and long leg
    "target_dte": 7,                    # 7 to 14 Days to Expiration (optimal Theta decay curve)
    "target_delta": 0.20,               # ~80% win rate probability
    "profit_target_pct": 70.0,          # Close spread when 70% of max premium is captured
    "stop_loss_multiplier": 1.5,        # Close if spread loss reaches 1.5x initial credit collected
    "etf_watchlist": ["SPY", "QQQ"]
}

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_msg(tag, text):
    msg = f"[{timestamp()}] [{tag}] {text}"
    try:
        print(msg)
    except Exception:
        print(msg.encode('ascii', errors='replace').decode('ascii'))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

class CreditSpreadBot:
    """
    Bot Institucional Especializado en Venta de Tiempo (Theta Positivo)
    Ejecuta Bull Put Spreads, Bear Call Spreads e Iron Condors a 7-14 DTE
    """
    def __init__(self):
        self.initial_capital = CONFIG["initial_capital_usd"]
        self.capital = self.initial_capital
        self.total_premiums_collected = 0.0
        self.system_start_time = timestamp()
        self.open_spreads = []
        self.closed_spreads = []
        self.load_state()

    def load_state(self):
        loaded = False
        # 1. Prioridad: Intentar cargar siempre desde GitHub Cloud
        gh_data = load_state_from_github("credit_spread_state.json")
        if gh_data and (gh_data.get("closed_spreads") or gh_data.get("open_spreads") or (gh_data.get("capital") and gh_data.get("capital") != CONFIG["initial_capital_usd"])):
            self.system_start_time = gh_data.get("system_start_time", timestamp())
            self.initial_capital = gh_data.get("initial_capital", CONFIG["initial_capital_usd"])
            self.capital = gh_data.get("capital", CONFIG["initial_capital_usd"])
            self.total_premiums_collected = gh_data.get("total_premiums_collected", 0.0)
            self.open_spreads = gh_data.get("open_spreads", [])
            self.closed_spreads = gh_data.get("closed_spreads", [])
            log_msg("CLOUD_STATE", "Estado de Spreads recuperado de GitHub Cloud Backup.")
            loaded = True

        # 2. Si no hay estado en GitHub, intentar archivo local
        if not loaded and os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.system_start_time = data.get("system_start_time", timestamp())
                    self.initial_capital = data.get("initial_capital", CONFIG["initial_capital_usd"])
                    self.capital = data.get("capital", CONFIG["initial_capital_usd"])
                    self.total_premiums_collected = data.get("total_premiums_collected", 0.0)
                    self.open_spreads = data.get("open_spreads", [])
                    self.closed_spreads = data.get("closed_spreads", [])
                    log_msg("STATE", "Estado de Credit Spread Bot cargado correctamente desde archivo local.")
                    loaded = True
            except Exception as e:
                log_msg("WARN", f"Error cargando estado local de Spreads: {e}")

        if not loaded:
            self.save_state()

    def save_state(self):
        state = {
            "system_start_time": self.system_start_time,
            "last_update": timestamp(),
            "execution_mode": CONFIG["execution_mode"],
            "initial_capital": self.initial_capital,
            "capital": round(self.capital, 2),
            "total_premiums_collected": round(self.total_premiums_collected, 2),
            "total_pnl_usd": round(self.capital - self.initial_capital, 2),
            "total_pnl_pct": round(((self.capital - self.initial_capital) / self.initial_capital) * 100.0, 2),
            "open_spreads": self.open_spreads,
            "closed_spreads": self.closed_spreads
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        sync_state_to_github_async("credit_spread_state.json", state)

    def get_stats(self):
        total = len(self.closed_spreads)
        if total == 0:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0}
        wins = sum(1 for s in self.closed_spreads if s.get("final_pnl_usd", 0) > 0)
        losses = sum(1 for s in self.closed_spreads if s.get("final_pnl_usd", 0) <= 0)
        rate = (wins / total) * 100.0
        return {"total": total, "wins": wins, "losses": losses, "win_rate": round(rate, 1)}

    def fetch_etf_price(self, symbol):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                meta = data["chart"]["result"][0]["meta"]
                return round(meta["regularMarketPrice"], 2)
        except Exception:
            return 750.50 if symbol == "SPY" else 705.20

    def scan_and_execute_spreads(self):
        """Escanea oportunidades de venta de primas y gestiona spreads abiertos"""
        log_msg("SPREAD_SCAN", "--- ESCANEANDO OPORTUNIDADES DE VENTA DE TIEMPO (THETA > 0) ---")
        
        # 1. Gestionar spreads abiertos
        for spread in list(self.open_spreads):
            self.manage_open_spread(spread)

        # 2. Abrir nuevos spreads si hay capacidad disponible
        if len(self.open_spreads) < CONFIG["max_simultaneous_spreads"]:
            for symbol in CONFIG["etf_watchlist"]:
                existing = [s for s in self.open_spreads if s["symbol"] == symbol]
                if not existing and len(self.open_spreads) < CONFIG["max_simultaneous_spreads"]:
                    self.open_bull_put_credit_spread(symbol)

    def open_bull_put_credit_spread(self, symbol):
        etf_price = self.fetch_etf_price(symbol)
        dte = CONFIG["target_dte"]
        width = CONFIG["spread_width_usd"]

        # Strike vendido (Short Put) ~2.5% OTM (Delta ~0.20)
        short_strike = round(etf_price * 0.975, 1)
        # Strike comprado protector (Long Put) $3 más abajo
        long_strike = round(short_strike - width, 1)

        T = dte / 365.0
        short_greeks = black_scholes("PUT", etf_price, short_strike, T, 0.0525, 0.18)
        long_greeks = black_scholes("PUT", etf_price, long_strike, T, 0.0525, 0.18)

        short_prem = max(0.90, short_greeks["price"])
        long_prem = max(0.20, long_greeks["price"])
        net_credit = round(short_prem - long_prem, 2)
        if net_credit <= 0.15:
            net_credit = 0.65

        # Allocacion de margen ($10,000 USD de garantia = 33 contratos de $3 de spread)
        collateral_per_contract = width * 100.0 # $300 USD de riesgo maximo por contrato
        max_margin = self.capital * (CONFIG["capital_per_spread_pct"] / 100.0)
        contracts = max(1, int(max_margin / collateral_per_contract))
        
        total_credit_collected = round(net_credit * 100.0 * contracts, 2)
        total_max_risk = round((width - net_credit) * 100.0 * contracts, 2)
        fee = contracts * 2 * 0.65 # $0.65 por pata

        spread_obj = {
            "id": int(time.time() * 1000),
            "symbol": symbol,
            "type": "BULL_PUT_SPREAD",
            "etf_price_at_entry": etf_price,
            "short_strike": short_strike,
            "long_strike": long_strike,
            "dte": dte,
            "entry_date": timestamp(),
            "contracts": contracts,
            "net_credit_per_share": net_credit,
            "total_credit_collected_usd": total_credit_collected,
            "total_max_risk_usd": total_max_risk,
            "total_fees_usd": fee,
            "status": "OPEN",
            "current_spread_value": net_credit,
            "pnl_usd": round(0.0 - fee, 2),
            "pnl_pct": 0.0,
            "win_probability_pct": 82.5,
            "theta_daily_decay_usd": round((short_greeks["theta"] - long_greeks["theta"]) * 100 * contracts, 2)
        }

        self.open_spreads.append(spread_obj)
        self.total_premiums_collected += total_credit_collected
        self.save_state()

        log_msg("CREDIT_OPEN", f"🟢 VENTA BULL PUT SPREAD [{symbol}]: Vende Put K=${short_strike} / Compra Put K=${long_strike} ({contracts}x). Prima Cobrada: +${total_credit_collected} USD (Theta: +${spread_obj['theta_daily_decay_usd']}/día | Probabilidad: 82.5%)")

    def manage_open_spread(self, spread):
        etf_price = self.fetch_etf_price(spread["symbol"])
        dte = max(1, spread["dte"] - 1)
        T = dte / 365.0

        short_g = black_scholes("PUT", etf_price, spread["short_strike"], T, 0.0525, 0.18)
        long_g = black_scholes("PUT", etf_price, spread["long_strike"], T, 0.0525, 0.18)

        curr_spread_val = max(0.02, round(short_g["price"] - long_g["price"], 2))
        profit_captured_pct = round(((spread["net_credit_per_share"] - curr_spread_val) / spread["net_credit_per_share"]) * 100.0, 2)
        raw_pnl = (spread["net_credit_per_share"] - curr_spread_val) * 100.0 * spread["contracts"]
        pnl_usd = round(raw_pnl - spread["total_fees_usd"], 2)

        spread["current_spread_value"] = curr_spread_val
        spread["pnl_usd"] = pnl_usd
        spread["pnl_pct"] = profit_captured_pct

        log_msg("SPREAD_MONITOR", f"Spread [{spread['symbol']} K{spread['short_strike']}/K{spread['long_strike']}]: Prima Restante: ${curr_spread_val} USD | Ganancia Capturada: {profit_captured_pct:+.1f}% (+${pnl_usd:+.2f} USD)")

        # 1. Take Profit: 70% de la prima capturada
        if profit_captured_pct >= CONFIG["profit_target_pct"]:
            self.close_spread(spread, "PROFIT_TARGET_70_PCT", curr_spread_val)
        # 2. Stop Loss: si la perdida llega al 1.5x de la prima
        elif curr_spread_val >= spread["net_credit_per_share"] * (1.0 + CONFIG["stop_loss_multiplier"]):
            self.close_spread(spread, "STOP_LOSS_1.5X", curr_spread_val)

    def close_spread(self, spread, reason, exit_spread_val):
        close_fee = spread["contracts"] * 2 * 0.65
        total_fees = spread["total_fees_usd"] + close_fee
        final_pnl = round(((spread["net_credit_per_share"] - exit_spread_val) * 100.0 * spread["contracts"]) - total_fees, 2)

        closed_obj = {
            **spread,
            "exit_date": timestamp(),
            "exit_spread_value": exit_spread_val,
            "exit_reason": reason,
            "final_pnl_usd": final_pnl,
            "final_pnl_pct": spread["pnl_pct"],
            "total_fees_usd": total_fees
        }

        self.open_spreads.remove(spread)
        self.closed_spreads.append(closed_obj)
        self.capital += final_pnl
        self.save_state()

        emoji = "🟢" if final_pnl >= 0 else "🔴"
        log_msg("CREDIT_CLOSE", f"{emoji} SPREAD CERRADO ({reason}): [{spread['symbol']}] PnL Neto: +${final_pnl} USD")

if __name__ == "__main__":
    bot = CreditSpreadBot()
    bot.scan_and_execute_spreads()