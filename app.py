# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import http.server
import socketserver
import json
import os
import urllib.parse
import urllib.request
import webbrowser
import threading
import time
from datetime import datetime
from options_engine import OptionsTradingEngine
from daytrade_options_bot import DaytradeOptionsBot
from wheel_compounding_engine import WheelCompoundingEngine, CONFIG as WHEEL_CONFIG
DAYTRADE_CONFIG = {"execution_mode": "PAPER_TRADING", "broker_name": "INTERACTIVE_BROKERS"}
from alpha_trade_bot import AlphaTradeBot
from rsi_opportunistic_bot import RSIOpportunisticBot
from bull_market_bot import BullMarketBot
from cloud_persistence import load_state_from_github
from master_portfolio_manager import MasterPortfolioManager

PORT = int(os.environ.get("PORT", 5050))
DIRECTORY = os.path.dirname(__file__)

engine = OptionsTradingEngine()
daytrade_bot = DaytradeOptionsBot()
wheel_engine = WheelCompoundingEngine()
alpha_bot = AlphaTradeBot()
rsi_bot = RSIOpportunisticBot()
bullmarket_bot = BullMarketBot(allocated_capital=15000.0)

master_portfolio = MasterPortfolioManager(wheel_engine, alpha_bot, rsi_bot, daytrade_bot, bullmarket_bot)

def is_market_open():
    # Use UTC-based Eastern time (EDT=UTC-4, EST=UTC-5)
    # Using UTC-4 (EDT) — covers Apr-Oct; adjust to UTC-5 in Nov-Mar if needed
    from datetime import timezone, timedelta
    eastern = timezone(timedelta(hours=-4))
    now = datetime.now(eastern)
    if now.weekday() >= 5:
        return False
    time_num = now.hour * 100 + now.minute
    return 930 <= time_num <= 1600

# Global Health Monitor
SYSTEM_HEALTH_PINGS = {
    "wheel": 0,
    "alpha": 0,
    "rsi": 0,
    "daytrade": 0,
    "bullmarket": 0
}

# Candado Global para proteger la memoria concurrente
trading_state_lock = threading.Lock()

def background_trading_loop():
    print("Motor de Opciones Hibrido (5 Capas + Colateral SGOV/GLD/TLT + Reinversion Auto) iniciado.")
    cycle = 0
    import time as builtin_time
    while True:
        try:
            cycle += 1
            
            with trading_state_lock:
                # Capa 1: Rueda & Compounding
                wheel_engine.auto_check_and_run_cycle()
                SYSTEM_HEALTH_PINGS["wheel"] = builtin_time.time()

                # Capa 2: Alpha Trade - monitoreo de posiciones sinteticas
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
                    # Fuera de horario de mercado: verificar vencimientos de posiciones abiertas
                    daytrade_bot.manage_open_position()
                    SYSTEM_HEALTH_PINGS["daytrade"] = builtin_time.time()
                    SYSTEM_HEALTH_PINGS["rsi"] = builtin_time.time()

                # Motor de Reinversion Automatica: verifica cada 10 ciclos (~10 min)
                if cycle % 10 == 0:
                    result = master_portfolio.check_and_execute_reinvestment()
                    if result and result.get("status") == "EXECUTED":
                        print(f"[REINVESTMENT] Reinversion automatica ejecutada: ${result['record']['total_reinvested_usd']:.2f}")

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
            summary["health_pings"] = SYSTEM_HEALTH_PINGS
            return self.send_json_response(summary)

        elif path == "/api/etfs":
            etfs = engine.fetch_live_etf_prices()
            return self.send_json_response(etfs)

        elif path == "/api/alpha/status":
            return self.send_json_response(alpha_bot.get_status())

        elif path == "/api/rsi-opportunistic/status":
            return self.send_json_response(rsi_bot.get_status())

        elif path == "/api/bullmarket/status":
            bullmarket_bot.load_state()
            return self.send_json_response(bullmarket_bot.get_status())

        elif path == "/api/collateral/status":
            summary = master_portfolio.get_master_summary()
            return self.send_json_response(summary.get("collateral_portfolio", {}))

        elif path == "/api/reinvestment/status":
            return self.send_json_response(master_portfolio.get_reinvestment_status())


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
            active = daytrade_bot.active_trades
            history = daytrade_bot.history
            total_pnl = sum(t.get("realized_pnl_usd", t.get("pnl_usd", 0)) for t in history)
            wins = sum(1 for t in history if t.get("realized_pnl_usd", t.get("pnl_usd", 0)) > 0)
            losses = sum(1 for t in history if t.get("realized_pnl_usd", t.get("pnl_usd", 0)) < 0)
            win_rate = round(wins / len(history) * 100, 1) if history else 0.0

            formatted_active = []
            for p in active:
                item = dict(p)
                item["option_ticker"] = item.get("option_ticker", f"{item.get('symbol', 'SPY')} PUT ${item.get('strike', 0)} 1-DTE")
                contracts = item.get("contracts", 1)
                item["entry_premium"] = item.get("entry_premium", round(item.get("premium_collected_usd", 0) / (contracts * 100), 2))
                item["total_cost_usd"] = item.get("total_cost_usd", round(item.get("strike", 500) * 100 * contracts * 0.20, 2))
                item["pnl_usd"] = item.get("pnl_usd", 0.0)
                item["dte"] = item.get("dte", 1)
                formatted_active.append(item)

            formatted_history = []
            for p in history:
                item = dict(p)
                item["option_ticker"] = item.get("option_ticker", f"{item.get('symbol', 'SPY')} PUT ${item.get('strike', 0)} 1-DTE")
                net_pnl = item.get("final_pnl_usd", item.get("realized_pnl_usd", item.get("pnl_usd", 0.0)))
                item["final_pnl_usd"] = net_pnl
                item["pnl_usd"] = net_pnl
                item["entry_time"] = item.get("entry_time", item.get("issued_date", ""))
                item["exit_time"] = item.get("exit_time", item.get("expiration_date", ""))
                contracts = item.get("contracts", 1)
                item["entry_premium"] = item.get("entry_premium", round(item.get("premium_collected_usd", 0) / (contracts * 100), 2))
                cost = item.get("strike", 500) * 100 * contracts * 0.20
                item["final_pnl_pct"] = item.get("final_pnl_pct", round((net_pnl / cost) * 100, 2) if cost > 0 else 0.0)
                item["roi_pct"] = item.get("final_pnl_pct")
                item["dte"] = item.get("dte", 1)
                formatted_history.append(item)

            state = {
                "config": DAYTRADE_CONFIG,
                "allocated_capital": daytrade_bot.allocated_capital,
                "total_pnl_usd": round(total_pnl, 2),
                "active_trades": formatted_active,
                "open_positions": formatted_active,
                "history": formatted_history,
                "closed_trades": formatted_history,
                "stats": {
                    "total": len(history),
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate
                }
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

        elif path == "/api/reinvestment/execute":
            # Forzar ejecucion manual del motor de reinversion (ignora threshold)
            total = master_portfolio._get_total_premiums_collected()
            already = master_portfolio._reinvestment_state.get("total_reinvested_usd", 0.0)
            pending = round(total - already, 2)
            if pending <= 0:
                return self.send_json_response({"status": "NOTHING_PENDING", "pending_usd": pending})
            result = master_portfolio.check_and_execute_reinvestment()
            return self.send_json_response(result)

        elif path == "/api/bullmarket/open":
            res = bullmarket_bot.scan_market()
            return self.send_json_response(res)

        elif path == "/api/bullmarket/roll":
            diag_id = int(payload.get("diagonal_id", 0))
            if not diag_id and bullmarket_bot.open_diagonals:
                diag_id = bullmarket_bot.open_diagonals[0]["id"]
            res = bullmarket_bot.roll_short_call(diag_id)
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
            daytrade_bot.scan_market()
            daytrade_bot.manage_open_position()
            return self.send_json_response({
                "status": "SUCCESS",
                "message": "Escaneo intradiario completado.",
                "active_trades": daytrade_bot.active_trades
            })

        elif path == "/api/daytrade/mode":
            mode = payload.get("mode", "PAPER_TRADING")
            broker = payload.get("broker", "INTERACTIVE_BROKERS")
            DAYTRADE_CONFIG["execution_mode"] = mode
            DAYTRADE_CONFIG["broker_name"] = broker
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
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), OptionsAPIHandler) as httpd:
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
