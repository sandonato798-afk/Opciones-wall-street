# -*- coding: utf-8 -*-
"""
core/contracts.py - Manejador de Contratos Validados de IBKR
Consulta la cadena real de opciones (reqSecDefOptParams / qualifyContracts).
Garantiza que NUNCA se intente operar un strike o vencimiento inexistente.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date

try:
    from ib_insync import IB, Option, Stock, Contract
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False


class ContractManager:
    def __init__(self, ib_client: Optional[Any] = None):
        self.ib = ib_client

    def find_valid_option_contract(
        self,
        symbol: str,
        right: str,               # 'C' para Call, 'P' para Put
        target_strike: float,
        target_dte: int,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Optional[Any]:
        """
        Busca y califica un contrato de opcion REAL en la cadena de IBKR.
        Garantiza que conId > 0 y que el strike exista oficialmente.
        """
        if not self.ib or not self.ib.isConnected():
            logging.error("[CONTRACTS] Error: No hay conexion activa con IBKR para validar contratos.")
            return None

        right = right.upper()
        if right not in ['C', 'P', 'CALL', 'PUT']:
            raise ValueError(f"Right invalido: {right}")
        right_code = 'C' if right in ['C', 'CALL'] else 'P'

        try:
            # 1. Crear contrato subyacente para calificar expiraciones
            underlying = Stock(symbol, exchange, currency)
            self.ib.qualifyContracts(underlying)

            # 2. Solicitar parametros de la cadena de opciones
            chains = self.ib.reqSecDefOptParams(underlying.symbol, '', underlying.secType, underlying.conId)
            if not chains:
                logging.warning(f"[CONTRACTS] No se encontraron cadenas de opciones para {symbol}.")
                return None

            # Usar la cadena principal SMART
            chain = next((c for c in chains if c.exchange == 'SMART'), chains[0])
            
            # 3. Encontrar la fecha de vencimiento mas cercana al target_dte
            today = date.today()
            expirations = sorted([datetime.strptime(exp, "%Y%m%d").date() for exp in chain.expirations])
            
            valid_exps = [exp for exp in expirations if (exp - today).days >= max(0, target_dte - 5)]
            if not valid_exps:
                selected_exp = expirations[-1]
            else:
                selected_exp = min(valid_exps, key=lambda exp: abs((exp - today).days - target_dte))

            exp_str = selected_exp.strftime("%Y%m%d")

            # 4. Encontrar el strike listado mas cercano al target_strike
            strikes = sorted(chain.strikes)
            selected_strike = min(strikes, key=lambda s: abs(s - target_strike))

            # 5. Instanciar contrato de opcion y calificarlo oficialmente con IBKR
            option_contract = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=exp_str,
                strike=selected_strike,
                right=right_code,
                exchange=exchange,
                currency=currency
            )

            qualified = self.ib.qualifyContracts(option_contract)
            if qualified and option_contract.conId > 0:
                logging.info(f"[CONTRACTS] ✅ Contrato Calificado: {symbol} {exp_str} {right_code}{selected_strike} (conId: {option_contract.conId})")
                return option_contract
            else:
                logging.warning(f"[CONTRACTS] IBKR no pudo calificar el contrato {symbol} {exp_str} {right_code}{selected_strike}.")
                return None

        except Exception as e:
            logging.error(f"[CONTRACTS] Error calificando contrato para {symbol}: {e}")
            return None
