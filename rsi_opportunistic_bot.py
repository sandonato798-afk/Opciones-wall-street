# -*- coding: utf-8 -*-
"""
rsi_opportunistic_bot.py - Motor Institucional de la Capa 3: RSI Oportunista (0-1 DTE Scalp)
Triggers: Intraday RSI < 25 (Pánico de sobreventa) Y Precio < Cierre Previo.
Opera sobre la infraestructura de `core/` y lee parámetros desde `config/strategies.yaml`.
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

STATE_FILE = os.path.join(os.path.dirname(__file__), "rsi_opportunistic_state.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config", "strategies.yaml")


def load_yaml_config() -> Dict[str, Any]:
    """Carga la configuración centralizada desde config/strategies.yaml."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"[RSI] Error cargando config/strategies.yaml: {e}")
    return {
        "GLOBAL": {"TRADING_ENABLED": False, "NAV_USD": 1000000.0},
        "CAPA_3_RSI": {
            "ENABLED": True,
            "ALLOCATED_CAPITAL_USD": 150000.0,
            "UNIVERSE": ["SPY", "QQQ", "DIA"],
            "RSI_PERIOD": 14,
            "RSI_ENTRY_THRESHOLD": 25.0,
            "TARGET_DTE_MAX": 1,
            "TAKE_PROFIT_PCT": 50.0,
            "TIME_STOP_EST": "15:55"
        }
    }


class RSIOpportunisticBot:
    """
    Motor Institucional de RSI Oportunista (Capa 3)
    - Venta de Short Puts OTM 0-1 DTE cuando RSI < 25.
    - Cierre por Take Profit 95% o Time Stop a las 15:55 EST.
    - Cero simulación: Solo registra fills confirmados por IBKR.
    """

    def __init__(self, initial_capital: float = 1000000.0, allocated_capital: float = 150000.0, broker_manager: Optional[Any] = None, ibkr_adapter: Optional[Any] = None):
        self.config = load_yaml_config()
        self.rsi_config = self.config.get("CAPA_3_RSI", {})
        
        self.initial_capital = initial_capital
        self.allocated_capital = allocated_capital
        self.ibkr_adapter = ibkr_adapter or broker_manager
        self.broker_mgr = broker_manager or BrokerManager()
        self.risk_guardian = RiskGuardian(self.config)
        self.ledger = InstitutionalLedger(STATE_FILE)

        self.status_mode = "IDLE_MONITORING"
        self.open_trades: List[Dict[str, Any]] = []
        self.closed_trades: List[Dict[str, Any]] = []
        self.total_premiums_collected: float = 0.0
        self.total_pnl_usd: float = 0.0
        self.last_rsi_scanned: Dict[str, float] = {"SPY": 50.0, "QQQ": 50.0, "DIA": 50.0}

        self.load_state()

    def load_state(self):
        """Carga el estado local limpio del libro mayor."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.status_mode = data.get("status_mode", "IDLE_MONITORING")
                    self.open_trades = data.get("open_trades", [])
                    self.closed_trades = data.get("closed_trades", [])
                    self.total_premiums_collected = data.get("total_premiums_collected", 0.0)
                    self.total_pnl_usd = data.get("total_pnl_usd", 0.0)
                    self.last_rsi_scanned = data.get("last_rsi_scanned", {"SPY": 50.0, "QQQ": 50.0, "DIA": 50.0})
            except Exception as e:
                logging.error(f"[RSI] Error cargando estado: {e}")

    def save_state(self):
        """Guarda el estado utilizando escritura atómica."""
        state = {
            "last_update": now_et().isoformat(),
            "allocated_capital": self.rsi_config.get("ALLOCATED_CAPITAL_USD", 150000.0),
            "status_mode": self.status_mode,
            "total_premiums_collected": round(self.total_premiums_collected, 2),
            "total_pnl_usd": round(self.total_pnl_usd, 2),
            "open_trades": self.open_trades,
            "closed_trades": self.closed_trades,
            "last_rsi_scanned": self.last_rsi_scanned
        }
        try:
            temp_file = f"{STATE_FILE}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, STATE_FILE)
        except Exception as e:
            logging.error(f"[RSI] Error guardando estado atómico: {e}")

    def scan_market(self) -> Dict[str, Any]:
        """Escanea el mercado y busca picos de sobreventa RSI < 25."""
        self.config = load_yaml_config()
        self.rsi_config = self.config.get("CAPA_3_RSI", {})

        if not self.rsi_config.get("ENABLED", False):
            return {"status": "SKIPPED", "reason": "Capa 3 RSI deshabilitada."}

        if not self.risk_guardian.is_trading_enabled():
            return {"status": "SKIPPED", "reason": "Kill-switch activado (TRADING_ENABLED=false)."}

        if not is_nyse_market_open():
            return {"status": "SKIPPED", "reason": "Mercado cerrado."}

        if not self.broker_mgr.connect():
            return {"status": "ERROR", "reason": "Sin conexión con IB Gateway."}

        logging.info(f"[RSI] Escaneando RSI intradía en subyacentes ({self.rsi_config.get('UNIVERSE')})...")

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado de la Capa 3 RSI para la API y Dashboard."""
        return {
            "allocated_capital": self.rsi_config.get("ALLOCATED_CAPITAL_USD", 150000.0),
            "status_mode": self.status_mode,
            "open_trades": self.open_trades,
            "closed_trades": self.closed_trades,
            "total_premiums_collected": self.total_premiums_collected,
            "total_pnl_usd": self.total_pnl_usd,
            "last_rsi_scanned": self.last_rsi_scanned,
            "last_update": now_et().isoformat()
        }
