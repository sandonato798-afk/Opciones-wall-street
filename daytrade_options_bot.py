# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import os
import json
import urllib.request
from datetime import datetime, timedelta

STATE_FILE = "daytrade_state.json"
CONFIG = {"target_profit_pct": 50}

from cloud_persistence import sync_state_to_github_async, load_state_from_github
from market_calendar import is_trading_day, is_market_open

class DaytradeOptionsBot:
    def __init__(self, initial_capital=100000.0, allocated_capital=15000.0, ibkr_adapter=None):
        self.ibkr_adapter = ibkr_adapter
        self.allocated_capital = allocated_capital
        self.active_trades = []
        self.history = []
        self.load_state()

    def load_state(self):
        local_data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
            except Exception:
                pass

        cloud_data = load_state_from_github(STATE_FILE)
        source = local_data
        if cloud_data:
            cloud_hist = cloud_data.get("history", [])
            local_hist = local_data.get("history", [])
            if len(cloud_hist) >= len(local_hist):
                source = cloud_data

        if source:
            self.allocated_capital = source.get("allocated_capital", 15000.0)
            self.active_trades = source.get("active_trades", [])
            self.history = source.get("history", [])

    def save_state(self):
        data = {
            "allocated_capital": self.allocated_capital,
            "active_trades": self.active_trades,
            "history": self.history,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            sync_state_to_github_async(STATE_FILE, data)
        except Exception as e:
            print(f"[DAYTRADE] Error guardando estado: {e}")

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

    def _fetch_real_put_premium(self, symbol, target_strike):
        """Busca la prima real en la cadena de opciones o Black-Scholes."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            exps = ticker.options
            if exps:
                chain = ticker.option_chain(exps[0])
                puts = chain.puts
                if not puts.empty:
                    put_row = puts.iloc[(puts['strike'] - target_strike).abs().argsort()[:1]]
                    if not put_row.empty:
                        bid = put_row['bid'].values[0]
                        ask = put_row['ask'].values[0]
                        mid = (bid + ask) / 2.0
                        if mid <= 0.01:
                            mid = put_row['lastPrice'].values[0]
                        if mid > 0.01:
                            return round(mid, 2)
        except Exception:
            pass
            
        try:
            from options_engine import black_scholes
            mkt = self.fetch_market_data(symbol)
            cp = mkt["current_price"] if mkt else target_strike
            bs = black_scholes("PUT", cp, target_strike, 1.0 / 365.0, 0.0525, 0.18)
            return round(max(0.50, bs["price"]), 2)
        except Exception:
            return round(target_strike * 0.005, 2)

    def scan_market(self):
        # GUARD: No operar en fines de semana ni feriados NYSE
        if not is_trading_day() or not is_market_open():
            return
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
                premium = self._fetch_real_put_premium(symbol, strike)
                
                contracts = max(1, int(self.allocated_capital / (strike * 100 * 0.20))) # Margen
                income = round(premium * 100 * contracts, 2)
                cost_usd = round(strike * 100 * contracts * 0.20, 2)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_trade = {
                    "id": f"DAY_ITM_PUT_{int(datetime.now().timestamp())}",
                    "symbol": symbol,
                    "option_ticker": f"{symbol} PUT ${strike} 1-DTE",
                    "strategy": "ITM_PUT_1DTE",
                    "entry_price": cp,
                    "strike": strike,
                    "contracts": contracts,
                    "dte": 1,
                    "entry_premium": premium,
                    "premium_collected_usd": income,
                    "total_cost_usd": cost_usd,
                    "take_profit_target_usd": round(income * 0.50, 2),
                    "issued_date": now_str,
                    "entry_time": now_str,
                    "expiration_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "status": "ACTIVE",
                    "pnl_usd": 0.0
                }
                self.active_trades.append(new_trade)
                self.save_state()
                return

    def manage_open_position(self):
        # Usar list() para poder remover elementos sin afectar el loop
        for pos in list(self.active_trades):
            if pos["status"] == "ACTIVE":
                symbol = pos["symbol"]
                data = self.fetch_market_data(symbol)
                if not data:
                    continue
                
                cp = data["current_price"]
                
                # 1. Check 50% Take Profit usando orden de recompra abierta
                current_premium = self._fetch_real_put_premium(symbol, pos["strike"])
                current_put_value = round(current_premium * 100 * pos["contracts"], 2)
                initial_premium = pos["premium_collected_usd"]
                cost = pos.get("total_cost_usd", pos.get("strike", 500) * 100 * pos.get("contracts", 1) * 0.20)
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Si cuesta menos del 50% recomprarlo, cerramos ganando el resto (+50% TP)
                if current_put_value <= pos["take_profit_target_usd"]:
                    net_pnl = round(initial_premium - current_put_value, 2)
                    pos["status"] = "CLOSED_TAKE_PROFIT"
                    pos["realized_pnl_usd"] = net_pnl
                    pos["final_pnl_usd"] = net_pnl
                    pos["pnl_usd"] = net_pnl
                    pos["exit_premium"] = current_premium
                    pos["exit_time"] = now_str
                    pos["final_pnl_pct"] = round((net_pnl / cost) * 100, 2) if cost > 0 else 0.0
                    pos["roi_pct"] = pos["final_pnl_pct"]
                    self.history.append(pos)
                    self.active_trades.remove(pos)
                    self.save_state()
                    print(f"[DAYTRADE] ✅ Take Profit (50%) alcanzado en {symbol}. PnL: +${net_pnl} USD (Liberado a Colateral).")
                    continue
                    
                # 2. Protocolo de Fin de Ronda (D+1 a las 15:55 EST - Regla de Andrés Weisz)
                try:
                    exp_date = datetime.strptime(pos["expiration_date"], "%Y-%m-%d").date()
                except Exception:
                    exp_date = now.date()
                    
                is_exp_day = (now.date() >= exp_date)
                is_eod_window = is_exp_day and (now.hour > 15 or (now.hour == 15 and now.minute >= 55) or now.date() > exp_date)
                
                if is_eod_window:
                    # Estimar comisiones y costos del broker (~$1.30 USD por contrato round-trip)
                    broker_commission = 1.30 * pos.get("contracts", 1)
                    net_proceeds = round(initial_premium - current_put_value - broker_commission, 2)
                    
                    if net_proceeds > 0:
                        # CASO A (Con Beneficio Neto): Recomprar y cerrar en el acto
                        pos["status"] = "CLOSED_EOD_PROFIT"
                        pos["realized_pnl_usd"] = net_proceeds
                        pos["final_pnl_usd"] = net_proceeds
                        pos["pnl_usd"] = net_proceeds
                        pos["exit_premium"] = current_premium
                        pos["exit_time"] = now_str
                        pos["final_pnl_pct"] = round((net_proceeds / cost) * 100, 2) if cost > 0 else 0.0
                        pos["roi_pct"] = pos["final_pnl_pct"]
                        self.history.append(pos)
                        self.active_trades.remove(pos)
                        self.save_state()
                        print(f"[DAYTRADE] 🎯 Cierre EOD 15:55 con beneficio neto en {symbol}. PnL: +${net_proceeds} USD (Transferible a Colateral).")
                        continue
                    else:
                        # CASO B (Con Pérdida): ROLLEAR EL PUT A VENCIMIENTO POSTERIOR
                        # Regla Andrés: NO se asume la pérdida ni se compra colateral. Se rollea con crédito.
                        new_dte = 2 # Roleo a 2 DTE o siguiente sesión
                        new_strike = round(cp * 1.005, 1) # Strike adaptado a spot actual
                        roll_premium = self._fetch_real_put_premium(symbol, new_strike)
                        roll_credit_usd = round(roll_premium * 100 * pos["contracts"], 2)
                        
                        pos["rolled_count"] = pos.get("rolled_count", 0) + 1
                        pos["expiration_date"] = (now + timedelta(days=new_dte)).strftime("%Y-%m-%d")
                        pos["strike"] = new_strike
                        pos["premium_collected_usd"] = round(initial_premium + roll_credit_usd - current_put_value, 2)
                        pos["take_profit_target_usd"] = round(pos["premium_collected_usd"] * 0.50, 2)
                        pos["last_roll_time"] = now_str
                        pos["status"] = "ACTIVE" # Sigue abierta en defensa, NO liberada a colateral
                        self.save_state()
                        print(f"[DAYTRADE] 🛡️ 15:55 EST: Recompra generaba pérdida (-${abs(net_proceeds)} USD). "
                              f"ROLED EXITOSO en {symbol} a K=${new_strike} ({new_dte}DTE). Posición sigue en trading sin tocar colateral.")
                        continue
                
                # 3. Liquidación Matemática Intrínseca si se alcanza expiración absoluta (Fallback Offline)
                if now.date() > exp_date:
                    intrinsic_per_share = max(0.0, round(pos["strike"] - cp, 2))
                    total_intrinsic_loss = round(intrinsic_per_share * 100 * pos["contracts"], 2)
                    net_pnl = round(initial_premium - total_intrinsic_loss, 2)
                    
                    pos["status"] = "CLOSED_EXPIRED"
                    pos["realized_pnl_usd"] = net_pnl
                    pos["final_pnl_usd"] = net_pnl
                    pos["pnl_usd"] = net_pnl
                    pos["exit_premium"] = intrinsic_per_share
                    pos["exit_time"] = now_str
                    pos["final_pnl_pct"] = round((net_pnl / cost) * 100, 2) if cost > 0 else 0.0
                    pos["roi_pct"] = pos["final_pnl_pct"]
                    self.history.append(pos)
                    self.active_trades.remove(pos)
                    self.save_state()
                    print(f"[DAYTRADE] ⏳ Trade cerrado por expiración en {symbol}. PnL: ${net_pnl} USD")
                    continue
                
                # 4. Actualización de PnL Flotante Intradía mientras la posición esté activa
                pos["current_underlying_price"] = cp
                pos["current_put_value"] = current_put_value
                pos["pnl_usd"] = round(initial_premium - current_put_value, 2)
                self.save_state()

    def get_status(self):
        return {
            "allocated_capital": self.allocated_capital,
            "active_trades": self.active_trades,
            "open_positions": self.active_trades,
            "history": self.history,
            "closed_trades": self.history
        }

if __name__ == "__main__":
    bot = DaytradeOptionsBot()
    print(f"[DAYTRADE] Ejecutando escaneo intradiario de opciones...")
    bot.manage_open_position()
    bot.scan_market()
    print(f"[DAYTRADE] Escaneo finalizado. Trades activos: {len(bot.active_trades)}")
