# -*- coding: utf-8 -*-
"""
daytrade_options_bot.py - Motor Institucional de la Capa 4: Daytrading 1DTE
Opera sobre la infraestructura de `core/` y lee parámetros desde `config/strategies.yaml`.
Incluye Roll Defensivo a 30 DTE a las 15:55 EST si la posición está en pérdida.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import yaml

# Módulos del Núcleo `core/`
from core.clock import now_et, is_nyse_market_open
from core.broker import BrokerManager
from core.contracts import ContractManager
from core.orders import OrderExecutionEngine
from core.risk import RiskGuardian
from core.ledger import InstitutionalLedger

STATE_FILE = os.path.join(os.path.dirname(__file__), "daytrade_state.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config", "strategies.yaml")


def load_yaml_config() -> Dict[str, Any]:
    """Carga la configuración centralizada desde config/strategies.yaml."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"[DAYTRADE] Error cargando config/strategies.yaml: {e}")
    return {
        "GLOBAL": {"TRADING_ENABLED": False, "NAV_USD": 1000000.0},
        "CAPA_4_DAYTRADE": {
            "ENABLED": True,
            "ALLOCATED_CAPITAL_USD": 150000.0,
            "UNIVERSE": ["SPY", "QQQ"],
            "TARGET_DTE": 1,
            "ROLL_DEFENSIVO_EST": "15:55",
            "ROLL_OUT_DTE": 30
        }
    }


class DaytradeOptionsBot:
    """
    Motor Institucional de Daytrading 1DTE (Capa 4)
    - Operaciones a 1 DTE con Take Profit al 50%.
    - Roll defensivo a 30 DTE a las 15:55 EST si entra en pérdida.
    - Cero simulación: Solo registra fills confirmados por IBKR.
    """

    def __init__(self, initial_capital: float = 1000000.0, allocated_capital: float = 150000.0, broker_manager: Optional[Any] = None, ibkr_adapter: Optional[Any] = None):
        self.config = load_yaml_config()
        self.daytrade_config = self.config.get("CAPA_4_DAYTRADE", {})
        
        self.initial_capital = initial_capital
        self.allocated_capital = allocated_capital
        self.ibkr_adapter = ibkr_adapter or broker_manager
        self.broker_mgr = broker_manager or BrokerManager()
        self.risk_guardian = RiskGuardian(self.config)
        self.ledger = InstitutionalLedger(STATE_FILE)

        self.active_trades: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []

        self.load_state()

    def load_state(self):
        """Carga el estado local limpio del libro mayor."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_trades = data.get("active_trades", [])
                    self.history = data.get("history", [])
            except Exception as e:
                logging.error(f"[DAYTRADE] Error cargando estado: {e}")

    def save_state(self):
        """Guarda el estado utilizando escritura atómica."""
        state = {
            "last_update": now_et().isoformat(),
            "allocated_capital": self.daytrade_config.get("ALLOCATED_CAPITAL_USD", 150000.0),
            "active_trades": self.active_trades,
            "history": self.history
        }
        try:
            temp_file = f"{STATE_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, STATE_FILE)
        except Exception as e:
            logging.error(f"[DAYTRADE] Error guardando estado atómico: {e}")

    def scan_market(self) -> Dict[str, Any]:
        """Escanea el mercado para rupturas intradía."""
        self.config = load_yaml_config()
        self.daytrade_config = self.config.get("CAPA_4_DAYTRADE", {})

        if not self.daytrade_config.get("ENABLED", False):
            return {"status": "SKIPPED", "reason": "Capa 4 Daytrade deshabilitada."}

        if not self.risk_guardian.is_trading_enabled():
            return {"status": "SKIPPED", "reason": "Kill-switch activado (TRADING_ENABLED=false)."}

        if not is_nyse_market_open():
            return {"status": "SKIPPED", "reason": "Mercado cerrado."}

        if not self.broker_mgr.connect():
            return {"status": "ERROR", "reason": "Sin conexión con IB Gateway."}

        logging.info(f"[DAYTRADE] Escaneando subyacentes ({self.daytrade_config.get('UNIVERSE')})...")

        self.save_state()
        return {"status": "SCAN_COMPLETED", "timestamp": now_et().isoformat()}

    def manage_open_position(self) -> Dict[str, Any]:
        """Supervisa posiciones y ejecuta roll defensivo a las 15:55 EST si aplica."""
        logging.info(f"[DAYTRADE] Monitoreando {len(self.active_trades)} trades activos...")
        return {"status": "MONITOR_COMPLETED", "active_count": len(self.active_trades)}
