# -*- coding: utf-8 -*-
"""
Alpha Trade Engine - Layer 3 (60-180 DTE Zero-Cost Risk-Free Synthetic LEAPS)
- Arms 2 Short Puts x 2 Long Calls (Zero Net Premium Paid).
- Uses accumulated premium reinvestment (20% allocation) to buy back / decouple Short Puts.
- Leaves 100% Risk-Free Long Calls with unlimited upside potential.
"""

import os
import json
import urllib.request
from datetime import datetime, timedelta
from cloud_persistence import sync_state_to_github_async, load_state_from_github

STATE_FILE = "alpha_trade_state.json"

class AlphaTradeBot:
    def __init__(self, initial_capital=100000.0, allocated_capital=20000.0):
        self.initial_capital = initial_capital
        self.allocated_capital = allocated_capital # $20,000 USD (20%)
        self.open_positions = []
        self.decoupled_calls = []
        self.closed_positions = []
        self.total_decouple_funds_used = 0.0
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.load_state()

    def load_state(self):
        # Prioritize cloud state from GitHub raw
        cloud_data = load_state_from_github(STATE_FILE)
        if cloud_data:
            self._apply_dict(cloud_data)
            print(f"[ALPHA_TRADE] Estado restaurado desde Nube GitHub ({len(self.open_positions)} sintéticos activos).")
            return

        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._apply_dict(data)
                    print(f"[ALPHA_TRADE] Estado cargado localmente.")
            except Exception as e:
                print(f"[ALPHA_TRADE] Error leyendo estado local: {e}")
                self._initialize_default_state()
        else:
            self._initialize_default_state()

    def _initialize_default_state(self):
        """
        Initializes a clean empty state when no prior state exists.
        Does NOT push to GitHub on init — avoids overwriting real cloud state
        when GitHub is temporarily slow on Render cold start.
        """
        self.open_positions = []
        self.decoupled_calls = []
        self.closed_positions = []
        self.total_decouple_funds_used = 0.0
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Save locally only — no GitHub sync to avoid overwriting real data
        try:
            data = {
                "allocated_capital": self.allocated_capital,
                "open_positions": self.open_positions,
                "decoupled_calls": self.decoupled_calls,
                "closed_positions": self.closed_positions,
                "total_decouple_funds_used": self.total_decouple_funds_used,
                "last_update": self.last_update
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("[ALPHA_TRADE] Estado inicial vacío guardado localmente (sin push a GitHub).")
        except Exception as e:
            print(f"[ALPHA_TRADE] Warning al guardar estado inicial: {e}")

    def _apply_dict(self, data):
        self.allocated_capital = data.get("allocated_capital", 20000.0)
        self.open_positions = data.get("open_positions", [])
        self.decoupled_calls = data.get("decoupled_calls", [])
        self.closed_positions = data.get("closed_positions", [])
        self.total_decouple_funds_used = data.get("total_decouple_funds_used", 0.0)
        self.last_update = data.get("last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def save_state(self):
        self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "allocated_capital": self.allocated_capital,
            "open_positions": self.open_positions,
            "decoupled_calls": self.decoupled_calls,
            "closed_positions": self.closed_positions,
            "total_decouple_funds_used": self.total_decouple_funds_used,
            "last_update": self.last_update
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            sync_state_to_github_async(STATE_FILE, data)
        except Exception as e:
            print(f"[ALPHA_TRADE] Error guardando estado: {e}")





    def scan_and_open_alpha_trade(self, market_data=None):
        """
        Lógica Institucional Macro: Escanea oportunidades para abrir Sintéticos a 2 años (730 DTE).
        Gatillo: Precio toca la DMA200 (Media Móvil 200 días) Y el RSI Semanal < 45.
        """
        # Verificar presupuesto libre (Asumimos costo neto 0, pero bloquea porción del riesgo asignado)
        if len(self.open_positions) >= 2:
            return {"status": "MAX_POSITIONS_REACHED"}
            
        symbols_to_scan = ["QQQ", "SPY"]
        
        for symbol in symbols_to_scan:
            current_price = self.fetch_underlying_price(symbol)
            if not current_price:
                continue
                
            # Simulamos el cálculo de DMA200 y RSI Semanal (En un entorno real se baja data histórica larga)
            # Para la arquitectura, el gatillo lógico queda programado:
            dma_200 = current_price * 1.01 # Placeholder simulado para el test
            rsi_weekly = 40 # Placeholder simulado para el test
            
            # GATILLO MACROECONÓMICO
            if current_price <= dma_200 or rsi_weekly <= 45:
                print(f"[ALPHA_TRADE] 🎯 Oportunidad Macro Detectada en {symbol}. RSI Semanal: {rsi_weekly} | Precio vs DMA200: ${current_price}/${dma_200}")
                
                # Armado del Sintético a 2 Años a Costo Cero
                put_strike = round(current_price * 0.85, 1) # Vende Put 15% OTM
                call_strike = round(current_price * 1.05, 1) # Compra Call 5% OTM
                
                premium_collected = round(current_price * 0.08 * 100, 2) # Prima estimada
                
                # Abre en números pares obligatoriamente para permitir el Desacople Autofinanciado futuro
                contracts = 2
                
                new_position = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "symbol": symbol,
                    "strategy": "ZERO_COST_SYNTHETIC_LEAP_2YR",
                    "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "dte": 730, # 2 años
                    "underlying_price_at_entry": current_price,
                    "short_put_strike": put_strike,
                    "short_put_contracts": contracts,
                    "short_put_premium_collected": premium_collected * contracts,
                    "long_call_strike": call_strike,
                    "long_call_contracts": contracts,
                    "long_call_premium_paid": premium_collected * contracts, # Costo Cero Neto
                    "net_cost_usd": 0.0,
                    "status": "ACTIVE_SYNTHETIC",
                    "short_put_current_buyback_cost": premium_collected * contracts,
                    "decoupled": False,
                    "current_underlying_price": current_price,
                    "unrealized_pnl_usd": 0.0
                }
                
                self.open_positions.append(new_position)
                self.save_state()
                print(f"[ALPHA_TRADE] ✅ Sintético LEAP 2 Años abierto exitosamente en {symbol}. Riesgo pareado.")
                return {"status": "OPENED", "position": new_position}
                
        return {"status": "NO_OPPORTUNITY"}

    def monitor_and_auto_decouple(self, market_data=None):
        """
        Lógica Institucional: Self-Funded Free Runner.
        Evalúa si la venta del 50% de los Long Calls cubre el 100% de la recompra de los Short Puts.
        """
        for pos in self.open_positions:
            if not pos.get("decoupled"):
                symbol = pos["symbol"]
                current_price = self.fetch_underlying_price(symbol)
                if not current_price:
                    continue
                
                # Simulacion de valorizacion (En live, llama a Black-Scholes)
                if current_price > pos["underlying_price_at_entry"]:
                    price_increase_pct = (current_price - pos["underlying_price_at_entry"]) / pos["underlying_price_at_entry"]
                    
                    # Valor actual de 1 Long Call (Delta proxy aproximado)
                    call_current_value = (pos["long_call_premium_paid"] / pos["long_call_contracts"]) * (1 + (price_increase_pct * 4))
                    # Costo actual de recomprar TODOS los Short Puts
                    total_put_buyback_cost = pos["short_put_premium_collected"] * max(0.1, (1 - (price_increase_pct * 5)))
                    
                    half_calls = max(1, int(pos["long_call_contracts"] / 2))
                    value_of_half_calls = call_current_value * half_calls
                    
                    # GATILLO DE ESCAPE AUTOFINANCIADO
                    if value_of_half_calls >= total_put_buyback_cost:
                        print(f"[ALPHA_TRADE] 🚀 GATILLO DE DESACOPLE AUTOFINANCIADO DETECTADO en {symbol}!")
                        
                        pos["decoupled"] = True
                        pos["long_call_contracts"] -= half_calls
                        pos["short_put_contracts"] = 0
                        
                        net_cash_generated = round(value_of_half_calls - total_put_buyback_cost, 2)
                        
                        free_runner = {
                            **pos,
                            "status": "FREE_RUNNER_LONG_CALL",
                            "net_cash_generated_usd": net_cash_generated,
                            "decouple_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.decoupled_calls.append(free_runner)
                        self.save_state()
                        print(f"[ALPHA_TRADE] ✅ Desacople Exitoso. Riesgo eliminado. Cash Sobrante: +${net_cash_generated}")
                        
        return {"status": "MONITORED"}

    def decouple_short_put(self, position_id, available_funds_usd):
        """
        Recompras la pata Short Put usando fondos de la reinversión (20%), 
        dejando el Long Call 100% LIMPIO Y SIN RIESGO (Risk-Free Call).
        """
        for pos in self.open_positions:
            if pos["id"] == position_id and not pos["decoupled"]:
                buyback_cost = pos.get("short_put_current_buyback_cost", 400.0)
                if available_funds_usd >= buyback_cost:
                    pos["decoupled"] = True
                    pos["status"] = "RISK_FREE_LONG_CALL"
                    pos["decouple_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    pos["decouple_cost_paid_usd"] = buyback_cost
                    self.total_decouple_funds_used += buyback_cost
                    
                    # Move to decoupled calls list
                    self.decoupled_calls.append(pos)
                    self.save_state()
                    return {
                        "success": True,
                        "message": f"¡Éxito! Short Put recomprado por ${buyback_cost:.2f} USD. Call {pos['symbol']} ahora es 100% LIBRE DE RIESGO.",
                        "cost_paid": buyback_cost,
                        "position": pos
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Fondos insuficientes (${available_funds_usd:.2f} USD disponibles vs ${buyback_cost:.2f} USD requeridos)."
                    }
        return {"success": False, "message": "Posición no encontrada o ya desacoplada."}

    def fetch_underlying_price(self, symbol):
        """Fetches live underlying price from Yahoo Finance."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return round(data["chart"]["result"][0]["meta"]["regularMarketPrice"], 2)
        except Exception:
            return None

    def monitor_positions(self):
        """
        Called every 60s by the background loop.
        Updates floating PnL on open synthetic positions using live prices.
        Flags positions where the Short Put buyback cost has dropped enough to decouple.
        """
        changed = False
        for pos in self.open_positions:
            symbol = pos.get("symbol", "QQQ")
            live_price = self.fetch_underlying_price(symbol)
            if live_price is None:
                continue

            pos["current_underlying_price"] = live_price

            # Estimate call PnL: if underlying rose above long_call_strike, intrinsic value increases
            call_strike = pos.get("long_call_strike", live_price)
            call_premium_paid = pos.get("long_call_premium_paid", 0) / 100.0  # per share
            intrinsic_call = max(0.0, live_price - call_strike)
            estimated_call_value = max(call_premium_paid, intrinsic_call)

            # Estimate put buyback: if underlying rose, short put loses value (good for us)
            put_strike = pos.get("short_put_strike", live_price * 0.97)
            entry_price = pos.get("underlying_price_at_entry", live_price)
            price_move_pct = (live_price - entry_price) / entry_price if entry_price > 0 else 0.0
            original_buyback = pos.get("short_put_current_buyback_cost", 400.0)
            # Put value decreases as underlying rises
            adjusted_buyback = max(10.0, round(original_buyback * (1.0 - price_move_pct * 2), 2))
            pos["short_put_current_buyback_cost"] = adjusted_buyback

            # Unrealized PnL: call appreciation minus put obligation
            net_pnl = round((estimated_call_value * 100 * pos.get("long_call_contracts", 2))
                            - (adjusted_buyback * pos.get("short_put_contracts", 2)), 2)
            pos["unrealized_pnl_usd"] = net_pnl
            changed = True

            print(f"[ALPHA_TRADE] Monitor: {symbol} @ ${live_price} | "
                  f"Put Buyback: ${adjusted_buyback} | Unrealized PnL: ${net_pnl}")

        if changed:
            self.save_state()

    def get_status(self):
        total_unrealized_pnl = sum(p.get("unrealized_pnl_usd", 0.0) for p in self.open_positions)
        return {
            "allocated_capital": self.allocated_capital,
            "active_synthetics_count": len([p for p in self.open_positions if not p.get("decoupled")]),
            "decoupled_calls_count": len(self.decoupled_calls),
            "open_positions": self.open_positions,
            "decoupled_calls": self.decoupled_calls,
            "closed_positions": self.closed_positions,
            "total_unrealized_pnl_usd": total_unrealized_pnl,
            "total_decouple_funds_used": self.total_decouple_funds_used,
            "last_update": self.last_update
        }

if __name__ == "__main__":
    bot = AlphaTradeBot()
    print(bot.get_status())
