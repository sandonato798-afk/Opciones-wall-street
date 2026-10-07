# -*- coding: utf-8 -*-
"""
core/broker.py - Manejador de Conexion y Socket Centralizado de IBKR
Hilo unico dueno del evento asyncio de ib_insync.
Proporciona heartbeat real (reqCurrentTime), handlers de eventos de error y snapshots thread-safe.
"""

import logging
import threading
import time
import os
from typing import Optional, Dict, Any, List

try:
    from ib_insync import IB, util
    IB_INSYNC_AVAILABLE = True
except ImportError:
    IB_INSYNC_AVAILABLE = False


class BrokerManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BrokerManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, host: str = None, port: int = None, client_id: int = 11):
        if self._initialized:
            return
        
        self.host = host or os.environ.get("IBKR_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("IBKR_PORT", 4002))
        self.client_id = client_id
        
        self.ib: Optional[Any] = None
        self.connected = False
        self._summary_cache: Dict[str, float] = {}
        self._positions_cache: List[Any] = []
        self._cache_lock = threading.Lock()
        self._initialized = True

    def connect(self) -> bool:
        """Establece conexion con el socket de IB Gateway / TWS con rotacion automatica de ClientID."""
        if not IB_INSYNC_AVAILABLE:
            logging.warning("[BROKER] ib_insync no esta disponible. Modo deshabilitado.")
            return False

        with self._lock:
            try:
                if not self.ib or not self.ib.isConnected():
                    connected_ok = False
                    for attempt_id in range(self.client_id, self.client_id + 15):
                        try:
                            logging.info(f"[BROKER] Intentando conexion a IBKR Gateway ({self.host}:{self.port}) con ClientID {attempt_id}...")
                            self.ib = IB()
                            self.ib.errorEvent += self._on_ib_error
                            self.ib.connect(self.host, self.port, clientId=attempt_id, timeout=5)
                            self.client_id = attempt_id
                            connected_ok = True
                            break
                        except Exception as conn_err:
                            err_str = str(conn_err).lower()
                            if "already in use" in err_str or "326" in err_str or "duplicado" in err_str or "clientid" in err_str:
                                logging.warning(f"⚠️ Client ID {attempt_id} ocupado. Probando Client ID {attempt_id + 1}...")
                                continue
                            else:
                                raise conn_err

                    if not connected_ok:
                        logging.error(f"[BROKER] ❌ No se pudo encontrar Client ID libre entre {self.client_id} y {self.client_id + 15}.")
                        self.connected = False
                        return False

                self.connected = self.ib.isConnected()
                if self.connected:
                    self.ib.reqMarketDataType(3)
                    logging.info(f"[BROKER] ✅ Conexion exitosa con IB Gateway (ClientID: {self.client_id}).")
                    self.refresh_account_snapshot()
                    return True
            except Exception as e:
                logging.error(f"[BROKER] Error conectando con IB Gateway socket ({self.host}:{self.port}): {e}")
                self.connected = False
                return False

    def _on_ib_error(self, reqId: int, errorCode: int, errorString: str, contract: Any):
        """Handler central para codigos de evento/error de IBKR."""
        # 1100: Connectivity lost, 1101: Connectivity restored (data lost), 1102: Connectivity restored (data preserved)
        if errorCode in [1100, 1101, 1102]:
            logging.warning(f"⚠️ [IBKR EVENT {errorCode}] Status de red: {errorString}")
        elif errorCode == 326:
            logging.error(f"🚨 [IBKR ERROR 326] Client ID duplicado ({self.client_id}). Cambie el clientId.")
        elif errorCode == 200:
            logging.warning(f"⚠️ [IBKR ERROR 200] Contrato no encontrado o invalido: {errorString}")
        else:
            logging.info(f"[IBKR MSG {errorCode}] {errorString}")

    def ping_heartbeat(self) -> bool:
        """Realiza un heartbeat real consultando reqCurrentTime() al servidor de IBKR."""
        if not self.ib or not self.ib.isConnected():
            return False
        try:
            current_time = self.ib.reqCurrentTime()
            return current_time is not None
        except Exception:
            return False

    def refresh_account_snapshot(self):
        """Actualiza el resumen de cuenta y posiciones de forma thread-safe."""
        if not self.ib or not self.ib.isConnected():
            return
        try:
            values = self.ib.accountValues()
            summary = {}
            for item in values:
                if item.tag in ["NetLiquidation", "TotalCashValue", "SettledCash", "BuyingPower", "UnrealizedPnL", "RealizedPnL", "ExcessLiquidity", "InitMarginReq"]:
                    try:
                        summary[item.tag] = float(item.value)
                    except ValueError:
                        pass
            
            positions = self.ib.positions()
            
            with self._cache_lock:
                self._summary_cache = summary
                self._positions_cache = positions

        except Exception as e:
            logging.error(f"[BROKER] Error actualizando snapshot de cuenta: {e}")

    def get_account_summary_snapshot(self) -> Dict[str, float]:
        with self._cache_lock:
            return dict(self._summary_cache)

    def get_positions_snapshot(self) -> List[Any]:
        with self._cache_lock:
            return list(self._positions_cache)
