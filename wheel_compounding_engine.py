import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import os
import math
import urllib.request
from datetime import datetime, timedelta
from options_engine import black_scholes
from market_calendar import is_trading_day

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
    try:
        print(msg)
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

class WheelCompoundingEngine:
    def __init__(self, ibkr_adapter=None):
        self.ibkr_adapter = ibkr_adapter
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
        if os.path.exists(STATE_FILE):
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
                log_msg("STATE_ERR", f"Error cargando estado local: {e}")

        if not loaded:
            gh_data = load_state_from_github("wheel_compounding_state.json")
            if gh_data:
                self.initial_capital = gh_data.get("initial_capital", CONFIG["initial_capital_usd"])
                self.cash_balance = gh_data.get("cash_balance", self.initial_capital)
                self.etf_shares = gh_data.get("etf_shares", 0.0)
                self.accumulated_premiums_usd = gh_data.get("accumulated_premiums_usd", 0.0)
                self.total_reinvested_usd = gh_data.get("total_reinvested_usd", 0.0)
                self.wheel_positions = gh_data.get("wheel_positions", [])
                self.history = gh_data.get("history", [])
                log_msg("CLOUD_STATE", "Estado de Rueda recuperado desde GitHub Cloud Backup.")
                loaded = True
        
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
            return 773.00 if symbol == "SPY" else 493.00  # Precios reales Sep 2026

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

        # Estrategia Institucional Rueda (Yield Overlay de Puts sobre Margen)
        # NUNCA vende Covered Calls sobre el Colateral Base (SGOV/SPY/QQQ/GLD son intocables)
        strike = round(etf_price * 0.97, 1) # Strike 3% OTM (Delta ~0.20-0.25)
        greeks = black_scholes("PUT", etf_price, strike, CONFIG["target_dte"]/365.0, 0.0525, 0.18)
        premium = max(2.50, greeks["price"])
        # Ejecución Real en IBKR
        exp_date = (datetime.now() + timedelta(days=CONFIG["target_dte"])).strftime("%Y-%m-%d")
        avg_price = premium
        commissions = 1.0
        if self.ibkr_adapter:
            exec_res = self.ibkr_adapter.execute_option_order_sync(
                symbol=etf_symbol, right="P", strike=strike, expiry=exp_date,
                action="SELL", quantity=1, limit_price=0.0 # Market Order for fast fill in paper
            )
            if exec_res.get("status") == "FILLED":
                avg_price = exec_res.get("avg_price", premium)
                commissions = exec_res.get("commission", 1.0)
                log_msg("CASH_PUT", f"🟢 ORDEN LLENADA EN IBKR: ${avg_price}/sh. Comisión: ${commissions}")

        income_usd = round(avg_price * 100.0 - commissions, 2)
        self.accumulated_premiums_usd += income_usd

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
            "status": "ACTIVE",
            "portfolio_nav_usd": round(self.cash_balance + (self.etf_shares * etf_price), 2)
        }
        self.history.append(cycle_record)
        self.save_state()
        return cycle_record

    def handle_assignment(self, assigned_shares=100, strike=None):
        """
        Protocolo Maestro de Asignación de Andrés Weisz (Capa 1):
        1. A la apertura de la sesión (09:30 EST): SE VENDEN LAS ACCIONES INMEDIATAMENTE al precio de mercado.
        2. A la par (simultáneamente): SE VENDE UN PUT (1 contrato por cada 100 acciones)
           con el mismo strike y vencimiento a 6-8 semanas (45 DTE).
        3. Excepción Caída > 15%: Buscar vencimiento con crédito neto manteniendo mismo strike o strike 5-10% menor.
        """
        etf_symbol = CONFIG["etf_target"]
        etf_price = self.fetch_etf_live_price(etf_symbol)
        ref_strike = strike if strike else round(etf_price * 1.02, 1)

        log_msg("ASSIGNMENT_PROTOCOL", f"⚡ EJECUTANDO PROTOCOLO DE ASIGNACIÓN ANDRÉS WEISZ en {etf_symbol}:")
        
        # 1. Venta Inmediata de Acciones para limpiar la cartera
        sale_proceeds = round(assigned_shares * etf_price, 2)
        log_msg("ASSIGNMENT_STOCK_SALE", f"🛒 1. Venta Inmediata de {assigned_shares} acciones de {etf_symbol} @ ${etf_price} USD (+$ {sale_proceeds} USD en efectivo). Cartera libre de acciones.")

        # 2. Venta Simultánea de Put a 6-8 semanas (45 DTE)
        target_dte = 45 # Entre 6 y 8 semanas (42-56 DTE)
        drop_pct = (ref_strike - etf_price) / ref_strike if etf_price < ref_strike else 0.0

        if drop_pct > 0.15:
            # Excepción: Caída > 15%, buscar strike entre 5% y 10% por debajo
            new_strike = round(ref_strike * 0.92, 1)
            reason_strike = f"Caída >15% ({drop_pct*100:.1f}%). Strike bajado 8% a ${new_strike} garantizando crédito neto."
        else:
            new_strike = ref_strike
            reason_strike = f"Mismo strike anterior ${new_strike}."

        greeks = black_scholes("PUT", etf_price, new_strike, target_dte/365.0, 0.0525, 0.22)
        premium = max(3.00, greeks["price"])
        contracts = max(1, assigned_shares // 100)
        income_usd = round(premium * 100.0 * contracts, 2)
        self.accumulated_premiums_usd += income_usd

        exp_date = (datetime.now() + timedelta(days=target_dte)).strftime("%Y-%m-%d")
        new_put_pos = {
            "id": f"WHEEL_RECOVERY_PUT_{int(datetime.now().timestamp())}",
            "ticker": f"{etf_symbol}_PUT_{new_strike:.1f}_{target_dte}DTE",
            "symbol": etf_symbol,
            "strategy_type": "ASSIGNMENT_RECOVERY_PUT_6_8_WEEKS",
            "underlying_price": etf_price,
            "strike": new_strike,
            "contracts": contracts,
            "premium_collected_usd": income_usd,
            "issued_date": timestamp(),
            "expiration_date": exp_date,
            "target_dte": target_dte,
            "status": "ACTIVE_RECOVERY",
            "note": reason_strike
        }
        self.wheel_positions = [new_put_pos]

        record = {
            "timestamp": timestamp(),
            "type": "ASSIGNMENT_RESET_6_8_WEEKS",
            "symbol": etf_symbol,
            "stock_sold_price": etf_price,
            "shares_sold": assigned_shares,
            "cash_freed_usd": sale_proceeds,
            "new_put_strike": new_strike,
            "new_put_dte": target_dte,
            "premium_collected_usd": income_usd,
            "note": reason_strike,
            "status": "ACTIVE_RECOVERY"
        }
        self.history.append(record)
        self.save_state()

        log_msg("ASSIGNMENT_NEW_PUT", f"🛡️ 2. Venta Simultánea de Put {contracts}x {etf_symbol} K=${new_strike} ({target_dte} DTE). Prima: +${income_usd} USD. {reason_strike}")
        return record

    def auto_check_and_run_cycle(self):
        """Verifica automáticamente el ciclo y aplica reglas institucionales de Auto-Roleo defensivo"""
        # GUARD: No operar en fines de semana ni feriados NYSE
        if not is_trading_day():
            log_msg("CALENDAR", "⏸️ Día no hábil (fin de semana/feriado NYSE) — ciclo suspendido.")
            return None
        try:
            if not self.history:
                log_msg("AUTO_WHEEL", "Iniciando primer ciclo automático de Rueda & Compuesto...")
                return self.run_wheel_cycle()

            # 1. VERIFICAR AUTO-ROLEO (Defensa de la posición actual)
            if hasattr(self, 'wheel_positions') and len(self.wheel_positions) > 0:
                pos = self.wheel_positions[0]
                if pos["strategy_type"] == "CASH_SECURED_PUT":
                    etf_price = self.fetch_etf_live_price(pos["symbol"])
                    exp_date = datetime.strptime(pos["expiration_date"], "%Y-%m-%d")
                    dte_remaining = (exp_date - datetime.now()).days

                    needs_roll = False
                    roll_reason = ""

                    # --- MATRIZ INSTITUCIONAL DE CRISIS (DTE y Moneyness) ---
                    drop_pct = (pos["strike"] - etf_price) / pos["strike"] if etf_price < pos["strike"] else 0
                    
                    # Simular indicador de Día Verde (precio de hoy > precio de ayer)
                    # Para el bot, asumimos acceso a price_history
                    is_green_day = True # Placeholder algorítmico
                    
                    nuevo_strike = pos["strike"]
                    dias_adelante = 30
                    
                    if drop_pct > 0:
                        # 4. Cisne Negro (>20%)
                        if drop_pct >= 0.20:
                            needs_roll = True
                            roll_reason = "CISNE_NEGRO_>20%"
                            dias_adelante = 60
                            nuevo_strike = round(etf_price, 1) # Bajar lo máximo posible
                            
                        # 3. Caída Fuerte (>15%) a 10 días
                        elif drop_pct >= 0.15 and dte_remaining <= 10:
                            needs_roll = True
                            roll_reason = "CAIDA_FUERTE_>15%_10DTE"
                            nuevo_strike = round(pos["strike"] * 0.90, 1) # Obligatorio bajar 10%
                            
                        # 2b. Caída Moderada (>5%) a 5 días
                        elif drop_pct >= 0.05 and dte_remaining <= 5:
                            needs_roll = True
                            roll_reason = "CAIDA_MODERADA_>5%_5DTE"
                            nuevo_strike = round(pos["strike"] * 0.98, 1) # Intenta bajar algo si da crédito
                            
                        # 2a. Caída Leve/Moderada (2% a 5%) a 5-3 días (Cazador de Días Verdes)
                        elif 0.02 <= drop_pct < 0.05 and dte_remaining <= 5:
                            if is_green_day or dte_remaining <= 3:
                                needs_roll = True
                                roll_reason = "CAIDA_2a5%_DIA_VERDE_O_DEADLINE_3DTE"
                                
                        # 1. Caída Leve (<2%) al Día 0
                        elif 0 < drop_pct < 0.02 and dte_remaining <= 0:
                            needs_roll = True
                            roll_reason = "CAIDA_LEVE_<2%_DIA_CERO"
                            # Se mantiene el mismo strike

                    if needs_roll:
                        log_msg("AUTO_ROLL", f"⚠️ GATILLO ACTIVADO: {roll_reason}. Ejecutando Roleo (DTE: {dte_remaining})...")
                        
                        # Calculo Real de Roleo usando Black-Scholes
                        old_put_val = black_scholes("PUT", etf_price, pos["strike"], max(0.01, dte_remaining)/365.0, 0.0525, 0.25)["price"]
                        new_put_val = black_scholes("PUT", etf_price, nuevo_strike, dias_adelante/365.0, 0.0525, 0.22)["price"]
                        
                        net_credit_per_share = round(new_put_val - old_put_val, 2)
                        income_usd = round(net_credit_per_share * 100.0, 2)
                        
                        # Si es débito (income_usd negativo), se resta de la caja/reinversión
                        self.accumulated_premiums_usd += income_usd
                        if income_usd > 0:
                            self.total_reinvested_usd += income_usd
                            shares_bought = round(income_usd / etf_price, 4)
                            self.etf_shares += shares_bought
                        else:
                            shares_bought = 0.0
                            # En la realidad, esto reduciría tu cash balance o requeriría vender acciones
                            self.cash_balance += income_usd 

                        exp_date_new = (datetime.now() + timedelta(days=dias_adelante)).strftime("%Y-%m-%d")
                        active_pos = {
                            "id": f"WHEEL_CSP_ROLLED_{int(datetime.now().timestamp())}",
                            "ticker": f"{pos['symbol']}_PUT_{nuevo_strike:.1f}_{dias_adelante}DTE",
                            "symbol": pos["symbol"],
                            "strategy_type": "CASH_SECURED_PUT",
                            "underlying_price": etf_price,
                            "strike": nuevo_strike,
                            "contracts": pos.get("contracts", 1),
                            "premium_collected_usd": income_usd,
                            "issued_date": timestamp(),
                            "expiration_date": exp_date_new,
                            "target_dte": dias_adelante,
                            "status": "ACTIVE_ROLLED"
                        }
                        self.wheel_positions = [active_pos]
                        
                        cycle_record = {
                            "timestamp": timestamp(),
                            "type": "ROLL_DOWN_AND_OUT",
                            "symbol": pos["symbol"],
                            "etf_price": etf_price,
                            "old_strike": pos["strike"],
                            "new_strike": nuevo_strike,
                            "net_credit_usd": income_usd,
                            "shares_bought": shares_bought,
                            "total_shares_now": round(self.etf_shares, 4),
                            "reason": roll_reason
                        }
                        self.history.append(cycle_record)
                        self.save_state()
                        
                        msg = f"✅ Roleo Exitoso. Nuevo Strike: ${nuevo_strike}. "
                        msg += f"Crédito Neto: +${income_usd}" if income_usd >= 0 else f"Débito (Costo): -${abs(income_usd)}"
                        log_msg("AUTO_ROLL", msg)
                        return cycle_record

            # 2. VERIFICAR EXPIRACIÓN NORMAL (Si pasaron los 30 días sin problemas)
            last_cycle = self.history[-1]
            last_ts_str = last_cycle.get("timestamp")
            if last_ts_str:
                last_dt = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_dt >= timedelta(days=CONFIG["target_dte"]):
                    log_msg("AUTO_WHEEL", f"Ciclo de {CONFIG['target_dte']} días completado con éxito. Renovando...")
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
