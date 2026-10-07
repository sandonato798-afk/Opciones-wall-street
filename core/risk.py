# -*- coding: utf-8 -*-
"""
core/risk.py - Guardian de Riesgo y Candados Institucionales
Valida de forma estricta cada orden antes de enviarla al broker.
"""

import logging
from typing import Dict, Any, Tuple

class RiskGuardian:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_config = config.get("RISK_MANAGEMENT", {})
        self.global_config = config.get("GLOBAL", {})

    def is_trading_enabled(self) -> bool:
        """Verifica si el Interruptor de Emergencia (Kill Switch) permite operar."""
        return bool(self.global_config.get("TRADING_ENABLED", False))

    def validate_order(
        self,
        symbol: str,
        order_type: str,
        quantity: int,
        estimated_margin_usd: float,
        account_summary: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Audita una orden propuesta antes de su envio.
        Retorna (True, "OK") o (False, "Motivo del rechazo").
        """
        # 1. Kill switch check
        if not self.is_trading_enabled():
            return False, "🚨 RECHAZADA: Kill-switch global activado (TRADING_ENABLED=false)."

        # 2. Strict order type check
        if order_type.upper() == "MKT" or order_type.upper() == "MARKET":
            return False, "🚨 RECHAZADA: No se permiten ordenes a mercado (MKT) en opciones. Debe usar LIMIT."

        # 3. Quantity check
        if quantity <= 0:
            return False, f"🚨 RECHAZADA: Cantidad invalida de contratos ({quantity})."

        # 4. Account liquidity check
        if account_summary:
            excess_liquidity = account_summary.get("ExcessLiquidity", 0.0)
            net_liquidation = account_summary.get("NetLiquidation", 0.0)

            # Drawdown check
            max_dd_pct = self.risk_config.get("MAX_DAILY_DRAWDOWN_PCT", 0.02)
            unrealized_pnl = account_summary.get("UnrealizedPnL", 0.0)
            if net_liquidation > 0 and (unrealized_pnl / net_liquidation) < -max_dd_pct:
                return False, f"🚨 RECHAZADA: Maximo Drawdown Diario Excedido ({unrealized_pnl / net_liquidation:.2%})."

            # Excess liquidity check
            if estimated_margin_usd > excess_liquidity:
                return False, f"🚨 RECHAZADA: Margen requerido (${estimated_margin_usd:,.2f}) excede liquidez disponible (${excess_liquidity:,.2f})."

        return True, "OK"
