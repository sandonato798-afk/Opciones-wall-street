# -*- coding: utf-8 -*-
"""
app.py - Orquestador Principal del Sistema de Opciones (5 Capas)
Servidor Web Modular y Coordinador de Hilos en Segundo Plano
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import http.server
import socketserver
import json
import os
import urllib.parse
import urllib.request
import threading
import time
from datetime import datetime, timezone, timedelta

# Importación de Motores y Bots
from options_engine import OptionsTradingEngine
from daytrade_options_bot import DaytradeOptionsBot
from wheel_compounding_engine import WheelCompoundingEngine, CONFIG as WHEEL_CONFIG
from alpha_trade_bot import AlphaTradeBot
from rsi_opportunistic_bot import RSIOpportunisticBot
from bull_market_bot import BullMarketBot
from master_portfolio_manager import MasterPortfolioManager

# Enrutador Modular de Endpoints
from routes import dispatch_get, dispatch_post

PORT = int(os.environ.get("PORT", 5050))
DIRECTORY = os.path.dirname(__file__)

DAYTRADE_CONFIG = {"execution_mode": "PAPER_TRADING", "broker_name": "INTERACTIVE_BROKERS"}

# Inicialización de Bots y Gestor Maestro
engine = OptionsTradingEngine()
daytrade_bot = DaytradeOptionsBot()
wheel_engine = WheelCompoundingEngine()
alpha_bot = AlphaTradeBot()
rsi_bot = RSIOpportunisticBot()
bullmarket_bot = BullMarketBot(allocated_capital=15000.0)

master_portfolio = MasterPortfolioManager(wheel_engine, alpha_bot, rsi_bot, daytrade_bot, bullmarket_bot)

# Monitor Global de Salud
SYSTEM_HEALTH_PINGS = {
    "wheel": 0,
    "alpha": 0,
    "rsi": 0,
    "daytrade": 0,
    "bullmarket": 0
}

# Contexto global inyectado a los controladores de rutas
APP_CONTEXT = {
    "engine": engine,
    "wheel_engine": wheel_engine,
    "wheel_config": WHEEL_CONFIG,
    "alpha_bot": alpha_bot,
    "rsi_bot": rsi_bot,
    "daytrade_bot": daytrade_bot,
    "daytrade_config": DAYTRADE_CONFIG,
    "bullmarket_bot": bullmarket_bot,
    "master_portfolio": master_portfolio,
    "health_pings": SYSTEM_HEALTH_PINGS
}

def is_market_open():
    eastern = timezone(timedelta(hours=-4))
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    time_num = now.hour * 100 + now.minute
    return 930 <= time_num <= 1600

trading_state_lock = threading.Lock()

def background_trading_loop():
    print("🚀 Motor de Opciones Híbrido (5 Capas + Portfolio Margin + Compounding) iniciado.")
    cycle = 0
    import time as builtin_time
    while True:
        try:
            cycle += 1
            with trading_state_lock:
                # Capa 1: Rueda & Compounding
                wheel_engine.auto_check_and_run_cycle()
                SYSTEM_HEALTH_PINGS["wheel"] = builtin_time.time()

                # Capa 2: Alpha Trade (Sintéticos LEAPS)
                alpha_bot.monitor_positions()
                SYSTEM_HEALTH_PINGS["alpha"] = builtin_time.time()

                # Capa 5: Bull Market PMCC (Diagonal Spread Alcista)
                bullmarket_bot.monitor_positions()
                SYSTEM_HEALTH_PINGS["bullmarket"] = builtin_time.time()

                if is_market_open():
                    # Capa 4: Daytrading ITM 1DTE
                    daytrade_bot.scan_market()
                    daytrade_bot.manage_open_position()
                    SYSTEM_HEALTH_PINGS["daytrade"] = builtin_time.time()
                    # Capa 3: RSI Oportunista
                    rsi_bot.scan_market()
                    SYSTEM_HEALTH_PINGS["rsi"] = builtin_time.time()
                    # Capa 5: Bull Market PMCC escaneo
                    bullmarket_bot.scan_market()
                else:
                    daytrade_bot.manage_open_position()
                    SYSTEM_HEALTH_PINGS["daytrade"] = builtin_time.time()
                    SYSTEM_HEALTH_PINGS["rsi"] = builtin_time.time()

                # Motor de Reinversión Automática (cada 10 ciclos)
                if cycle % 10 == 0:
                    result = master_portfolio.check_and_execute_reinvestment()
                    if result and result.get("status") == "EXECUTED":
                        print(f"[REINVESTMENT] Reinversión ejecutada: ${result['record']['total_reinvested_usd']:.2f}")

            time.sleep(60)
        except Exception as e:
            print(f"Error en bucle en segundo plano: {e}")
            time.sleep(30)

def self_ping_loop():
    time.sleep(15)
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://opciones-wall-street-xmz0.onrender.com")
    print(f"⏰ Hilo Keep-Alive activo. Auto-ping programado a: {render_url}")
    
    while True:
        try:
            time.sleep(600)
            headers = {'User-Agent': 'Mozilla/5.0 (Keep-Alive Self-Ping)'}
            req = urllib.request.Request(f"{render_url}/api/etfs", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 Keep-Alive Self-Ping Exitoso (Status {resp.status})")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Self-Ping Warning: {e}")

# Iniciar hilos en segundo plano
threading.Thread(target=background_trading_loop, daemon=True).start()
threading.Thread(target=self_ping_loop, daemon=True).start()

class OptionsAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/" or path == "":
            self.path = "/index.html"
            return super().do_GET()

        status, response = dispatch_get(path, query, APP_CONTEXT)
        if status is not None:
            return self.send_json_response(response, status)

        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            payload = {}

        status, response = dispatch_post(path, payload, APP_CONTEXT)
        if status is not None:
            return self.send_json_response(response, status)

        return self.send_json_response({"error": "Endpoint no encontrado"}, 404)

def run_server():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), OptionsAPIHandler) as httpd:
        print("=" * 75)
        print(f"🚀 SISTEMA MODULAR DE OPCIONES (5 CAPAS + PORTFOLIO MARGIN + SGOV)")
        print(f"🌐 Servidor Web Activo en Puerto: {PORT}")
        print(f"⚡ Modo de Ejecución: {DAYTRADE_CONFIG['execution_mode']} (Broker: {DAYTRADE_CONFIG['broker_name']})")
        print("=" * 75)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido por el usuario.")

if __name__ == "__main__":
    run_server()
