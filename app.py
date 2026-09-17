# -*- coding: utf-8 -*-
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
from credit_spread_bot import CreditSpreadBot, CONFIG as SPREAD_CONFIG
from alpha_trade_bot import AlphaTradeBot
from rsi_opportunistic_bot import RSIOpportunisticBot
from cloud_persistence import load_state_from_github
from master_portfolio_manager import MasterPortfolioManager

PORT = int(os.environ.get("PORT", 5050))
DIRECTORY = os.path.dirname(__file__)

engine = OptionsTradingEngine()
daytrade_bot = DayTradeOptionsBot()
wheel_engine = WheelCompoundingEngine()
credit_bot = CreditSpreadBot()
alpha_bot = AlphaTradeBot()
rsi_bot = RSIOpportunisticBot()

master_portfolio = MasterPortfolioManager(wheel_engine, credit_bot, alpha_bot, rsi_bot, daytrade_bot)

def is_market_open():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    time_num = now.hour * 100 + now.minute
    return 1030 <= time_num <= 1700

def background_trading_loop():
    print("⚡ Motores de Opciones Híbridos (5 Capas + Portfolio Margin + Tesorería SGOV) iniciados en segundo plano.")
    while True:
        try:
            # 1. Chequeo automático de Rueda & Compounding
            wheel_engine.auto_check_and_run_cycle()

            # 2. Escaneo intradiario 0-DTE, Credit Spreads & RSI Opportunistic 1DTE
            if is_market_open():
                daytrade_bot.run_intraday_scan()
                credit_bot.scan_and_execute_spreads()
                rsi_bot.scan_market()
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

        if path == "/api/master/summary":
            summary = master_portfolio.get_master_summary()
            return self.send_json_response(summary)

        elif path == "/api/etfs":
            etfs = engine.fetch_live_etf_prices()
            return self.send_json_response(etfs)

        elif path == "/api/alpha/status":
            return self.send_json_response(alpha_bot.get_status())

        elif path == "/api/rsi-opportunistic/status":
            return self.send_json_response(rsi_bot.get_status())

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
            daytrade_bot.load_state()
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

        elif path == "/api/spreads/status":
            credit_bot.load_state()
            stats = credit_bot.get_stats()
            total_pnl_usd = round(credit_bot.capital - credit_bot.initial_capital, 2)
            total_pnl_pct = round((total_pnl_usd / credit_bot.initial_capital) * 100.0, 2)

            state = {
                "config": SPREAD_CONFIG,
                "system_start_time": credit_bot.system_start_time,
                "initial_capital_usd": credit_bot.initial_capital,
                "capital": round(credit_bot.capital, 2),
                "total_premiums_collected": round(credit_bot.total_premiums_collected, 2),
                "total_pnl_usd": total_pnl_usd,
                "total_pnl_pct": total_pnl_pct,
                "stats": stats,
                "open_spreads": credit_bot.open_spreads,
                "closed_spreads": credit_bot.closed_spreads
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
                "wheel_positions": wheel_engine.wheel_positions,
                "history": wheel_engine.history
            }
            return self.send_json_response(state)

        elif path == "/api/wheel/projections":
            projections = wheel_engine.calculate_compounding_projections(years=10)
            return self.send_json_response(projections)

        elif path == "/api/backtest/1y":
            bt_file = os.path.join(os.path.dirname(__file__), "backtest_results_1y.json")
            if os.path.exists(bt_file):
                with open(bt_file, "r", encoding="utf-8") as f:
                    bt_data = json.load(f)
                return self.send_json_response(bt_data)
            else:
                from backtest_historical_1y import run_1y_backtest
                res = run_1y_backtest()
                return self.send_json_response(res)

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

        if path == "/api/alpha/decouple":
            pos_id = int(payload.get("position_id", 0))
            available_funds = float(payload.get("available_funds_usd", 1000.0))
            res = alpha_bot.decouple_short_put(pos_id, available_funds)
            return self.send_json_response(res)

        elif path == "/api/payoff":
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

        elif path == "/api/daytrade/sync-force":
            gh_data = load_state_from_github("daytrade_paper_state.json")
            if gh_data:
                daytrade_bot.system_start_time = gh_data.get("system_start_time", daytrade_bot.system_start_time)
                daytrade_bot.capital = gh_data.get("capital", daytrade_bot.capital)
                daytrade_bot.daily_pnl_usd = gh_data.get("daily_pnl_usd", daytrade_bot.daily_pnl_usd)
                daytrade_bot.total_commissions_paid = gh_data.get("total_commissions_paid", daytrade_bot.total_commissions_paid)
                daytrade_bot.open_positions = gh_data.get("open_positions", daytrade_bot.open_positions)
                daytrade_bot.closed_trades = gh_data.get("closed_trades", daytrade_bot.closed_trades)
                daytrade_bot.save_state()
                return self.send_json_response({
                    "status": "SUCCESS",
                    "closed_trades_count": len(daytrade_bot.closed_trades),
                    "capital": daytrade_bot.capital,
                    "daily_pnl_usd": daytrade_bot.daily_pnl_usd
                })
            return self.send_json_response({"status": "ERROR", "message": "No se pudo obtener datos de GitHub"}, 500)

        elif path == "/api/spreads/scan":
            credit_bot.scan_and_execute_spreads()
            return self.send_json_response({
                "status": "SUCCESS",
                "message": "Escaneo de venta de tiempo / credit spreads completado.",
                "open_spreads": credit_bot.open_spreads,
                "capital": credit_bot.capital
            })

        elif path == "/api/daytrade/mode":
            mode = payload.get("mode", "PAPER_TRADING")
            broker = payload.get("broker", "INTERACTIVE_BROKERS")
            DAYTRADE_CONFIG["execution_mode"] = mode
            DAYTRADE_CONFIG["broker_name"] = broker
            SPREAD_CONFIG["execution_mode"] = mode
            SPREAD_CONFIG["broker_name"] = broker
            return self.send_json_response({"status": "SUCCESS", "mode": mode, "broker": broker})

        elif path == "/api/wheel/run-cycle":
            cycle_result = wheel_engine.run_wheel_cycle()
            return self.send_json_response({
                "status": "SUCCESS",
                "cycle": cycle_result
            })

        elif path == "/api/wheel/transfer-profit":
            amount = float(payload.get("amount_usd", 0.0))
            if amount <= 0:
                return self.send_json_response({"error": "Monto inválido"}, 400)
            res = wheel_engine.transfer_profit_to_wheel(amount)
            return self.send_json_response({"status": "SUCCESS", "result": res})

        return self.send_json_response({"error": "Endpoint no encontrado"}, 404)

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), OptionsAPIHandler) as httpd:
        print("=" * 75)
        print(f"🚀 SISTEMA HÍBRIDO DE OPCIONES (5 CAPAS + PORTFOLIO MARGIN + SGOV)")
        print(f"🌐 Servidor Web Activo en Puerto: {PORT}")
        print(f"⚡ Modo de Ejecución: {DAYTRADE_CONFIG['execution_mode']} (Broker: {DAYTRADE_CONFIG['broker_name']})")
        print("=" * 75)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor detenido por el usuario.")

if __name__ == "__main__":
    run_server()
