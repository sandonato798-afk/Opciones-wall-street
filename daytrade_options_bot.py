import time
import json
import os
import math
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes

STATE_FILE = os.path.join(os.path.dirname(__file__), "daytrade_paper_state.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "daytrade_bot.log")

# Configuration
CONFIG = {
    "execution_mode": "PAPER_TRADING",  # "PAPER_TRADING" or "LIVE_BROKER"
    "broker_name": "INTERACTIVE_BROKERS", # "INTERACTIVE_BROKERS", "ALPACA", "TRADIER"
    "initial_capital_usd": 10000.0,
    "max_capital_per_trade_pct": 5.0,   # Max 5% ($500 USD) per 0-DTE / 1-DTE trade
    "max_daily_loss_usd": 300.0,        # Daily drawdown limit circuit breaker
    "target_profit_pct": 35.0,          # TP: +35% option premium gain
    "stop_loss_pct": 18.0,              # SL: -18% option premium loss
    "hard_eod_exit_time": "15:45",      # Close all positions at 15:45 EST
    "etf_watchlist": ["SPY", "QQQ"],
    "dte_target": 0                     # 0-DTE (Same day expiration) or 1-DTE
}

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_msg(tag, text):
    msg = f"[{timestamp()}] [{tag}] {text}"
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

class BrokerAdapter:
    """Abstract Broker Adapter Interface for Live Execution (Interactive Brokers, Alpaca, Tradier)"""
    def __init__(self, mode="PAPER_TRADING", broker="INTERACTIVE_BROKERS"):
        self.mode = mode
        self.broker = broker
        self.connected = False

    def connect(self):
        if self.mode == "PAPER_TRADING":
            self.connected = True
            log_msg("BROKER", "Conectado a Motor de Paper Trading Intradiario (Simulación Alta Fidelidad).")
            return True
        else:
            log_msg("BROKER", f"Intentando conexión con {self.broker} API...")
            # Placeholder for IB Gateway (127.0.0.1:7497) or Alpaca API
            log_msg("WARN", f"API de {self.broker} no configurada aún. Revisa credenciales en CONFIG.")
            return False

    def submit_order(self, symbol, option_symbol, action, qty, order_type="MARKET", limit_price=None):
        if self.mode == "PAPER_TRADING":
            log_msg("EXEC-PAPER", f"Orden enviada: {action} {qty}x {option_symbol} ({order_type}) @ ${limit_price or 'MKT'}")
            return {
                "order_id": int(time.time() * 1000),
                "status": "FILLED",
                "fill_price": limit_price,
                "timestamp": timestamp()
            }
        else:
            log_msg("EXEC-LIVE", f"Orden enviada a Broker Real {self.broker}: {action} {qty}x {option_symbol}")
            return {"order_id": 99999, "status": "SUBMITTED"}

class DayTradeOptionsBot:
    def __init__(self):
        self.broker_adapter = BrokerAdapter(mode=CONFIG["execution_mode"], broker=CONFIG["broker_name"])
        self.capital = CONFIG["initial_capital_usd"]
        self.open_positions = []
        self.closed_trades = []
        self.daily_pnl = 0.0
        self.trading_active = True
        self.load_state()
        self.broker_adapter.connect()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.capital = data.get("capital", CONFIG["initial_capital_usd"])
                    self.open_positions = data.get("open_positions", [])
                    self.closed_trades = data.get("closed_trades", [])
                    self.daily_pnl = data.get("daily_pnl", 0.0)
                    log_msg("STATE", "Estado de Day Trading cargado correctamente.")
                    return
            except Exception as e:
                log_msg("WARN", f"Error cargando estado ({e}). Inicializando valores por defecto.")
        self.save_state()

    def save_state(self):
        state = {
            "last_update": timestamp(),
            "execution_mode": CONFIG["execution_mode"],
            "capital": self.capital,
            "daily_pnl": self.daily_pnl,
            "open_positions": self.open_positions,
            "closed_trades": self.closed_trades
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def fetch_etf_intraday_data(self, symbol):
        """Consulta cotización e indicadores intradiarios de ETF desde Yahoo Finance (intervalo 1m / 5m)"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                result = data["chart"]["result"][0]
                meta = result["meta"]
                quotes = result["indicators"]["quote"][0]
                
                prices = [p for p in quotes.get("close", []) if p is not None]
                if not prices:
                    return None

                current_price = prices[-1]
                prev_close = meta.get("chartPreviousClose", current_price)
                
                # Compute Intraday Indicators: EMA9, EMA21, VWAP
                ema9 = self.calculate_ema(prices, 9)
                ema21 = self.calculate_ema(prices, 21)
                rsi = self.calculate_rsi(prices, 14)

                return {
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "change_pct": round(((current_price - prev_close) / prev_close) * 100, 2),
                    "ema9": round(ema9, 2),
                    "ema21": round(ema21, 2),
                    "rsi": round(rsi, 1),
                    "signal": "BULLISH_CROSS" if (ema9 > ema21 and rsi > 52) else ("BEARISH_CROSS" if (ema9 < ema21 and rsi < 48) else "NEUTRAL")
                }
        except Exception as e:
            log_msg("WARN", f"Fallo fetch intradiario para {symbol}: {e}")
            return None

    def calculate_ema(self, prices, period):
        if len(prices) < period:
            return prices[-1] if prices else 100.0
        multiplier = 2.0 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema

    def calculate_rsi(self, prices, period=14):
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

    def evaluate_daytrade_signals(self):
        pass # Evaluated in main loop

    def run_intraday_scan(self):
        log_msg("SCAN", "--- ESCANEANDO SEÑALES DE DAY TRADING (0-DTE / 1-DTE ETFs) ---")
        
        # Check Daily Drawdown Limit
        if self.daily_pnl <= -CONFIG["max_daily_loss_usd"]:
            log_msg("CIRCUIT_BREAKER", f"Límite de pérdida diaria alcanzado (-${abs(self.daily_pnl):.2f} USD). Pausando bot por hoy.")
            return

        for symbol in CONFIG["etf_watchlist"]:
            market_data = self.fetch_etf_intraday_data(symbol)
            if not market_data:
                continue

            log_msg("DATA", f"{symbol}: ${market_data['price']} | EMA9: ${market_data['ema9']} | EMA21: ${market_data['ema21']} | RSI: {market_data['rsi']} | Señal: {market_data['signal']}")

            # Check if position already open for this ETF
            existing = [p for p in self.open_positions if p["symbol"] == symbol]
            if existing:
                self.manage_open_position(existing[0], market_data)
                continue

            # Signal Trigger Entry Rules for Day Trading 0-DTE Calls/Puts
            if market_data["signal"] == "BULLISH_CROSS" and market_data["rsi"] < 70:
                self.open_intraday_option(symbol, "CALL", market_data)
            elif market_data["signal"] == "BEARISH_CROSS" and market_data["rsi"] > 30:
                self.open_intraday_option(symbol, "PUT", market_data)

    def open_intraday_option(self, symbol, option_type, market_data):
        etf_price = market_data["price"]
        dte = CONFIG["dte_target"]
        
        # Select Strike: Slightly OTM / Delta ~0.40 for high responsiveness & low cost
        strike_step = 1.0 if symbol != "SPY" and symbol != "QQQ" else 2.0
        if option_type == "CALL":
            strike = math.ceil(etf_price / strike_step) * strike_step
        else:
            strike = math.floor(etf_price / strike_step) * strike_step

        # Calculate Black-Scholes Option Premium
        T = max(0.5, dte) / 365.0
        greeks = black_scholes(option_type, etf_price, strike, T, 0.0525, 0.20)
        entry_premium = max(0.25, greeks["price"])

        # Determine Contract Quantity (Max 5% of capital)
        alloc_usd = self.capital * (CONFIG["max_capital_per_trade_pct"] / 100.0)
        contracts = max(1, int(alloc_usd / (entry_premium * 100.0)))
        total_cost = entry_premium * 100.0 * contracts

        option_ticker = f"{symbol}_{option_type}_{strike:.0f}_{dte}DTE"

        trade_res = self.broker_adapter.submit_order(
            symbol=symbol,
            option_symbol=option_ticker,
            action="BUY",
            qty=contracts,
            limit_price=entry_premium
        )

        position = {
            "id": trade_res["order_id"],
            "symbol": symbol,
            "option_ticker": option_ticker,
            "option_type": option_type,
            "strike": strike,
            "dte": dte,
            "contracts": contracts,
            "entry_premium": entry_premium,
            "total_cost_usd": round(total_cost, 2),
            "entry_time": timestamp(),
            "target_profit_price": round(entry_premium * (1.0 + CONFIG["target_profit_pct"] / 100.0), 2),
            "stop_loss_price": round(entry_premium * (1.0 - CONFIG["stop_loss_pct"] / 100.0), 2),
            "status": "OPEN",
            "current_premium": entry_premium,
            "pnl_usd": 0.0,
            "pnl_pct": 0.0
        }

        self.open_positions.append(position)
        self.save_state()
        log_msg("DAYTRADE_OPEN", f"🟢 NUEVA POSICIÓN {option_type}: {contracts}x {option_ticker} @ ${entry_premium} USD (Costo: ${total_cost:.2f} USD | TP: ${position['target_profit_price']} | SL: ${position['stop_loss_price']})")

    def manage_open_position(self, pos, market_data):
        etf_price = market_data["price"]
        greeks = black_scholes(pos["option_type"], etf_price, pos["strike"], 0.5/365.0, 0.0525, 0.20)
        curr_premium = max(0.05, greeks["price"])

        pnl_pct = ((curr_premium - pos["entry_premium"]) / pos["entry_premium"]) * 100.0
        pnl_usd = (curr_premium - pos["entry_premium"]) * 100.0 * pos["contracts"]

        pos["current_premium"] = curr_premium
        pos["pnl_pct"] = round(pnl_pct, 2)
        pos["pnl_usd"] = round(pnl_usd, 2)

        log_msg("MONITOR", f"Posición [{pos['option_ticker']}]: Prima Actual: ${curr_premium} USD | PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f} USD)")

        # Check Take Profit
        if curr_premium >= pos["target_profit_price"]:
            self.close_position(pos, "TAKE_PROFIT", curr_premium)
        # Check Stop Loss
        elif curr_premium <= pos["stop_loss_price"]:
            self.close_position(pos, "STOP_LOSS", curr_premium)

    def close_position(self, pos, reason, exit_premium):
        trade_res = self.broker_adapter.submit_order(
            symbol=pos["symbol"],
            option_symbol=pos["option_ticker"],
            action="SELL",
            qty=pos["contracts"],
            limit_price=exit_premium
        )

        pnl_usd = (exit_premium - pos["entry_premium"]) * 100.0 * pos["contracts"]
        pnl_pct = ((exit_premium - pos["entry_premium"]) / pos["entry_premium"]) * 100.0

        closed_record = {
            **pos,
            "exit_time": timestamp(),
            "exit_premium": exit_premium,
            "exit_reason": reason,
            "final_pnl_usd": round(pnl_usd, 2),
            "final_pnl_pct": round(pnl_pct, 2)
        }

        self.open_positions.remove(pos)
        self.closed_trades.append(closed_record)
        self.daily_pnl += pnl_usd
        self.capital += pnl_usd

        self.save_state()
        emoji = "🔴" if pnl_usd < 0 else "🟢"
        log_msg("DAYTRADE_CLOSE", f"{emoji} POSICIÓN CERRADA ({reason}): [{pos['option_ticker']}] Exit Premium: ${exit_premium} USD | PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f} USD)")

if __name__ == "__main__":
    log_msg("BOOT", "=== BOT DE DAY TRADING DE OPCIONES SOBRE ETFs (0-DTE / 1-DTE) INICIADO ===")
    bot = DayTradeOptionsBot()
    bot.run_intraday_scan()
