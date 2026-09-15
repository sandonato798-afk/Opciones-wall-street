import http.server
import socketserver
import json
import os
import urllib.parse
import webbrowser
import threading
import time
from datetime import datetime
from options_engine import OptionsTradingEngine
from daytrade_options_bot import DayTradeOptionsBot, CONFIG as DAYTRADE_CONFIG

# Read PORT from environment variable (required by Koyeb / Railway) or default to 5050
PORT = int(os.environ.get("PORT", 5050))
DIRECTORY = os.path.dirname(__file__)

engine = OptionsTradingEngine()
daytrade_bot = DayTradeOptionsBot()

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    time_num = now.hour * 100 + now.minute
    return 1030 <= time_num <= 1700

def background_trading_loop():
    """Ejecuta escaneos intradiarios en segundo plano mientras el servidor Web HTML está activo"""
    print("⚡ Motor de Day Trading intradiario iniciado en segundo plano.")
    while True:
        try:
            if is_market_open():
                daytrade_bot.run_intraday_scan()
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Error en bucle en segundo plano: {e}")
            time.sleep(30)

# Start background scanner thread
scanner_thread = threading.Thread(target=background_trading_loop, daemon=True)
scanner_thread.start()

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

        # Serve index.html for root path
        if path == "/" or path == "":
            self.path = "/index.html"
            return super().do_GET()

        # API Endpoints
        if path == "/api/etfs":
            etfs = engine.fetch_live_etf_prices()
            return self.send_json_response(etfs)

        elif path == "/api/option-chain":
            symbol = query.get("symbol", ["SPY"])[0]
            dte = int(query.get("dte", [30])[0])
            chain_data = engine.generate_option_chain(symbol, dte=dte)
            return self.send_json_response(chain_data)

        elif path == "/api/portfolio":
            state = {
                "portfolio_capital": engine.portfolio_capital,
                "positions": engine.positions,
                "trade_history": engine.trade_history
            }
            return self.send_json_response(state)

        elif path == "/api/daytrade/status":
            state = {
                "config": DAYTRADE_CONFIG,
                "capital": daytrade_bot.capital,
                "daily_pnl": daytrade_bot.daily_pnl,
                "open_positions": daytrade_bot.open_positions,
                "closed_trades": daytrade_bot.closed_trades
            }
            return self.send_json_response(state)

        # Fallback to static file server (styles.css, app.js, etc.)
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

        if path == "/api/payoff":
            legs = payload.get("legs", [])
            payoff = engine.calculate_strategy_payoff(legs)
            return self.send_json_response(payoff)

        elif path == "/api/trade":
            symbol = payload.get("symbol", "SPY")
            strategy = payload.get("strategy", "Estrategia Simulado Opciones")
            legs = payload.get("legs", [])
            
            if not legs:
                return self.send_json_response({"error": "Debe especificar al menos una leg (opción)"}, 400)

            trade = engine.open_paper_trade(symbol, strategy, legs)
            return self.send_json_response({"status": "SUCCESS", "trade": trade})

        elif path == "/api/daytrade/scan":
            daytrade_bot.run_intraday_scan()
            return self.send_json_response({
                "status": "SUCCESS",
                "message": "Escaneo intradiario completado.",
                "open_positions": daytrade_bot.open_positions,
                "daily_pnl": daytrade_bot.daily_pnl
            })

        elif path == "/api/daytrade/mode":
            new_mode = payload.get("mode", "PAPER_TRADING")
            new_broker = payload.get("broker", "INTERACTIVE_BROKERS")
            DAYTRADE_CONFIG["execution_mode"] = new_mode
            DAYTRADE_CONFIG["broker_name"] = new_broker
            daytrade_bot.broker_adapter.mode = new_mode
            daytrade_bot.broker_adapter.broker = new_broker
            daytrade_bot.broker_adapter.connect()
            daytrade_bot.save_state()
            return self.send_json_response({
                "status": "SUCCESS",
                "execution_mode": new_mode,
                "broker": new_broker
            })

        return self.send_json_response({"error": "Endpoint no encontrado"}, 404)

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), OptionsAPIHandler) as httpd:
        print("=" * 75)
        print(f"🚀 SISTEMA DE OPCIONES & DAY TRADING 0-DTE (WALL STREET)")
        print(f"🌐 Servidor Web Activo en Puerto: {PORT}")
        print(f"⚡ Modo de Ejecución Actual: {DAYTRADE_CONFIG['execution_mode']} (Broker: {DAYTRADE_CONFIG['broker_name']})")
        print("=" * 75)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido por el usuario.")

if __name__ == "__main__":
    run_server()
