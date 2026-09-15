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
from wheel_compounding_engine import WheelCompoundingEngine, CONFIG as WHEEL_CONFIG

PORT = int(os.environ.get("PORT", 5050))
DIRECTORY = os.path.dirname(__file__)

engine = OptionsTradingEngine()
daytrade_bot = DayTradeOptionsBot()
wheel_engine = WheelCompoundingEngine()

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    time_num = now.hour * 100 + now.minute
    return 1030 <= time_num <= 1700

def background_trading_loop():
    print("⚡ Motor de Day Trading intradiario iniciado en segundo plano.")
    while True:
        try:
            if is_market_open():
                daytrade_bot.run_intraday_scan()
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Error en bucle en segundo plano: {e}")
            time.sleep(30)

def self_ping_loop():
    time.sleep(15)
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://opciones-wall-street.onrender.com")
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

# Start background threads
scanner_thread = threading.Thread(target=background_trading_loop, daemon=True)
scanner_thread.start()

ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
ping_thread.start()

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
            stats = daytrade_bot.get_win_rate_stats()
            daily_pnl_pct = round((daytrade_bot.daily_pnl_usd / daytrade_bot.initial_capital) * 100.0, 2)
            total_pnl_usd = round(daytrade_bot.capital - daytrade_bot.initial_capital, 2)
            total_pnl_pct = round((total_pnl_usd / daytrade_bot.initial_capital) * 100.0, 2)

            state = {
                "config": DAYTRADE_CONFIG,
                "system_start_time": daytrade_bot.system_start_time,
                "uptime_hours": daytrade_bot.get_uptime_hours(),
                "initial_capital_usd": daytrade_bot.initial_capital,
                "capital": daytrade_bot.capital,
                "daily_pnl_usd": daytrade_bot.daily_pnl_usd,
                "daily_pnl_pct": daily_pnl_pct,
                "total_pnl_usd": total_pnl_usd,
                "total_pnl_pct": total_pnl_pct,
                "total_commissions_paid": round(daytrade_bot.total_commissions_paid, 2),
                "stats": stats,
                "open_positions": daytrade_bot.open_positions,
                "closed_trades": daytrade_bot.closed_trades
            }
            return self.send_json_response(state)

        elif path == "/api/wheel/status":
            etf_price = wheel_engine.fetch_etf_live_price(WHEEL_CONFIG["etf_target"])
            nav_usd = round(wheel_engine.cash_balance + (wheel_engine.etf_shares * etf_price), 2)
            cagr = round((((nav_usd / wheel_engine.initial_capital) ** 1) - 1) * 100.0, 2)

            state = {
                "config": WHEEL_CONFIG,
                "initial_capital_usd": wheel_engine.initial_capital,
                "cash_balance": wheel_engine.cash_balance,
                "etf_symbol": WHEEL_CONFIG["etf_target"],
                "etf_price": etf_price,
                "etf_shares": wheel_engine.etf_shares,
                "portfolio_nav_usd": nav_usd,
                "accumulated_premiums_usd": wheel_engine.accumulated_premiums_usd,
                "total_reinvested_usd": wheel_engine.total_reinvested_usd,
                "cagr_pct": cagr,
                "history": wheel_engine.history
            }
            return self.send_json_response(state)

        elif path == "/api/wheel/projections":
            projections = wheel_engine.calculate_compounding_projections(years=10)
            return self.send_json_response(projections)

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
                "daily_pnl_usd": daytrade_bot.daily_pnl_usd
            })

        elif path == "/api/wheel/run-cycle":
            cycle_result = wheel_engine.run_wheel_cycle()
            return self.send_json_response({
                "status": "SUCCESS",
                "cycle": cycle_result
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
