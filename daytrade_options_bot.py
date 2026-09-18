import time
import json
import os
import math
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes
from cloud_persistence import sync_state_to_github_async, load_state_from_github

STATE_FILE = os.path.join(os.path.dirname(__file__), "daytrade_paper_state.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "daytrade_bot.log")

# Configuration
CONFIG = {
    "execution_mode": "PAPER_TRADING",      # "PAPER_TRADING" or "LIVE_BROKER"
    "broker_name": "INTERACTIVE_BROKERS",    # "INTERACTIVE_BROKERS", "ALPACA", "TRADIER"
    "initial_capital_usd": 100000.0,
    "max_simultaneous_trades": 4,           # Max 4 open intraday option positions
    "max_capital_per_trade_pct": 5.0,       # 5% ($5,000 USD) max allocation per trade
    "broker_fee_per_contract": 0.65,        # $0.65 USD fee per option contract (IBKR / E*Trade standard)
    "bid_ask_slippage_pct": 1.0,            # 1.0% bid-ask spread friction
    "max_daily_loss_usd": 3000.0,           # Daily drawdown limit circuit breaker (-3%)
    "target_profit_pct": 150.0,             # TP: +150% (Jonron Asimetrico)              # TP: +35% option premium gain
    "max_holding_time_minutes": 45,       # Salida por tiempo (Time-Stop) en vez de %                  # SL: -18% option premium loss
    "hard_eod_exit_time": "15:45",          # Close all positions at 15:45 EST
    "etf_watchlist": ["SPY", "QQQ"],
    "dte_target": 0                         # 0-DTE (Same day expiration)
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
            log_msg("BROKER", "Conectado a Motor de Paper Trading Intradiario (Fricción y Comisiones Reales $0.65/contrato).")
            return True
        else:
            log_msg("BROKER", f"Intentando conexión con {self.broker} API...")
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
        self.initial_capital = CONFIG["initial_capital_usd"]
        self.capital = self.initial_capital
        self.daily_pnl_usd = 0.0
        self.total_commissions_paid = 0.0
        self.system_start_time = timestamp()
        self.open_positions = []
        self.closed_trades = []
        self.symbol_cooldowns = {} # Symbol -> datetime until which trading is paused
        self.broker_adapter = BrokerAdapter(mode=CONFIG["execution_mode"], broker=CONFIG["broker_name"])
        self.broker_adapter.connect()
        self.load_state()

    def load_state(self):
        loaded = False
        # 1. Prioridad: Intentar cargar siempre desde GitHub Cloud
        gh_data = load_state_from_github("daytrade_paper_state.json")
        if gh_data and (gh_data.get("closed_trades") or gh_data.get("open_positions") or (gh_data.get("capital") and gh_data.get("capital") != CONFIG["initial_capital_usd"])):
            self.system_start_time = gh_data.get("system_start_time", timestamp())
            self.initial_capital = gh_data.get("initial_capital", CONFIG["initial_capital_usd"])
            self.capital = gh_data.get("capital", CONFIG["initial_capital_usd"])
            self.open_positions = gh_data.get("open_positions", [])
            self.closed_trades = gh_data.get("closed_trades", [])
            self.daily_pnl_usd = gh_data.get("daily_pnl_usd", 0.0)
            self.total_commissions_paid = gh_data.get("total_commissions_paid", 0.0)
            log_msg("CLOUD_STATE", "Estado recuperado exitosamente desde GitHub Cloud Backup.")
            loaded = True

        # 2. Si no hay estado en GitHub, intentar archivo local
        if not loaded and os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.system_start_time = data.get("system_start_time", timestamp())
                    self.initial_capital = data.get("initial_capital", CONFIG["initial_capital_usd"])
                    self.capital = data.get("capital", CONFIG["initial_capital_usd"])
                    self.open_positions = data.get("open_positions", [])
                    self.closed_trades = data.get("closed_trades", [])
                    self.daily_pnl_usd = data.get("daily_pnl_usd", 0.0)
                    self.total_commissions_paid = data.get("total_commissions_paid", 0.0)
                    log_msg("STATE", "Estado de Day Trading cargado correctamente desde archivo local.")
                    loaded = True
            except Exception as e:
                log_msg("WARN", f"Error cargando estado local ({e}).")

        if not loaded:
            self.save_state()

    def save_state(self):
        state = {
            "system_start_time": self.system_start_time,
            "last_update": timestamp(),
            "execution_mode": CONFIG["execution_mode"],
            "initial_capital": self.initial_capital,
            "capital": self.capital,
            "daily_pnl_usd": self.daily_pnl_usd,
            "daily_pnl_pct": round((self.daily_pnl_usd / self.initial_capital) * 100.0, 2),
            "total_pnl_usd": round(self.capital - self.initial_capital, 2),
            "total_pnl_pct": round(((self.capital - self.initial_capital) / self.initial_capital) * 100.0, 2),
            "total_commissions_paid": round(self.total_commissions_paid, 2),
            "open_positions": self.open_positions,
            "closed_trades": self.closed_trades
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        sync_state_to_github_async("daytrade_paper_state.json", state)

    def get_uptime_hours(self):
        try:
            start_dt = datetime.strptime(self.system_start_time, "%Y-%m-%d %H:%M:%S")
            diff = datetime.now() - start_dt
            hours = diff.total_seconds() / 3600.0
            return round(hours, 1)
        except Exception:
            return 0.0

    def get_win_rate_stats(self):
        total = len(self.closed_trades)
        if total == 0:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0}
        wins = sum(1 for t in self.closed_trades if t.get("final_pnl_usd", 0) > 0)
        losses = sum(1 for t in self.closed_trades if t.get("final_pnl_usd", 0) <= 0)
        rate = (wins / total) * 100.0
        return {"total": total, "wins": wins, "losses": losses, "win_rate": round(rate, 1)}

    def fetch_etf_intraday_data(self, symbol):
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
                
                ema9 = self.calculate_ema(prices, 9)
                ema21 = self.calculate_ema(prices, 21)
                rsi = self.calculate_rsi(prices, 14)
                
                # VWAP Calculation (Session Average Benchmark)
                vwap = sum(prices) / float(len(prices)) if prices else current_price
                ema_diff_pct = ((ema9 - ema21) / ema21) * 100.0 if ema21 > 0 else 0.0

                # High Probability Signal Filters:
                # 1. Bulls: EMA9 > EMA21 with clear separation (>0.03%), RSI > 56, Price ABOVE VWAP
                # 2. Bears: EMA9 < EMA21 with clear separation (<-0.03%), RSI < 44, Price BELOW VWAP
                signal = "NEUTRAL"
                if ema_diff_pct > 0.03 and rsi > 56.0 and current_price >= vwap:
                    signal = "BULLISH_CROSS"
                elif ema_diff_pct < -0.03 and rsi < 44.0 and current_price <= vwap:
                    signal = "BEARISH_CROSS"

                return {
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "change_pct": round(((current_price - prev_close) / prev_close) * 100, 2),
                    "ema9": round(ema9, 2),
                    "ema21": round(ema21, 2),
                    "vwap": round(vwap, 2),
                    "rsi": round(rsi, 1),
                    "signal": signal
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

    def run_intraday_scan(self):
        log_msg("SCAN", "--- ESCANEANDO SEÑALES DE DAY TRADING (0-DTE / 1-DTE ETFs) ---")
        
        # Check Daily Drawdown Circuit Breaker
        if self.daily_pnl_usd <= -CONFIG["max_daily_loss_usd"]:
            log_msg("CIRCUIT_BREAKER", f"Límite de pérdida diaria alcanzado (-${abs(self.daily_pnl_usd):.2f} USD). Pausando bot por hoy.")
            return

        now_dt = datetime.now()

        for symbol in CONFIG["etf_watchlist"]:
            # Check Cooldown Filter (10 min after a Stop Loss)
            cooldown_until = self.symbol_cooldowns.get(symbol)
            if cooldown_until and now_dt < cooldown_until:
                remaining_secs = int((cooldown_until - now_dt).total_seconds())
                log_msg("COOLDOWN", f"⏳ {symbol} en tiempo de enfriamiento post-StopLoss ({remaining_secs}s restantes). Evitando sobre-operativa.")
                continue

            market_data = self.fetch_etf_intraday_data(symbol)
            if not market_data:
                continue

            log_msg("DATA", f"{symbol}: ${market_data['price']} | VWAP: ${market_data['vwap']} | EMA9: ${market_data['ema9']} | EMA21: ${market_data['ema21']} | RSI: {market_data['rsi']} | Señal: {market_data['signal']}")

            # Check if position already open for this ETF
            existing = [p for p in self.open_positions if p["symbol"] == symbol]
            if existing:
                self.manage_open_position(existing[0], market_data)
                continue

            # Open new trade if below max simultaneous trades limit
            if len(self.open_positions) < CONFIG["max_simultaneous_trades"]:
                if market_data["signal"] == "BULLISH_CROSS" and market_data["rsi"] < 70:
                    self.open_intraday_option(symbol, "CALL", market_data)
                elif market_data["signal"] == "BEARISH_CROSS" and market_data["rsi"] > 30:
                    self.open_intraday_option(symbol, "PUT", market_data)

    def open_intraday_option(self, symbol, option_type, market_data):
        etf_price = market_data["price"]
        dte = CONFIG["dte_target"]
        
        strike_step = 1.0 if symbol != "SPY" and symbol != "QQQ" else 2.0
        if option_type == "CALL":
            strike = math.ceil(etf_price / strike_step) * strike_step
        else:
            strike = math.floor(etf_price / strike_step) * strike_step

        T = max(0.5, dte) / 365.0
        greeks = black_scholes(option_type, etf_price, strike, T, 0.0525, 0.20)
        base_premium = max(0.25, greeks["price"])
        
        # Apply 1.0% Bid-Ask Slippage Friction
        entry_premium = round(base_premium * (1.0 + CONFIG["bid_ask_slippage_pct"] / 100.0), 2)

        # Allocate 5% of Total Capital
        alloc_usd = self.capital * (CONFIG["max_capital_per_trade_pct"] / 100.0)
        contracts = max(1, int(alloc_usd / (entry_premium * 100.0)))
        
        # Calculate Broker Commission Fee ($0.65/contract)
        open_fee = contracts * CONFIG["broker_fee_per_contract"]
        total_cost = (entry_premium * 100.0 * contracts) + open_fee
        self.total_commissions_paid += open_fee

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
            "open_fee_usd": open_fee,
            "total_cost_usd": round(total_cost, 2),
            "entry_time": timestamp(),
            "target_profit_price": round(entry_premium * (1.0 + CONFIG["target_profit_pct"] / 100.0), 2),
            "stop_loss_price": 0.01, # Stop-Loss desactivado (Reemplazado por Time-Stop)
            "status": "OPEN",
            "current_premium": entry_premium,
            "pnl_usd": 0.0,
            "pnl_pct": 0.0,
            "trailing_stop_active": False
        }

        self.open_positions.append(position)
        self.save_state()
        log_msg("DAYTRADE_OPEN", f"🟢 NUEVA POSICIÓN {option_type}: {contracts}x {option_ticker} @ ${entry_premium} USD (Costo: ${total_cost:.2f} USD incl. ${open_fee:.2f} comisión | TP: ${position['target_profit_price']} | SL: ${position['stop_loss_price']})")

    def manage_open_position(self, pos, market_data):
        etf_price = market_data["price"]
        greeks = black_scholes(pos["option_type"], etf_price, pos["strike"], 0.5/365.0, 0.0525, 0.20)
        curr_premium = max(0.05, greeks["price"])

        raw_pnl_usd = (curr_premium - pos["entry_premium"]) * 100.0 * pos["contracts"]
        pnl_usd = raw_pnl_usd - pos["open_fee_usd"]
        pnl_pct = ((curr_premium - pos["entry_premium"]) / pos["entry_premium"]) * 100.0

        pos["current_premium"] = curr_premium
        pos["pnl_pct"] = round(pnl_pct, 2)
        pos["pnl_usd"] = round(pnl_usd, 2)

        # TRAILING STOP A BREAK-EVEN: Si la opción sube al +15%, mover SL al precio de entrada (+1%) para asegurar capital
        if pnl_pct >= 30.0 and not pos.get("trailing_stop_active", False):
            break_even_price = round(pos["entry_premium"] * 1.01, 2)
            pos["stop_loss_price"] = break_even_price
            pos["trailing_stop_active"] = True
            log_msg("TRAILING_STOP", f"🛡️ 🚀 Ganancia de +{pnl_pct:.1f}% alcanzada en [{pos['option_ticker']}]. Stop Loss subido a Break-Even (${break_even_price} USD) para blindar el capital.")

        log_msg("MONITOR", f"Posición [{pos['option_ticker']}]: Prima: ${curr_premium} USD | PnL Neto: {pnl_pct:+.2f}% (${pnl_usd:+.2f} USD) | SL: ${pos['stop_loss_price']}")

        # 1. Salida por Tiempo (Time-Stop 45 mins)
        entry_time_dt = datetime.strptime(pos["entry_time"], "%Y-%m-%d %H:%M:%S")
        elapsed_minutes = (datetime.now() - entry_time_dt).total_seconds() / 60.0
        
        if elapsed_minutes >= CONFIG.get("max_holding_time_minutes", 45):
            log_msg("TIME_STOP", f"⏳ Límite de 45 mins alcanzado para [{pos['option_ticker']}]. Forzando salida.")
            self.close_position(pos, "TIME_STOP_45M", curr_premium)
            return

        # 2. Salida por Jonrón (Take-Profit +150%)
        if curr_premium >= pos["target_profit_price"]:
            self.close_position(pos, "TAKE_PROFIT_HOMERUN", curr_premium)
            return
            
        # 3. Trailing Stop (Break-Even)
        if pos.get("trailing_stop_active") and curr_premium <= pos.get("stop_loss_price", 0):
            self.close_position(pos, "TRAILING_BREAK_EVEN", curr_premium)
            return

    def close_position(self, pos, reason, exit_premium):
        close_fee = pos["contracts"] * CONFIG["broker_fee_per_contract"]
        self.total_commissions_paid += close_fee

        trade_res = self.broker_adapter.submit_order(
            symbol=pos["symbol"],
            option_symbol=pos["option_ticker"],
            action="SELL",
            qty=pos["contracts"],
            limit_price=exit_premium
        )

        raw_pnl_usd = (exit_premium - pos["entry_premium"]) * 100.0 * pos["contracts"]
        final_pnl_usd = raw_pnl_usd - pos["open_fee_usd"] - close_fee
        pnl_pct = ((exit_premium - pos["entry_premium"]) / pos["entry_premium"]) * 100.0

        closed_record = {
            **pos,
            "exit_time": timestamp(),
            "exit_premium": exit_premium,
            "exit_reason": reason,
            "close_fee_usd": close_fee,
            "total_fees_usd": pos["open_fee_usd"] + close_fee,
            "final_pnl_usd": round(final_pnl_usd, 2),
            "final_pnl_pct": round(pnl_pct, 2)
        }

        self.open_positions.remove(pos)
        self.closed_trades.append(closed_record)
        self.daily_pnl_usd += final_pnl_usd
        self.capital += final_pnl_usd

        # Activar Cooldown de 10 minutos si fue Stop Loss para no sobre-operar
        if reason == "STOP_LOSS":
            self.symbol_cooldowns[pos["symbol"]] = datetime.now() + timedelta(minutes=10)
            log_msg("COOLDOWN", f"🛑 Stop Loss registrado en {pos['symbol']}. Cooldown activado por 10 minutos.")

        self.save_state()
        emoji = "🔴" if final_pnl_usd < 0 else "🟢"
        log_msg("DAYTRADE_CLOSE", f"{emoji} POSICIÓN CERRADA ({reason}): [{pos['option_ticker']}] Exit Premium: ${exit_premium} USD | PnL Neto: {pnl_pct:+.2f}% (${final_pnl_usd:+.2f} USD desdeduciendo ${closed_record['total_fees_usd']:.2f} comisiones)")

if __name__ == "__main__":
    log_msg("BOOT", "=== BOT DE DAY TRADING DE OPCIONES SOBRE ETFs (0-DTE / 1-DTE) INICIADO ===")
    bot = DayTradeOptionsBot()
    bot.run_intraday_scan()
