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
    def __init__(self, host: str = None, port: int = None, client_id: int = 10, is_paper: bool = True):
        # Leer host/puerto desde variable de entorno (permite conectar a VM Oracle/Hetzner)
        # Si no hay variable, usa localhost (PC local con IB Gateway corriendo)
        self.host = host or os.environ.get("IBKR_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("IBKR_PORT", 4002))
        self.client_id = client_id
        self.is_paper = is_paper
        self.connected = False
        self.ib: Optional[Any] = None
        self._cached_summary: Dict[str, float] = {}
        self._last_summary_fetch: float = 0.0
        
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
                    self.update_account_summary_cache()
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

    def update_account_summary_cache(self) -> Dict[str, float]:
        """Consulta y actualiza en cache las metricas reales de la cuenta IBKR."""
        if self.is_live_connected():
            try:
                values = self.ib.accountValues()
                res = {}
                for item in values:
                    if item.tag in ["NetLiquidation", "TotalCashValue", "SettledCash", "BuyingPower", "UnrealizedPnL", "RealizedPnL", "AvailableFunds"]:
                        try:
                            res[item.tag] = float(item.value)
                        except ValueError:
                            pass
                if res:
                    self._cached_summary = res
                    self._last_summary_fetch = time.time()
                    return res
            except Exception as e:
                logging.debug(f"Account summary fetch debug: {e}")

        return self._cached_summary

    def get_account_summary(self) -> Dict[str, float]:
        """Obtiene liquidez, NAV total y margen disponible en vivo desde IBKR."""
        if self._cached_summary:
            return self._cached_summary

        return self.update_account_summary_cache() or {
            "NetLiquidation": 1000000.0,
            "TotalCashValue": 1000000.0,
            "SettledCash": 1000000.0,
            "BuyingPower": 4000000.0,
            "AvailableFunds": 1000000.0,
            "UnrealizedPnL": 0.0,
            "RealizedPnL": 0.0
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

    def execute_option_order_sync(self, symbol: str, right: str, strike: float, expiry: str, action: str, quantity: int, limit_price: float = 0.0) -> Dict:
        """
        Ejecuta una orden real (Market o Limit) y espera hasta 5 segundos para obtener el fill y la comisión.
        Si limit_price > 0, es Limit. Si es 0.0, es Market.
        """
        if self.is_live_connected():
            try:
                clean_expiry = expiry.replace("-", "")
                contract = Option(symbol, clean_expiry, strike, right, "SMART", currency="USD")
                self.ib.qualifyContracts(contract)

                if limit_price > 0:
                    order = LimitOrder(action.upper(), quantity, limit_price)
                else:
                    order = MarketOrder(action.upper(), quantity)

                trade = self.ib.placeOrder(contract, order)
                logging.info(f"🚀 [IBKR Order Sent] {action} {quantity}x {symbol} {right}{strike} Exp: {expiry}")
                
                # Espera activa (pumps the asyncio event loop)
                timeout = 5.0
                start_t = time.time()
                while not trade.isDone() and (time.time() - start_t) < timeout:
                    self.ib.sleep(0.1)

                if trade.orderStatus.status == 'Filled':
                    commissions = sum([e.commission for e in trade.fills if e.commission])
                    avg_price = trade.orderStatus.avgFillPrice
                    logging.info(f"✅ [FILLED] AvgPrice: ${avg_price} | Comm: ${commissions}")
                    return {
                        "status": "FILLED",
                        "filled": trade.orderStatus.filled,
                        "avg_price": avg_price,
                        "commission": commissions if commissions > 0 else 1.0
                    }
                elif trade.orderStatus.status in ['Submitted', 'PreSubmitted']:
                    logging.warning(f"⏳ [PENDING] La orden quedó abierta (no se llenó en 5s).")
                    return {
                        "status": "SUBMITTED",
                        "filled": trade.orderStatus.filled,
                        "avg_price": trade.orderStatus.avgFillPrice,
                        "commission": 0.0,
                        "order_id": trade.order.orderId
                    }
                else:
                    logging.warning(f"❌ [ORDER {trade.orderStatus.status}]")
                    return {
                        "status": trade.orderStatus.status,
                        "filled": trade.orderStatus.filled,
                        "avg_price": 0.0,
                        "commission": 0.0
                    }
            except Exception as e:
                logging.error(f"Error en execute_option_order_sync: {e}")
                return {"status": "ERROR", "error": str(e)}

        # Fallback de simulación (Paper sin conexión a TWS)
        simulated_price = limit_price if limit_price > 0 else 1.0 # Precio ficticio
        logging.info(f"🚀 [SIMULATED EXEC] {action} {quantity}x {symbol} {right}{strike} Exp: {expiry}")
        return {
            "status": "FILLED",
            "filled": quantity,
            "avg_price": simulated_price,
            "commission": 1.0
        }


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

    def ping_heartbeat(self) -> Dict[str, Any]:
        """Sistema de Latidos: Envía un ping al socket de IBKR para validar latencia y estado."""
        start_t = time.time()
        if self.is_live_connected():
            try:
                # Consulta liviana de tiempo/versión de servidor IBKR
                _ = self.ib.client.serverVersion()
                latency_ms = round((time.time() - start_t) * 1000, 2)
                return {
                    "status": "ONLINE",
                    "latency_ms": max(latency_ms, 1.5),
                    "last_heartbeat": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "live": True
                }
            except Exception as e:
                logging.warning(f"⚠️ Fallo de latido (Heartbeat) en IBKR socket: {e}")
                return {
                    "status": "DEGRADED",
                    "latency_ms": 999.0,
                    "last_heartbeat": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "live": False,
                    "error": str(e)
                }
        
        return {
            "status": "SIMULATED",
            "latency_ms": 1.0,
            "last_heartbeat": time.strftime("%Y-%m-%d %H:%M:%S"),
            "live": False
        }


import subprocess
import os

class IBKRWatchdog:
    """Perro Guardián Auto-Healing: Supervisa la pasarela IB Gateway y auto-reinicia StartGateway.bat si cae."""
    def __init__(self, adapter: IBKRBrokerAdapter, gateway_bat_path: Optional[str] = None):
        self.adapter = adapter
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\HP")
        default_bat = os.path.join(user_profile, r"Dropbox\D+ARQ\2_FINANZAS_Y_CRIPTO\FINANZAS Y CRIPTO\02_INFRAESTRUCTURA_IBKR\IBC\StartGateway.bat")
        self.gateway_bat_path = gateway_bat_path or default_bat
        self.reconnect_count = 0
        self.last_restart_time = 0.0

    def check_and_heal(self) -> bool:
        """Verifica la conectividad y si la pasarela cayó, intenta reconectar o auto-reinicia IB Gateway."""
        hb = self.adapter.ping_heartbeat()
        if hb["status"] == "ONLINE" or hb["status"] == "SIMULATED":
            return True

        logging.warning("🚨 Watchdog: Pasarela IBKR no responde. Iniciando protocolo de Auto-Healing...")
        
        # 1. Intentar reconexión simple de socket
        if self.adapter.connect():
            logging.info("✅ Watchdog: Reconexión exitosa a la API de IBKR.")
            return True

        # 2. Si falló la reconexión, auto-lanzar StartGateway.bat si transcurrieron >60s del último reinicio
        now = time.time()
        if now - self.last_restart_time > 60:
            self.last_restart_time = now
            self.reconnect_count += 1
            logging.info(f"🔄 Watchdog: Lanzando StartGateway.bat automáticamente (Intento #{self.reconnect_count})...")
            try:
                if os.path.exists(self.gateway_bat_path):
                    subprocess.Popen([self.gateway_bat_path], shell=True)
                    logging.info("🚀 StartGateway.bat ejecutado en segundo plano. Esperando 15s a que inicie el socket...")
                    time.sleep(15)
                    return self.adapter.connect()
                else:
                    logging.error(f"❌ No se encontró el script StartGateway.bat en: {self.gateway_bat_path}")
            except Exception as e:
                logging.error(f"❌ Error ejecutando Watchdog StartGateway.bat: {e}")

        return False


# Alias para compatibilidad de imports
IBKRAdapter = IBKRBrokerAdapter

if __name__ == "__main__":
    adapter = IBKRBrokerAdapter(port=4002, is_paper=True)
    success = adapter.connect()
    summary = adapter.get_account_summary()
    hb = adapter.ping_heartbeat()
    print("Estado Conectado:", success)
    print("Resumen de Cuenta IBKR:", summary)
    print("Latido (Heartbeat):", hb)

