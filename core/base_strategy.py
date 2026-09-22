# -*- coding: utf-8 -*-
"""
core/base_strategy.py - Interfaz base universal para todas las estrategias de opciones
Garantiza un contrato uniforme de reporte, cálculo de margen y ciclo de ejecución.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseStrategy(ABC):
    def __init__(self, name: str, allocated_capital: float = 10000.0):
        self.name = name
        self.allocated_capital = allocated_capital

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna el estado operativo, métricas de balance, capital asignado y posiciones.
        """
        pass

    @abstractmethod
    def monitor_and_step(self):
        """
        Ejecuta el ciclo de monitoreo continuo (escanear señales, rolleo automático, toma de ganancias, etc.).
        """
        pass

    @abstractmethod
    def get_margin_required(self) -> float:
        """
        Retorna el capital o margen de garantía exacto que la estrategia tiene bloqueado.
        """
        pass

    def get_total_pnl(self) -> float:
        """
        Retorna el PnL neto total (realizado + flotante) de la estrategia.
        """
        status = self.get_status()
        return status.get("total_pnl_usd", 0.0)
