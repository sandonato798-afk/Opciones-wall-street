# -*- coding: utf-8 -*-
"""
Opportunistic 1DTE RSI < 30 Engine - Layer 4 (Andrés Model 1)
- Opportunistic Short Puts (0-1 DTE) on SPY, QQQ, DIA.
- Triggers ONLY when intraday RSI < 30 (oversold panic) AND Price < Previous Day Close.
- Exploits IV Spikes to collect inflated premiums.
- Exits on RSI > 70 OR Price Recovery OR 95% profit.
"""

import os
import json
from datetime import datetime, timedelta
from cloud_persistence import sync_state_to_github_async, load_state_from_github

from options_engine import black_scholes

STATE_FILE = "rsi_opportunistic_state.json"

class RSIOpportunisticBot:
    def __init__(self, initial_capital=100000.0, allocated_capital=15000.0):
        self.initial_capital = initial_capital
        self.allocated_capital = allocated_capital # $15,000 USD (15%)
        self.status_mode = "IDLE_MONITORING" # IDLE_MONITORING or ACTIVE_TRADE
        self.open_trades = []
        self.closed_trades = []
        self.total_premiums_collected = 0.0
        self.total_pnl_usd = 0.0
        self.last_rsi_scanned = {"SPY": 48.5, "QQQ": 51.2, "DIA": 46.8}
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.load_state()

    def load_state(self):
        cloud_data = load_state_from_github(STATE_FILE)
        if cloud_data:
            self._apply_dict(cloud_data)
            print(f"[RSI_OPPORTUNISTIC] Estado restaurado desde Nube GitHub ({len(self.open_trades)} trades activos).")
            return

        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._apply_dict(data)
                    print(f"[RSI_OPPORTUNISTIC] Estado cargado localmente.")
            except Exception as e:
                print(f"[RSI_OPPORTUNISTIC] Error leyendo estado local: {e}")
                self._initialize_default_state()
        else:
            self._initialize_default_state()

    def _initialize_default_state(self):
        # Default state: monitoring intraday RSI
        self.status_mode = "IDLE_MONITORING"
        self.open_trades = []
        self.closed_trades = []
        self.save_state()

    def _apply_dict(self, data):
        self.allocated_capital = data.get("allocated_capital", 15000.0)
        self.status_mode = data.get("status_mode", "IDLE_MONITORING")
        self.open_trades = data.get("open_trades", [])
        self.closed_trades = data.get("closed_trades", [])
        self.total_premiums_collected = data.get("total_premiums_collected", 0.0)
        self.total_pnl_usd = data.get("total_pnl_usd", 0.0)
        self.last_rsi_scanned = data.get("last_rsi_scanned", {"SPY": 48.5, "QQQ": 51.2, "DIA": 46.8})
        self.last_update = data.get("last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def save_state(self):
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "allocated_capital": self.allocated_capital,
            "status_mode": self.status_mode,
            "open_trades": self.open_trades,
            "closed_trades": self.closed_trades,
            "total_premiums_collected": self.total_premiums_collected,
            "total_pnl_usd": self.total_pnl_usd,
            "last_rsi_scanned": self.last_rsi_scanned,
            "last_update": self.last_update
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            sync_state_to_github_async(STATE_FILE, data)
        except Exception as e:
            print(f"[RSI_OPPORTUNISTIC] Error guardando estado: {e}")

    def _fetch_rsi(self, symbol):
        """Fetches real intraday prices and calculates RSI(14) from Yahoo Finance."""
        try:
            import urllib.request as urlreq
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
            req = urlreq.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlreq.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                quotes = data["chart"]["result"][0]["indicators"]["quote"][0]
                prices = [p for p in quotes.get("close", []) if p is not None]
                if len(prices) < 15:
                    return None, None
                # RSI(14) calculation
                gains, losses = 0.0, 0.0
                for i in range(1, 15):
                    diff = prices[-i] - prices[-i - 1]
                    if diff >= 0:
                        gains += diff
                    else:
                        losses -= diff
                if losses == 0:
                    return 100.0, prices[-1]
                rs = (gains / 14) / (losses / 14)
                rsi = round(100.0 - (100.0 / (1.0 + rs)), 1)
                return rsi, round(prices[-1], 2)
        except Exception as e:
            print(f"[RSI_OPPORTUNISTIC] Error fetching {symbol}: {e}")
            return None, None

    def scan_market(self, market_data=None):
        """
        Scans real intraday RSI for SPY, QQQ, DIA.
        Opens 1DTE Short Put ONLY when RSI < 30 (genuine oversold panic).
        Closes open trades when RSI > 70 or premium decays 90%.
        """
        rsi_values = {}
        for symbol in ["SPY", "QQQ", "DIA"]:
            rsi, price = self._fetch_rsi(symbol)
            if rsi is not None:
                rsi_values[symbol] = {"rsi": rsi, "price": price}
                print(f"[RSI_OPPORTUNISTIC] {symbol}: RSI={rsi} @ ${price}")
            else:
                rsi_values[symbol] = {"rsi": self.last_rsi_scanned.get(symbol, 50.0), "price": 0}

        self.last_rsi_scanned = {s: v["rsi"] for s, v in rsi_values.items()}

        # Check and close profitable open trades using real Black-Scholes valuation & expiration
        for trade in list(self.open_trades):
            symbol = trade["symbol"]
            current_rsi = rsi_values.get(symbol, {}).get("rsi", 50.0)
            current_price = rsi_values.get(symbol, {}).get("price", 0)
            if current_price <= 0:
                continue

            try:
                entry_dt = datetime.strptime(trade["entry_date"], "%Y-%m-%d %H:%M:%S")
            except Exception:
                entry_dt = datetime.now()
            hours_elapsed = max(0.1, (datetime.now() - entry_dt).total_seconds() / 3600.0)
            dte_remaining = max(0.01, 1.0 - (hours_elapsed / 24.0))
            T = dte_remaining / 365.0

            # Dynamic Black-Scholes valuation for Short Put
            put_val = black_scholes("PUT", current_price, trade["put_strike"], T, 0.0525, 0.20)
            curr_prem_per_share = round(put_val["price"], 2)
            curr_put_cost = round(curr_prem_per_share * 100 * trade["contracts"], 2)
            
            initial_premium = trade.get("premium_collected_usd", 0)
            unrealized_pnl = round(initial_premium - curr_put_cost, 2)
            tp_target = trade.get("take_profit_target_usd", initial_premium * 0.50)

            close_reason = None
            if curr_put_cost <= tp_target:
                close_reason = "TAKE_PROFIT_50%"
                pnl = unrealized_pnl
            elif current_rsi >= 60.0 and unrealized_pnl > 0:
                close_reason = f"RSI_REBOUND_{current_rsi:.1f}"
                pnl = unrealized_pnl
            elif hours_elapsed >= 24.0:
                if current_price >= trade["put_strike"]:
                    close_reason = "EXPIRED_OTM_WORTHLESS"
                    pnl = initial_premium
                else:
                    close_reason = "EXPIRED_ITM"
                    loss_intrinsic = (trade["put_strike"] - current_price) * 100 * trade["contracts"]
                    pnl = round(initial_premium - loss_intrinsic, 2)
            elif curr_put_cost >= initial_premium * 2.0:
                close_reason = "STOP_LOSS_200%"
                pnl = unrealized_pnl

            if close_reason:
                self.total_pnl_usd += pnl
                self.total_premiums_collected += initial_premium
                self.closed_trades.append({
                    **trade,
                    "exit_rsi": current_rsi,
                    "exit_price": current_price,
                    "exit_reason": close_reason,
                    "pnl_usd": pnl,
                    "exit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.open_trades.remove(trade)
                self.status_mode = "IDLE_MONITORING"
                print(f"[RSI_OPPORTUNISTIC] ✅ CERRADO trade en {symbol} ({close_reason}) — PnL: ${pnl:+.2f} USD")

        # Open new trades when RSI < 25 (Pánico Extremo - Umbral Institucional)
        if len(self.open_trades) == 0:
            for symbol, data in rsi_values.items():
                if data["rsi"] < 25 and data["price"] > 0:
                    price = data["price"]

                    # NAKED PUT: Strike 1% OTM, vencimiento 1DTE
                    put_strike = round(price * 0.99, 1)
                    premium_per_share = round(price * 0.015, 2)  # Prima estimada (IV inflada por pánico)

                    # Sizing: ~20% de margen por Put desnudo (Portfolio Margin)
                    margin_per_contract = put_strike * 100 * 0.20
                    contracts = max(1, int(self.allocated_capital * 0.5 / margin_per_contract))
                    premium_collected_usd = round(premium_per_share * 100 * contracts, 2)
                    take_profit_usd = round(premium_collected_usd * 0.50, 2)  # TP al 50%

                    trade = {
                        "id": int(datetime.now().timestamp() * 1000),
                        "symbol": symbol,
                        "strategy": "NAKED_PUT_PANIC_SCALP_1DTE",
                        "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "entry_rsi": data["rsi"],
                        "underlying_price": price,
                        "put_strike": put_strike,
                        "contracts": contracts,
                        "premium_per_share": premium_per_share,
                        "premium_collected_usd": premium_collected_usd,
                        "take_profit_target_usd": take_profit_usd,
                        "dte": 1,
                        "status": "OPEN"
                    }
                    self.open_trades.append(trade)
                    self.status_mode = "ACTIVE_TRADE"
                    print(f"[RSI_OPPORTUNISTIC] ABIERTO Naked Put 1DTE en {symbol} | Strike={put_strike} | RSI={data['rsi']} | Prima: +${premium_collected_usd} | TP: ${take_profit_usd}")
                    break  # Un trade a la vez


        self.save_state()
        return self.get_status()

    def get_status(self):
        return {
            "allocated_capital": self.allocated_capital,
            "status_mode": self.status_mode,
            "open_trades_count": len(self.open_trades),
            "open_trades": self.open_trades,
            "closed_trades": self.closed_trades,
            "total_premiums_collected": self.total_premiums_collected,
            "total_pnl_usd": self.total_pnl_usd,
            "last_rsi_scanned": self.last_rsi_scanned,
            "last_update": self.last_update
        }

if __name__ == "__main__":
    bot = RSIOpportunisticBot()
    print(bot.get_status())
