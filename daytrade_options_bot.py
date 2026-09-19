import json
import urllib.request
from datetime import datetime, timedelta

STATE_FILE = "daytrade_state.json"
CONFIG = {"target_profit_pct": 50}

class DaytradeOptionsBot:
    def __init__(self, initial_capital=100000.0, allocated_capital=15000.0):
        self.allocated_capital = allocated_capital
        self.active_trades = []
        self.history = []
        self.load_state()

    def load_state(self):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.active_trades = data.get("active_trades", [])
                self.history = data.get("history", [])
        except FileNotFoundError:
            pass

    def save_state(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "allocated_capital": self.allocated_capital,
                "active_trades": self.active_trades,
                "history": self.history,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)

    def fetch_market_data(self, symbol):
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
                if not prices or len(prices) < 15:
                    return None
                current_price = prices[-1]
                prev_close = meta.get("chartPreviousClose", current_price)

                gains, losses = 0.0, 0.0
                for i in range(1, 15):
                    diff = prices[-i] - prices[-i - 1]
                    if diff >= 0:
                        gains += diff
                    else:
                        losses -= diff
                rs = (gains / 14) / (losses / 14) if losses > 0 else 1.0
                rsi = 100.0 - (100.0 / (1.0 + rs)) if losses > 0 else 100.0

                prev_gains, prev_losses = 0.0, 0.0
                if len(prices) >= 16:
                    for i in range(2, 16):
                        diff = prices[-i] - prices[-i - 1]
                        if diff >= 0:
                            prev_gains += diff
                        else:
                            prev_losses -= diff
                    prev_rs = (prev_gains / 14) / (prev_losses / 14) if prev_losses > 0 else 1.0
                    prev_rsi = 100.0 - (100.0 / (1.0 + prev_rs)) if prev_losses > 0 else 100.0
                else:
                    prev_rsi = rsi

                return {
                    "current_price": round(current_price, 2),
                    "previous_close": round(prev_close, 2),
                    "rsi": round(rsi, 1),
                    "prev_rsi": round(prev_rsi, 1)
                }
        except Exception as e:
            print(f"[DAYTRADE] Error fetching market data for {symbol}: {e}")
            return None

    def scan_market(self):
        if len(self.active_trades) > 0: return # Solo 1 trade activo a la vez para no saturar margen
        
        for symbol in ["SPY", "QQQ"]:
            data = self.fetch_market_data(symbol)
            if not data:
                continue
            cp = data["current_price"]
            pc = data["previous_close"]
            
            # GATILLOS: Caída >= 1% desde cierre anterior O RSI cruza 30 hacia arriba
            drop_condition = cp <= (pc * 0.99)
            rsi_condition = (data["prev_rsi"] <= 30) and (data["rsi"] > 30)
            
            if drop_condition or rsi_condition:
                print(f"[DAYTRADE] 🎯 Gatillo activado en {symbol}. Drop: {drop_condition}, RSI Cross: {rsi_condition}")
                
                # Venta Put ITM a 1DTE
                strike = round(cp * 1.01, 1) # Strike + 1%
                premium = round(cp * 0.015, 2) # Prima estimada
                
                contracts = max(1, int(self.allocated_capital / (strike * 100 * 0.20))) # Margen
                income = premium * 100 * contracts
                
                new_trade = {
                    "id": f"DAY_ITM_PUT_{int(datetime.now().timestamp())}",
                    "symbol": symbol,
                    "strategy": "ITM_PUT_1DTE",
                    "entry_price": cp,
                    "strike": strike,
                    "contracts": contracts,
                    "premium_collected_usd": income,
                    "take_profit_target_usd": income * 0.50,
                    "issued_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "expiration_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "status": "ACTIVE"
                }
                self.active_trades.append(new_trade)
                self.save_state()
                return

    def manage_open_position(self):
        for pos in self.active_trades:
            if pos["status"] == "ACTIVE":
                data = self.fetch_market_data(pos["symbol"])
                cp = data["current_price"]
                
                # Check 50% Take Profit
                current_put_value = max(0, pos["strike"] - cp) * 100 * pos["contracts"] # Aproximacion intrinseca
                if current_put_value <= pos["take_profit_target_usd"]:
                    pos["status"] = "CLOSED_TAKE_PROFIT"
                    self.history.append(pos)
                    self.active_trades.remove(pos)
                    self.save_state()
                    print(f"[DAYTRADE] ✅ Take Profit 50% alcanzado en {pos['symbol']}.")
                    return
                    
                # Check Expiration & Roll Matrix (D+1, 5 mins to close -> simulated by date)
                exp_date = datetime.strptime(pos["expiration_date"], "%Y-%m-%d")
                if datetime.now() >= exp_date:
                    if current_put_value < pos["premium_collected_usd"]:
                        # Beneficio neto
                        pos["status"] = "CLOSED_NET_PROFIT"
                        self.history.append(pos)
                        self.active_trades.remove(pos)
                    else:
                        # Matriz de Roleo
                        pct_above = (pos["strike"] - cp) / cp
                        if pct_above <= 0.03:
                            pos["expiration_date"] = (exp_date + timedelta(days=2)).strftime("%Y-%m-%d")
                            print(f"[DAYTRADE] ⚠️ Roleo +2 Días aplicado en {pos['symbol']}.")
                        elif pct_above <= 0.06:
                            pos["expiration_date"] = (exp_date + timedelta(days=7)).strftime("%Y-%m-%d")
                            print(f"[DAYTRADE] ⚠️ Roleo +1 Semana aplicado en {pos['symbol']}.")
                        else:
                            pos["expiration_date"] = (exp_date + timedelta(days=14)).strftime("%Y-%m-%d") # Prox viernes 3ro
                            print(f"[DAYTRADE] ⚠️ Roleo al 3er Viernes aplicado en {pos['symbol']}.")
                    self.save_state()

    def get_status(self):
        return {"allocated_capital": self.allocated_capital, "active_trades": self.active_trades}
