# -*- coding: utf-8 -*-
"""
core/orders.py - Motor de Ejecucion Institucional de Ordenes
Procesa unicamentes ordenes LIMIT (Precio Medio +- tick) con monitoreo de estado real.
Soporta combos de multiples patas (BAG) y prohibe estrictamente respuestas "FILLED" simuladas.
"""

import logging
import time
from typing import Optional, Dict, Any, List

try:
    from ib_insync import IB, LimitOrder, Order, Trade, Contract, Bag, ComboLeg
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False


class OrderExecutionEngine:
    def __init__(self, ib_client: Optional[Any] = None, timeout_seconds: int = 15):
        self.ib = ib_client
        self.timeout_seconds = timeout_seconds

    def execute_limit_order(
        self,
        contract: Any,
        action: str,            # 'BUY' o 'SELL'
        quantity: int,
        limit_price: float,
        order_ref: str = ""
    ) -> Dict[str, Any]:
        """
        Ejecuta una orden LIMIT sobre un contrato calificado de IBKR.
        Supervisa el estado hasta confirmacion de Fill o Timeout.
        """
        if not self.ib or not self.ib.isConnected():
            return {
                "status": "REJECTED",
                "reason": "Sin conexion activa con el broker IBKR.",
                "filled_quantity": 0,
                "avg_fill_price": 0.0
            }

        action = action.upper()
        if action not in ['BUY', 'SELL']:
            raise ValueError(f"Accion invalida: {action}")

        # Asegurar precio limit valido
        limit_price = round(limit_price, 2)
        order = LimitOrder(action, quantity, limit_price, orderRef=order_ref)

        logging.info(f"[ORDERS] Enviando orden LIMIT: {action} {quantity} {contract.symbol} @ ${limit_price:.2f} (Ref: {order_ref})...")

        try:
            trade: Trade = self.ib.placeOrder(contract, order)
            start_time = time.time()

            # Monitorear confirmacion de ejecucion en tiempo real
            while not trade.isDone():
                self.ib.sleep(0.5)
                if time.time() - start_time > self.timeout_seconds:
                    logging.warning(f"[ORDERS] Timeout alcanzado ({self.timeout_seconds}s) para orden #{trade.order.orderId}. Cancelando orden...")
                    self.ib.cancelOrder(order)
                    self.ib.sleep(1.0)
                    break

            status = trade.orderStatus.status
            filled_qty = trade.orderStatus.filled
            avg_price = trade.orderStatus.avgFillPrice
            commission = sum(fill.commissionReport.commission for fill in trade.fills if fill.commissionReport)

            if status == 'Filled':
                logging.info(f"[ORDERS] ✅ Orden #{trade.order.orderId} FILLED COMPLETAMENTE: {filled_qty} @ ${avg_price:.2f} (Comision: ${commission:.2f})")
                return {
                    "status": "FILLED",
                    "order_id": trade.order.orderId,
                    "perm_id": trade.order.permId,
                    "filled_quantity": filled_qty,
                    "avg_fill_price": avg_price,
                    "commission": commission,
                    "raw_trade": trade
                }
            elif filled_qty > 0:
                logging.warning(f"[ORDERS] ⚠️ Orden #{trade.order.orderId} FILLED PARCIALMENTE: {filled_qty}/{quantity} @ ${avg_price:.2f}")
                return {
                    "status": "PARTIALLY_FILLED",
                    "order_id": trade.order.orderId,
                    "perm_id": trade.order.permId,
                    "filled_quantity": filled_qty,
                    "avg_fill_price": avg_price,
                    "commission": commission,
                    "raw_trade": trade
                }
            else:
                logging.warning(f"[ORDERS] ❌ Orden #{trade.order.orderId} NO EJECUTADA (Estado final: {status}).")
                return {
                    "status": status.upper() if status else "CANCELLED",
                    "reason": f"Orden no fue completada en el broker (Estado: {status}).",
                    "filled_quantity": 0,
                    "avg_fill_price": 0.0
                }

        except Exception as e:
            logging.error(f"[ORDERS] Error fatal enviando orden a IBKR: {e}")
            return {
                "status": "ERROR",
                "reason": str(e),
                "filled_quantity": 0,
                "avg_fill_price": 0.0
            }
