# -*- coding: utf-8 -*-
"""
Alpha Trade Engine - Layer 3 (60-180 DTE Zero-Cost Risk-Free Synthetic LEAPS)
- Arms 2 Short Puts x 2 Long Calls (Zero Net Premium Paid).
- Uses accumulated premium reinvestment (20% allocation) to buy back / decouple Short Puts.
- Leaves 100% Risk-Free Long Calls with unlimited upside potential.
"""

import os
import json
import random
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
        # Create an initial demo Alpha Trade position on SPY if empty
        self.open_positions = [
            {
                "id": 178960001,
                "symbol": "QQQ",
                "strategy": "ZERO_COST_SYNTHETIC_LEAP",
                "entry_date": (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d %H:%M:%S"),
                "dte": 120,
                "underlying_price_at_entry": 692.50,
                "short_put_strike": 670.0,
                "short_put_contracts": 2,
                "short_put_premium_collected": 1450.0,
                "long_call_strike": 715.0,
                "long_call_contracts": 2,
                "long_call_premium_paid": 1450.0,
                "net_cost_usd": 0.0,
                "status": "ACTIVE_SYNTHETIC",
                "short_put_current_buyback_cost": 420.0, # Reduced due to passage of time & market rise
                "decoupled": False,
                "current_underlying_price": 704.16,
                "unrealized_pnl_usd": 1280.0
            }
        ]
        self.save_state()

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
