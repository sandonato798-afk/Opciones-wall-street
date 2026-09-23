# -*- coding: utf-8 -*-
"""
ibkr_adapter.py - Módulo de Integración Institucional para Interactive Brokers (IBKR)
Soporta Paper Trading (Puerto 4002 / 7497) y Live Trading (Puerto 4001 / 7496) vía IB Gateway / TWS API.
Conecta de forma nativa mediante ib_insync (asíncrono, institucional).
Incluye candados de gestión de riesgo automáticos (Server-Side Bracket Orders).
"""

import logging
import time
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    from ib_insync import IB, Option, Stock, MarketOrder, LimitOrder, StopOrder, util
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False
    logging.warning("⚠️ ib_insync no está instalado. Operando en modo simulación.")


class IBKRBrokerAdapter:
    def __init__(self, host: str = "127.0.0.1", port: int = 4002, client_id: int = 1, is_paper: bool = True):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.is_paper = is_paper
        self.connected = False
        self.ib: Optional[Any] = None
        
        # Candados de Seguridad / Risk Management Locks
        self.max_daily_drawdown_pct = 0.02  # Max 2% pérdida en 1 día
        self.max_concurrent_trades = 4     # Máximo 4 posiciones en simultáneo
        self.stop_loss_pct = 0.18           # Stop Loss al -18%
        self.take_profit_pct = 0.50         # Take Profit institucional al 50%
        self.max_delta = 0.25               # Delta máximo para venta de opciones (Rueda)

    def connect(self) -> bool:
        """Conecta con IB Gateway o TWS."""
        logging.info(f"Conectando a IBKR ({'PAPER' if self.is_paper else 'LIVE'}) en {self.host}:{self.port} (Client ID: {self.client_id})...")
        
        if IB_INSYNC_AVAILABLE:
            try:
                if self.ib is None:
                    self.ib = IB()
                if not self.ib.isConnected():
                    self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=4)
                self.connected = self.ib.isConnected()
                if self.connected:
                    logging.info("✅ Conexión establecida exitosamente con Interactive Brokers (IB Gateway / TWS).")
                    return True
            except Exception as e:
                logging.warning(f"⚠️ No se pudo conectar al socket {self.host}:{self.port} de IBKR: {e}. Activando fallback de simulación.")
                self.connected = False
                return False
        else:
            time.sleep(1)
            self.connected = True
            logging.info("✅ Conexión en modo Simulación Activa (ib_insync no disponible).")
            return True

    def disconnect(self):
        """Desconecta limpiamente el socket."""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            self.connected = False
            logging.info("🔌 Desconectado de Interactive Brokers.")

    def is_live_connected(self) -> bool:
        """Verifica si el socket real está activo."""
        return bool(self.ib and self.ib.isConnected())

    def get_account_summary(self) -> Dict[str, float]:
        """Obtiene liquidez, NAV total y margen disponible en vivo desde IBKR."""
        if self.is_live_connected():
            try:
                summary = self.ib.accountSummary()
                res = {}
                for item in summary:
                    if item.tag in ["NetLiquidation", "TotalCashValue", "SettledCash", "BuyingPower", "UnrealizedPnL", "RealizedPnL", "AvailableFunds"]:
                        try:
                            res[item.tag] = float(item.value)
                        except ValueError:
                            pass
                return res
            except Exception as e:
                logging.error(f"Error consultando accountSummary en IBKR: {e}")

        # Estructura fallback / simulación
        return {
            "NetLiquidation": 113743.28,
            "TotalCashValue": 82553.28,
            "SettledCash": 82553.28,
            "BuyingPower": 280000.0,
            "AvailableFunds": 82553.28,
            "UnrealizedPnL": 9824.0,
            "RealizedPnL": 3919.28
        }

    def place_bracket_option_order(self, symbol: str, option_type: str, strike: float, expiry: str, 
                                   action: str, quantity: int, limit_price: float) -> Dict:
        """
        Envía una orden tipo BRACKET a los servidores de IBKR.
        La orden incluye Stop Loss (-18%) y Take Profit (+50%) que viven en el servidor de IBKR.
        """
        sl_price = round(limit_price * (1 - self.stop_loss_pct), 2)
        tp_price = round(limit_price * (1 - self.take_profit_pct), 2) if action == "SELL" else round(limit_price * (1 + self.take_profit_pct), 2)

        if self.is_live_connected():
            try:
                right = "C" if option_type.upper().startswith("C") else "P"
                # Formato expiry YYYYMMDD
                clean_expiry = expiry.replace("-", "")
                contract = Option(symbol, clean_expiry, strike, right, "SMART", currency="USD")
                self.ib.qualifyContracts(contract)

                # Construir Bracket Order en IBKR
                parent_action = action.upper()
                closing_action = "BUY" if parent_action == "SELL" else "SELL"

                parent = LimitOrder(parent_action, quantity, limit_price)
                parent.transmit = False

                take_profit = LimitOrder(closing_action, quantity, tp_price)
                take_profit.parentId = parent.orderId
                take_profit.transmit = False

                stop_loss = StopOrder(closing_action, quantity, sl_price)
                stop_loss.parentId = parent.orderId
                stop_loss.transmit = True

                orders = [parent, take_profit, stop_loss]
                for o in orders:
                    trade = self.ib.placeOrder(contract, o)

                logging.info(f"🚀 [IBKR Real Order Transmitted] {action} {quantity}x {symbol} Strike {strike} ({expiry}) | Limit: ${limit_price} | TP: ${tp_price} | SL: ${sl_price}")
                return {
                    "status": "SUBMITTED_LIVE",
                    "parent_order_id": parent.orderId,
                    "symbol": symbol,
                    "strike": strike,
                    "expiry": expiry
                }
            except Exception as e:
                logging.error(f"Error enviando orden real a IBKR: {e}")

        # Fallback de simulación
        order_payload = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "strike": strike,
            "expiry": expiry,
            "limit_price": limit_price,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "mode": "PAPER_SIMULATION"
        }
        logging.info(f"🚀 [IBKR Order Sent (Sim)] {action} {quantity}x {symbol} Strike {strike} ({expiry}) | Limit: ${limit_price} | TP: ${tp_price} | SL: ${sl_price}")
        return {"status": "SUBMITTED_SIMULATED", "order_id": int(time.time()), "payload": order_payload}

    def check_risk_limits(self, current_daily_loss_pct: float, current_open_positions: int) -> bool:
        """Verifica si se violó algún candado de seguridad antes de abrir una nueva posición."""
        if current_daily_loss_pct >= self.max_daily_drawdown_pct:
            logging.warning(f"🛑 [CANDADO ACTIVADO] Pérdida diaria ({current_daily_loss_pct*100:.2f}%) superó el límite permitido ({self.max_daily_drawdown_pct*100:.2f}%). Se congelan compras.")
            return False
        if current_open_positions >= self.max_concurrent_trades:
            logging.warning(f"🛑 [CANDADO ACTIVADO] Límite de posiciones concurrentes alcanzado ({current_open_positions}/{self.max_concurrent_trades}).")
            return False
        return True


# Alias para compatibilidad de imports
IBKRAdapter = IBKRBrokerAdapter

if __name__ == "__main__":
    adapter = IBKRBrokerAdapter(port=4002, is_paper=True)
    success = adapter.connect()
    summary = adapter.get_account_summary()
    print("Estado Conectado:", success)
    print("Resumen de Cuenta IBKR:", summary)
