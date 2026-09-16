import json
import os
import math
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes

STATE_FILE = os.path.join(os.path.dirname(__file__), "wheel_compounding_state.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "wheel_compounding.log")

from cloud_persistence import sync_state_to_github_async, load_state_from_github

# Configuration for Wheel Strategy & Compounding
CONFIG = {
    "initial_capital_usd": 100000.0,
    "etf_target": "SPY",               # Primary compounding ETF (SPY or QQQ)
    "monthly_premium_target_pct": 2.0,  # 2.0% monthly options premium yield (~24% annual yield)
    "etf_annual_appreciation_pct": 9.0, # 9.0% average historical ETF appreciation
    "reinvest_premiums_pct": 100.0,    # 100% of collected premiums reinvested into more ETF shares
    "target_delta": 0.25,               # 0.25 Delta for high probability of expiring worthless (75%+ win rate)
    "target_dte": 30                    # 30 Days To Expiration
}

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_msg(tag, text):
    msg = f"[{timestamp()}] [{tag}] {text}"
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

class WheelCompoundingEngine:
    def __init__(self):
        self.initial_capital = CONFIG["initial_capital_usd"]
        self.cash_balance = self.initial_capital
        self.etf_shares = 0.0
        self.accumulated_premiums_usd = 0.0
        self.total_reinvested_usd = 0.0
        self.wheel_positions = []
        self.history = []
        self.load_state()

    def load_state(self):
        loaded = False
        # 1. Prioridad: Intentar cargar siempre desde GitHub Cloud
        gh_data = load_state_from_github("wheel_compounding_state.json")
        if gh_data and (gh_data.get("history") or gh_data.get("wheel_positions") or (gh_data.get("etf_shares") and gh_data.get("etf_shares") > 0)):
            self.initial_capital = gh_data.get("initial_capital", CONFIG["initial_capital_usd"])
            self.cash_balance = gh_data.get("cash_balance", self.initial_capital)
            self.etf_shares = gh_data.get("etf_shares", 0.0)
            self.accumulated_premiums_usd = gh_data.get("accumulated_premiums_usd", 0.0)
            self.total_reinvested_usd = gh_data.get("total_reinvested_usd", 0.0)
            self.wheel_positions = gh_data.get("wheel_positions", [])
            self.history = gh_data.get("history", [])
            log_msg("CLOUD_STATE", "Estado de Rueda recuperado exitosamente desde GitHub Cloud Backup.")
            loaded = True

        # 2. Si no hay estado en GitHub, intentar archivo local
        if not loaded and os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.initial_capital = data.get("initial_capital", CONFIG["initial_capital_usd"])
                    self.cash_balance = data.get("cash_balance", self.initial_capital)
                    self.etf_shares = data.get("etf_shares", 0.0)
                    self.accumulated_premiums_usd = data.get("accumulated_premiums_usd", 0.0)
                    self.total_reinvested_usd = data.get("total_reinvested_usd", 0.0)
                    self.wheel_positions = data.get("wheel_positions", [])
                    self.history = data.get("history", [])
                    log_msg("STATE", "Estado de Rueda & Interés Compuesto cargado exitosamente desde archivo local.")
                    loaded = True
            except Exception as e:
                log_msg("WARN", f"Error cargando estado ({e}). Inicializando valores por defecto.")
        
        if not loaded:
            self.save_state()

    def save_state(self):
        state = {
            "last_update": timestamp(),
            "initial_capital": self.initial_capital,
            "cash_balance": round(self.cash_balance, 2),
            "etf_shares": round(self.etf_shares, 4),
            "accumulated_premiums_usd": round(self.accumulated_premiums_usd, 2),
            "total_reinvested_usd": round(self.total_reinvested_usd, 2),
            "wheel_positions": self.wheel_positions,
            "history": self.history
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        sync_state_to_github_async("wheel_compounding_state.json", state)

    def fetch_etf_live_price(self, symbol="SPY"):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                current_price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                return round(current_price, 2)
        except Exception:
            return 560.50 if symbol == "SPY" else 485.20

    def calculate_compounding_projections(self, years=10):
        """
        Calcula la proyección matemática exponencial del Interés Compuesto
        Reinvirtiendo el 100% de las primas cobradas en más acciones del ETF
        """
        etf_price = self.fetch_etf_live_price(CONFIG["etf_target"])
        monthly_premium_yield = CONFIG["monthly_premium_target_pct"] / 100.0
        monthly_etf_growth = (CONFIG["etf_annual_appreciation_pct"] / 100.0) / 12.0

        projections = []
        current_portfolio_usd = self.initial_capital
        current_shares = current_portfolio_usd / etf_price
        current_etf_p = etf_price

        total_premiums_gen = 0.0

        for m in range(1, years * 12 + 1):
            # ETF Appreciation
            current_etf_p *= (1.0 + monthly_etf_growth)

            # Option Premium Cash Flow Generated (2.0% of portfolio per month)
            monthly_premium = current_portfolio_usd * monthly_premium_yield
            total_premiums_gen += monthly_premium

            # Auto-Compounding: Reinvest 100% of premium into buying MORE ETF Shares
            new_shares_bought = monthly_premium / current_etf_p
            current_shares += new_shares_bought

            # Total Portfolio Net Asset Value (NAV)
            current_portfolio_usd = current_shares * current_etf_p

            if m % 12 == 0:
                year_num = m // 12
                projections.append({
                    "year": year_num,
                    "etf_price": round(current_etf_p, 2),
                    "total_shares": round(current_shares, 2),
                    "accumulated_premiums_usd": round(total_premiums_gen, 2),
                    "portfolio_nav_usd": round(current_portfolio_usd, 2),
                    "cagr_pct": round((((current_portfolio_usd / self.initial_capital) ** (1 / year_num)) - 1) * 100, 2)
                })

        return projections

    def run_wheel_cycle(self):
        """Ejecuta un ciclo de la Estrategia Rueda (Wheel) y Re-Inversión de Primas"""
        etf_symbol = CONFIG["etf_target"]
        etf_price = self.fetch_etf_live_price(etf_symbol)

        log_msg("WHEEL_CYCLE", f"--- EJECUTANDO CICLO DE RUEDA & COMPUESTO EN {etf_symbol} (Precio ETF: ${etf_price} USD) ---")

        # Determine strategy phase: Cash-Secured Put (CSP) or Covered Call (CC)
        if self.etf_shares < 10:  # Holding Cash: Sell Cash-Secured Put
            strike = round(etf_price * 0.97, 1) # Strike 3% OTM
            greeks = black_scholes("PUT", etf_price, strike, CONFIG["target_dte"]/365.0, 0.0525, 0.18)
            premium = max(2.50, greeks["price"])
            
            # Premium Income Collected
            income_usd = round(premium * 100.0, 2)
            self.accumulated_premiums_usd += income_usd

            # AUTO-COMPOUNDING REINVESTMENT: Buy ETF shares with collected premium
            shares_bought = round(income_usd / etf_price, 4)
            self.etf_shares += shares_bought
            self.total_reinvested_usd += income_usd

            log_msg("CASH_PUT", f"🟢 VENTA CASH-SECURED PUT [{etf_symbol} K=${strike}]: Prima Cobrada: +${income_usd} USD.")
            log_msg("AUTO_REINVEST", f"📈 REINVERSIÓN AUTOMÁTICA: Compradas +{shares_bought} acciones de {etf_symbol} @ ${etf_price} USD. Total Acciones: {self.etf_shares:.4f}")

            exp_date = (datetime.now() + timedelta(days=CONFIG["target_dte"])).strftime("%Y-%m-%d")
            active_pos = {
                "id": f"WHEEL_CSP_{int(datetime.now().timestamp())}",
                "ticker": f"{etf_symbol}_PUT_{strike:.1f}_{CONFIG['target_dte']}DTE",
                "symbol": etf_symbol,
                "strategy_type": "CASH_SECURED_PUT",
                "underlying_price": etf_price,
                "strike": strike,
                "contracts": 1,
                "premium_collected_usd": income_usd,
                "issued_date": timestamp(),
                "expiration_date": exp_date,
                "target_dte": CONFIG["target_dte"],
                "status": "ACTIVE"
            }
            self.wheel_positions = [active_pos]

            cycle_record = {
                "timestamp": timestamp(),
                "type": "CASH_SECURED_PUT",
                "symbol": etf_symbol,
                "etf_price": etf_price,
                "strike": strike,
                "premium_collected_usd": income_usd,
                "shares_bought": shares_bought,
                "total_shares_now": round(self.etf_shares, 4),
                "portfolio_nav_usd": round(self.cash_balance + (self.etf_shares * etf_price), 2)
            }
            self.history.append(cycle_record)
            self.save_state()
            return cycle_record

        else: # Holding Shares: Sell Covered Call
            strike = round(etf_price * 1.03, 1) # Strike 3% OTM
            greeks = black_scholes("CALL", etf_price, strike, CONFIG["target_dte"]/365.0, 0.0525, 0.18)
            premium = max(2.50, greeks["price"])
            
            income_usd = round(premium * 100.0, 2)
            self.accumulated_premiums_usd += income_usd

            shares_bought = round(income_usd / etf_price, 4)
            self.etf_shares += shares_bought
            self.total_reinvested_usd += income_usd

            log_msg("COVERED_CALL", f"🟢 VENTA COVERED CALL [{etf_symbol} K=${strike}]: Prima Cobrada: +${income_usd} USD.")
            log_msg("AUTO_REINVEST", f"📈 REINVERSIÓN AUTOMÁTICA: Compradas +{shares_bought} acciones de {etf_symbol} @ ${etf_price} USD. Total Acciones: {self.etf_shares:.4f}")

            exp_date = (datetime.now() + timedelta(days=CONFIG["target_dte"])).strftime("%Y-%m-%d")
            active_pos = {
                "id": f"WHEEL_CC_{int(datetime.now().timestamp())}",
                "ticker": f"{etf_symbol}_CALL_{strike:.1f}_{CONFIG['target_dte']}DTE",
                "symbol": etf_symbol,
                "strategy_type": "COVERED_CALL",
                "underlying_price": etf_price,
                "strike": strike,
                "contracts": 1,
                "premium_collected_usd": income_usd,
                "issued_date": timestamp(),
                "expiration_date": exp_date,
                "target_dte": CONFIG["target_dte"],
                "status": "ACTIVE"
            }
            self.wheel_positions = [active_pos]

            cycle_record = {
                "timestamp": timestamp(),
                "type": "COVERED_CALL",
                "symbol": etf_symbol,
                "etf_price": etf_price,
                "strike": strike,
                "premium_collected_usd": income_usd,
                "shares_bought": shares_bought,
                "total_shares_now": round(self.etf_shares, 4),
                "portfolio_nav_usd": round(self.cash_balance + (self.etf_shares * etf_price), 2)
            }
            self.history.append(cycle_record)
            self.save_state()
            return cycle_record

    def auto_check_and_run_cycle(self):
        """Verifica automáticamente si es momento de iniciar o renovar el ciclo de 30 días"""
        try:
            if not self.history:
                log_msg("AUTO_WHEEL", "Iniciando primer ciclo automático de Rueda & Compuesto...")
                return self.run_wheel_cycle()

            last_cycle = self.history[-1]
            last_ts_str = last_cycle.get("timestamp")
            if last_ts_str:
                last_dt = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
                # Si han pasado 30 días desde el último ciclo, renovar automáticamente
                if datetime.now() - last_dt >= timedelta(days=CONFIG["target_dte"]):
                    log_msg("AUTO_WHEEL", f"Ciclo de {CONFIG['target_dte']} días completado. Renovando nuevo ciclo...")
                    return self.run_wheel_cycle()
        except Exception as e:
            log_msg("WARN", f"Error en verificación automática de Rueda: {e}")
        return None

    def transfer_profit_to_wheel(self, amount_usd):
        """Permite transferir profit hacia la compra directa de acciones ETF en la Rueda"""
        etf_symbol = CONFIG["etf_target"]
        etf_price = self.fetch_etf_live_price(etf_symbol)
        shares_bought = round(amount_usd / etf_price, 4)
        self.etf_shares += shares_bought
        self.total_reinvested_usd += amount_usd
        log_msg("MANUAL_TRANSFER", f"💵 TRANSFERENCIA MANUAL: +${amount_usd} USD aplicados a comprar +{shares_bought} acciones de {etf_symbol} @ ${etf_price} USD.")
        self.save_state()
        return {"shares_bought": shares_bought, "total_shares": self.etf_shares}

if __name__ == "__main__":
    wheel = WheelCompoundingEngine()
    print("Simulación de Proyecciones a 10 años:")
    print(json.dumps(wheel.calculate_compounding_projections(), indent=2))
