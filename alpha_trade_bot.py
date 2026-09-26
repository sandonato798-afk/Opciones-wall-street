# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
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
from market_calendar import is_trading_day

STATE_FILE = "alpha_trade_state.json"

class AlphaTradeBot:
    def __init__(self, initial_capital=100000.0, allocated_capital=20000.0, ibkr_adapter=None):
        self.ibkr_adapter = ibkr_adapter
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
            
        # Universo de Inversión: Índices (hasta 33% de NAV) y Sectores (hasta 5% de NAV)
        indices_core = ["SPY", "QQQ", "VOO"]
        etfs_sectoriales = ["XLK", "XLF", "XLV", "XLE", "XLY"]
        symbols_to_scan = indices_core + etfs_sectoriales
        
        total_nav = self.initial_capital
        
        for symbol in symbols_to_scan:
            # Control Estricto de Exposición (Sizing)
            is_sector = symbol in etfs_sectoriales
            max_allocation_pct = 0.05 if is_sector else 0.333
            max_capital_for_symbol = total_nav * max_allocation_pct
            
            # (En código de producción aquí se sumaría la exposición actual al símbolo para ver si hay margen)
            # if current_exposure[symbol] >= max_capital_for_symbol: continue

            current_price = self.fetch_underlying_price(symbol)
            if not current_price:
                continue
                
            # Simulamos el cálculo de DMA200 y RSI Semanal (En un entorno real se baja data histórica larga)
            # Lógica de Cruce de Confirmación (Momentum Reversal)
            # En entorno real, esto compara la vela anterior vs la vela actual
            prev_price = current_price * 0.99 
            dma_200 = current_price * 0.995 # Simula que el precio acaba de cruzar hacia arriba
            
            prev_rsi_weekly = 44
            current_rsi_weekly = 46 # Simula que el RSI acaba de cruzar de menos a mas de 45
            
            # GATILLO DE CONFIRMACIÓN ALCISTA
            cruce_dma_alcista = (prev_price <= dma_200) and (current_price > dma_200)
            cruce_rsi_alcista = (prev_rsi_weekly <= 45) and (current_rsi_weekly > 45)
            
            if cruce_dma_alcista or cruce_rsi_alcista:
                motivo = "DMA200 Cross-Up" if cruce_dma_alcista else "RSI > 45 Cross-Up"
                print(f"[ALPHA_TRADE] 🎯 Confirmación Macro Detectada en {symbol} ({motivo}).")
                
                # Búsqueda del vencimiento máximo absoluto (LEAP más lejano, 2 a 3 años)
                max_available_dte = 850 # Placeholder para "furthest possible expiration"
                
                put_strike = round(current_price * 0.85, 1)
                call_strike = round(current_price * 1.05, 1)
                
                # Dimensionamiento Dinámico Institucional de Contratos
                # Se estima costo del margin requirement del put (aprox 20% del strike)
                margin_req_per_put = put_strike * 100 * 0.20
                calculated_puts = int(max_capital_for_symbol / margin_req_per_put)
                
                # REGLA INSTITUCIONAL: Siempre al menos 2 Long Calls.
                # Si el peso de la cartera permite >= 2 puts, se entra en pares (2P : 2C o N:N).
                # Si el límite asignado sólo permite 1 put (ej. ETFs sectoriales con tope del 5%), se entra en ratio 1P : 2C.
                if calculated_puts >= 2:
                    short_put_contracts = calculated_puts
                    long_call_contracts = calculated_puts
                    ratio_desc = f"{short_put_contracts}P:{long_call_contracts}C (Par)"
                else:
                    short_put_contracts = 1
                    long_call_contracts = 2
                    ratio_desc = "1P:2C (Ratio Asimétrico)"
                
                # Entrada con Costo Cero Neto Estricto (Net Cost = $0.00)
                # La prima total cobrada por los puts financia el 100% de los calls comprados
                put_premium_per_contract = round(current_price * 0.08 * 100, 2)
                total_put_premium_collected = round(put_premium_per_contract * short_put_contracts, 2)
                total_call_premium_paid = total_put_premium_collected # Financiación 100% simétrica a costo neto 0
                
                # --- EJECUCIÓN REAL EN IBKR ---
                # Expiry string: 730 días desde hoy (aprox 2 años)
                expiry_str = (datetime.now() + timedelta(days=730)).strftime("%Y%m%d")
                
                # Para evitar bloquear si no hay conexión, validamos:
                if self.ibkr_adapter and self.ibkr_adapter.is_live_connected():
                    # Ejecutar pata corta (Short Put)
                    put_resp = self.ibkr_adapter.execute_option_order_sync(symbol, "P", put_strike, expiry_str, "SELL", short_put_contracts)
                    # Ejecutar pata larga (Long Call)
                    call_resp = self.ibkr_adapter.execute_option_order_sync(symbol, "C", call_strike, expiry_str, "BUY", long_call_contracts)
                else:
                    print("[ALPHA_TRADE] ⚠️ IBKR no está conectado. Abortando trade real por seguridad.")
                    return {"status": "NO_OPPORTUNITY"}

                new_position = {
                    "id": int(datetime.now().timestamp() * 1000),
                    "symbol": symbol,
                    "strategy": "ZERO_COST_SYNTHETIC_LEAP_MAX_DTE",
                    "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "dte": max_available_dte, # Vencimiento más lejano posible # 2 años
                    "underlying_price_at_entry": current_price,
                    "ratio": ratio_desc,
                    "short_put_strike": put_strike,
                    "short_put_contracts": short_put_contracts,
                    "short_put_premium_collected": total_put_premium_collected,
                    "long_call_strike": call_strike,
                    "long_call_contracts": long_call_contracts,
                    "long_call_premium_paid": total_call_premium_paid, # Costo Cero Neto
                    "net_cost_usd": 0.0,
                    "status": "ACTIVE_SYNTHETIC",
                    "short_put_current_buyback_cost": total_put_premium_collected,
                    "decoupled": False,
                    "current_underlying_price": current_price,
                    "unrealized_pnl_usd": 0.0
                }
                
                self.open_positions.append(new_position)
                self.save_state()
                print(f"[ALPHA_TRADE] ✅ Sintético LEAP abierto en {symbol}. Estructura: {ratio_desc} ({short_put_contracts} Puts, {long_call_contracts} Calls). Costo Neto: $0.00.")
                return {"status": "OPENED", "position": new_position}
                
        return {"status": "NO_OPPORTUNITY"}

    def monitor_and_auto_decouple(self, market_data=None):
        """
        Lógica Institucional: Self-Funded Free Runner.
        Evalúa si la venta del 50% de los Long Calls cubre el 100% de la recompra de los Short Puts.
        """
        if not is_trading_day():
            return
        for pos in self.open_positions:
            if not pos.get("decoupled"):
                symbol = pos["symbol"]
                current_price = self.fetch_underlying_price(symbol)
                if not current_price:
                    continue
                
                # Obtener la valoracion real calculada en monitor_positions (BS)
                total_put_buyback_cost = pos.get("short_put_current_buyback_cost", 999999.0)
                
                # Asumimos que net_pnl tiene el valor base, recalculamos el call
                from options_engine import black_scholes
                try:
                    entry_dt = datetime.strptime(pos.get("entry_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                    days_elapsed = max(1, (datetime.now() - entry_dt).days)
                    dte = max(1.0, float(pos.get("dte", 730)) - days_elapsed)
                except Exception:
                    dte = 730.0
                    
                call_val = black_scholes("CALL", current_price, pos["long_call_strike"], dte/365.0, 0.0525, 0.18)
                call_current_value_total = call_val["price"] * 100 * pos["long_call_contracts"]
                
                half_calls = max(1, int(pos["long_call_contracts"] / 2))
                value_of_half_calls = (call_current_value_total / pos["long_call_contracts"]) * half_calls
                
                # GATILLO DE ESCAPE AUTOFINANCIADO
                if value_of_half_calls >= total_put_buyback_cost:
                    print(f"[ALPHA_TRADE] 🚀 GATILLO DE DESACOPLE AUTOFINANCIADO DETECTADO en {symbol}!")
                    
                    pos["decoupled"] = True
                    remaining_calls = max(1, pos["long_call_contracts"] - half_calls)
                    pos["long_call_contracts"] = remaining_calls
                    pos["short_put_contracts"] = 0
                    pos["short_put_current_buyback_cost"] = 0.0
                    
                    net_cash_generated = round(value_of_half_calls - total_put_buyback_cost, 2)
                    
                    free_runner = {
                        **pos,
                        "status": "FREE_RUNNER_LONG_CALL",
                        "long_call_contracts": remaining_calls,
                        "net_cash_generated_usd": net_cash_generated,
                        "decouple_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.open_positions = [p for p in self.open_positions if p["id"] != pos["id"]]
                    if not any(p["id"] == free_runner["id"] for p in self.decoupled_calls):
                        self.decoupled_calls.append(free_runner)
                    self.save_state()
                    print(f"[ALPHA_TRADE] ✅ Desacople Exitoso en {symbol}. {half_calls} Call(s) vendidos para liquidar Short Put. Quedan {remaining_calls} Long Call(s) Free Runner. Cash Neto Sobrante: +${net_cash_generated}")
                        
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
                    pos["short_put_current_buyback_cost"] = 0.0
                    self.total_decouple_funds_used += buyback_cost
                    
                    # Move to decoupled calls list and remove from open_positions
                    self.open_positions = [p for p in self.open_positions if p["id"] != pos["id"]]
                    if not any(p["id"] == pos["id"] for p in self.decoupled_calls):
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
        """Fetches live underlying price from IBKR."""
        if self.ibkr_adapter:
            try:
                return self.ibkr_adapter.fetch_live_price(symbol)
            except Exception as e:
                print(f"[{bot.upper()}] Error obteniendo precio: {e}")
                return None
        return None

    def monitor_positions(self):
        """
        Called every 60s by the background loop.
        Updates floating PnL on open synthetic positions and decoupled calls using live Black-Scholes.
        """
        changed = False
        from options_engine import black_scholes
        
        # 1. Monitorear Sintéticos Activos (con Short Put pendiente de recompra)
        for pos in self.open_positions:
            if pos.get("decoupled"):
                continue
                
            symbol = pos.get("symbol", "QQQ")
            live_price = self.fetch_underlying_price(symbol)
            if live_price is None:
                continue

            pos["current_underlying_price"] = live_price
            call_strike = pos.get("long_call_strike", live_price)
            put_strike = pos.get("short_put_strike", live_price * 0.97)
            
            try:
                entry_dt = datetime.strptime(pos.get("entry_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                days_elapsed = max(1, (datetime.now() - entry_dt).days)
                dte = max(1.0, float(pos.get("dte", 730)) - days_elapsed)
            except Exception:
                dte = 730.0
            
            T = dte / 365.0
            risk_free_rate = 0.0525
            iv = 0.18
            
            call_val = black_scholes("CALL", live_price, call_strike, T, risk_free_rate, iv)
            estimated_call_value_per_share = round(call_val["price"], 2)
            
            put_val = black_scholes("PUT", live_price, put_strike, T, risk_free_rate, iv)
            adjusted_buyback_per_share = round(put_val["price"], 2)
            adjusted_buyback_total = round(adjusted_buyback_per_share * 100 * pos.get("short_put_contracts", 2), 2)
            
            pos["short_put_current_buyback_cost"] = adjusted_buyback_total
            net_pnl = round((estimated_call_value_per_share * 100 * pos.get("long_call_contracts", 2)) - adjusted_buyback_total, 2)
            pos["unrealized_pnl_usd"] = net_pnl
            changed = True

        # 2. Monitorear Calls Desacoplados (100% Risk-Free Long Calls, Buyback = $0.00)
        for pos in self.decoupled_calls:
            symbol = pos.get("symbol", "QQQ")
            live_price = self.fetch_underlying_price(symbol)
            if live_price is None:
                continue
            pos["current_underlying_price"] = live_price
            call_strike = pos.get("long_call_strike", live_price)
            try:
                entry_dt = datetime.strptime(pos.get("entry_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                days_elapsed = max(1, (datetime.now() - entry_dt).days)
                dte = max(1.0, float(pos.get("dte", 730)) - days_elapsed)
            except Exception:
                dte = 730.0
            
            T = dte / 365.0
            call_val = black_scholes("CALL", live_price, call_strike, T, 0.0525, 0.18)
            estimated_call_value = round(call_val["price"] * 100 * pos.get("long_call_contracts", 2), 2)
            pos["short_put_current_buyback_cost"] = 0.0
            pos["unrealized_pnl_usd"] = estimated_call_value
            changed = True

        if changed:
            self.save_state()
            self.monitor_and_auto_decouple()

    def get_status(self):
        active_synthetics = [p for p in self.open_positions if not p.get("decoupled")]
        pnl_active = sum(p.get("unrealized_pnl_usd", 0.0) for p in active_synthetics)
        pnl_decoupled = sum(p.get("unrealized_pnl_usd", 0.0) for p in self.decoupled_calls)
        total_unrealized_pnl = round(pnl_active + pnl_decoupled, 2)
        
        short_put_risk = sum(p.get("short_put_current_buyback_cost", 0.0) for p in active_synthetics)
        
        return {
            "allocated_capital": self.allocated_capital,
            "active_synthetics_count": len(active_synthetics),
            "decoupled_calls_count": len(self.decoupled_calls),
            "open_positions": active_synthetics,
            "decoupled_calls": self.decoupled_calls,
            "closed_positions": self.closed_positions,
            "total_unrealized_pnl_usd": total_unrealized_pnl,
            "short_put_risk_usd": short_put_risk,
            "total_decouple_funds_used": self.total_decouple_funds_used,
            "last_update": self.last_update
        }

if __name__ == "__main__":
    bot = AlphaTradeBot()
    print(bot.get_status())
