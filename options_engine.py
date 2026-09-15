import math
import json
import os
import urllib.request
from datetime import datetime, timedelta

# File paths
STATE_FILE = os.path.join(os.path.dirname(__file__), "options_state.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "options_execution.log")

# Standard Wall Street ETFs for Options Trading
WALL_STREET_ETFS = {
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "default_iv": 0.16, "description": "Índice S&P 500 - Alta Liquidez"},
    "QQQ": {"name": "Invesco QQQ Trust (Nasdaq 100)", "default_iv": 0.22, "description": "Tecnología Nasdaq 100"},
    "IWM": {"name": "iShares Russell 2000 ETF", "default_iv": 0.24, "description": "Small Caps de EE.UU."},
    "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "default_iv": 0.18, "description": "Bonos del Tesoro de EE.UU. a Largo Plazo"},
    "GLD": {"name": "SPDR Gold Shares", "default_iv": 0.17, "description": "Oro Físico"}
}

def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution using math.erf"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def norm_pdf(x):
    """Probability density function for standard normal distribution"""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def black_scholes(option_type, S, K, T, r, sigma):
    """
    Calculates Black-Scholes option price and Greeks
    S: Underlying ETF Price
    K: Strike Price
    T: Time to Expiration in Years (DTE / 365.0)
    r: Risk-free Interest Rate (e.g., 0.0525 for 5.25%)
    sigma: Implied Volatility (e.g., 0.20 for 20%)
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {
            "price": max(0.0, S - K) if option_type.upper() == "CALL" else max(0.0, K - S),
            "delta": 1.0 if (option_type.upper() == "CALL" and S > K) else (0.0 if option_type.upper() == "CALL" else (-1.0 if S < K else 0.0)),
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0
        }

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    opt = option_type.upper()

    if opt == "CALL":
        price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        delta = norm_cdf(d1)
        theta = (- (S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365.0
        rho = (K * T * math.exp(-r * T) * norm_cdf(d2)) / 100.0
    else:  # PUT
        price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
        delta = norm_cdf(d1) - 1.0
        theta = (- (S * norm_pdf(d1) * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365.0
        rho = (-K * T * math.exp(-r * T) * norm_cdf(-d2)) / 100.0

    gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
    vega = (S * norm_pdf(d1) * math.sqrt(T)) / 100.0  # Per 1% change in IV

    return {
        "price": round(max(0.01, price), 2),
        "delta": round(delta, 4),
        "gamma": round(gamma, 4),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
        "rho": round(rho, 4)
    }

class OptionsTradingEngine:
    def __init__(self):
        self.risk_free_rate = 0.0525  # 5.25% Fed Rate
        self.portfolio_capital = 100000.0
        self.positions = []
        self.trade_history = []
        self.load_state()

    def log(self, tag, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{tag}] {message}"
        print(entry)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.portfolio_capital = data.get("portfolio_capital", 50000.0)
                    self.positions = data.get("positions", [])
                    self.trade_history = data.get("trade_history", [])
                    self.log("INFO", "Estado del Sistema de Opciones cargado exitosamente.")
                    return
            except Exception as e:
                self.log("WARN", f"Error al cargar estado ({e}). Inicializando valores por defecto.")
        self.save_state()

    def save_state(self):
        state = {
            "system": "SISTEMA_OPCIONES_ETFS_WALL_STREET",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "portfolio_capital": self.portfolio_capital,
            "positions": self.positions,
            "trade_history": self.trade_history
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def fetch_live_etf_prices(self):
        """Consulta cotizaciones reales en vivo de ETFs desde Yahoo Finance API"""
        prices = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        for symbol in WALL_STREET_ETFS.keys():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    meta = data["chart"]["result"][0]["meta"]
                    current_price = meta.get("regularMarketPrice", 0.0)
                    prev_close = meta.get("chartPreviousClose", current_price)
                    pct_change = ((current_price - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0
                    
                    prices[symbol] = {
                        "symbol": symbol,
                        "name": WALL_STREET_ETFS[symbol]["name"],
                        "description": WALL_STREET_ETFS[symbol]["description"],
                        "price": round(current_price, 2),
                        "prev_close": round(prev_close, 2),
                        "change_pct": round(pct_change, 2),
                        "iv_rank": round(45.0 + (hash(symbol) % 30), 1),  # Simulated IV Rank 30-75%
                        "implied_volatility": WALL_STREET_ETFS[symbol]["default_iv"]
                    }
            except Exception as e:
                self.log("WARN", f"Fallo consulta Yahoo Finance para {symbol}: {e}")
                # Fallback realistic pricing
                fallback_prices = {"SPY": 560.50, "QQQ": 485.20, "IWM": 220.10, "TLT": 98.40, "GLD": 232.80}
                prices[symbol] = {
                    "symbol": symbol,
                    "name": WALL_STREET_ETFS[symbol]["name"],
                    "description": WALL_STREET_ETFS[symbol]["description"],
                    "price": fallback_prices.get(symbol, 500.0),
                    "prev_close": fallback_prices.get(symbol, 500.0),
                    "change_pct": 0.25,
                    "iv_rank": 52.0,
                    "implied_volatility": WALL_STREET_ETFS[symbol]["default_iv"]
                }
        return prices

    def generate_option_chain(self, symbol, dte=30, strikes_count=7):
        """Genera la cadena de opciones (Calls & Puts) con griegas y primas reales"""
        etf_data = self.fetch_live_etf_prices().get(symbol)
        if not etf_data:
            return {}

        S = etf_data["price"]
        sigma = etf_data["implied_volatility"]
        T = max(1, dte) / 365.0
        r = self.risk_free_rate

        # Determine strike spacing based on ETF price
        if S > 400:
            step = 5.0
        elif S > 150:
            step = 2.5
        else:
            step = 1.0

        center_strike = round(S / step) * step
        strikes = [center_strike + (i - strikes_count // 2) * step for i in range(strikes_count)]

        chain = []
        for K in strikes:
            call_greeks = black_scholes("CALL", S, K, T, r, sigma)
            put_greeks = black_scholes("PUT", S, K, T, r, sigma)

            chain.append({
                "strike": K,
                "moneyness": "ITM" if S > K else ("ATM" if abs(S - K) < step / 2 else "OTM"),
                "call": {
                    "strike": K,
                    "bid": round(call_greeks["price"] * 0.98, 2),
                    "ask": round(call_greeks["price"] * 1.02, 2),
                    "last_price": call_greeks["price"],
                    "delta": call_greeks["delta"],
                    "gamma": call_greeks["gamma"],
                    "theta": call_greeks["theta"],
                    "vega": call_greeks["vega"],
                    "iv": round(sigma * 100, 1),
                    "open_interest": int(1200 + (K % 17) * 340)
                },
                "put": {
                    "strike": K,
                    "bid": round(put_greeks["price"] * 0.98, 2),
                    "ask": round(put_greeks["price"] * 1.02, 2),
                    "last_price": put_greeks["price"],
                    "delta": put_greeks["delta"],
                    "gamma": put_greeks["gamma"],
                    "theta": put_greeks["theta"],
                    "vega": put_greeks["vega"],
                    "iv": round(sigma * 100, 1),
                    "open_interest": int(950 + (K % 19) * 280)
                }
            })

        return {
            "symbol": symbol,
            "etf_price": S,
            "dte": dte,
            "expiration_date": (datetime.now() + timedelta(days=dte)).strftime("%Y-%m-%d"),
            "implied_volatility_pct": round(sigma * 100, 1),
            "iv_rank": etf_data["iv_rank"],
            "chain": chain
        }

    def calculate_strategy_payoff(self, legs, price_range_pct=0.15):
        """
        Calcula la curva de TyP (Profit/Loss at Expiration) para cualquier combinación de legs
        Leg format: {"action": "BUY"/"SELL", "type": "CALL"/"PUT", "strike": 560, "premium": 4.50, "qty": 1}
        """
        if not legs:
            return {"prices": [], "payoffs": []}

        strikes = [leg["strike"] for leg in legs]
        avg_strike = sum(strikes) / len(strikes) if strikes else 500.0

        min_price = avg_strike * (1.0 - price_range_pct)
        max_price = avg_strike * (1.0 + price_range_pct)
        steps = 50
        step_size = (max_price - min_price) / steps

        prices = [round(min_price + i * step_size, 2) for i in range(steps + 1)]
        payoffs = []

        max_profit = -float('inf')
        max_loss = float('inf')
        breakevens = []

        for p in prices:
            pnl = 0.0
            for leg in legs:
                qty = leg.get("qty", 1)
                action = leg["action"].upper() # BUY or SELL
                opt_type = leg["type"].upper() # CALL or PUT
                strike = leg["strike"]
                premium = leg["premium"]

                # Intrinsic value at expiration
                if opt_type == "CALL":
                    intrinsic = max(0.0, p - strike)
                else:
                    intrinsic = max(0.0, strike - p)

                if action == "BUY":
                    leg_pnl = (intrinsic - premium) * 100.0 * qty
                else: # SELL
                    leg_pnl = (premium - intrinsic) * 100.0 * qty

                pnl += leg_pnl

            payoffs.append(round(pnl, 2))
            if pnl > max_profit:
                max_profit = pnl
            if pnl < max_loss:
                max_loss = pnl

        # Find approximate breakevens
        for i in range(len(payoffs) - 1):
            if (payoffs[i] <= 0 and payoffs[i+1] >= 0) or (payoffs[i] >= 0 and payoffs[i+1] <= 0):
                breakevens.append(prices[i])

        return {
            "prices": prices,
            "payoffs": payoffs,
            "max_profit": round(max_profit, 2) if max_profit != float('inf') else "Ilimitado",
            "max_loss": round(max_loss, 2) if max_loss != -float('inf') else "Ilimitado",
            "breakevens": breakevens
        }

    def open_paper_trade(self, symbol, strategy_name, legs):
        """Abre una posición simulación de opciones en la cartera"""
        etf_prices = self.fetch_live_etf_prices()
        current_etf_price = etf_prices.get(symbol, {}).get("price", 500.0)

        # Compute net premium credit/debit
        net_premium = 0.0
        net_delta = 0.0
        net_theta = 0.0
        net_vega = 0.0

        for leg in legs:
            action = leg["action"].upper()
            premium = leg["premium"]
            qty = leg.get("qty", 1)
            greeks = black_scholes(leg["type"], current_etf_price, leg["strike"], leg.get("dte", 30)/365.0, self.risk_free_rate, 0.20)

            if action == "SELL":
                net_premium += premium * qty
                net_delta -= greeks["delta"] * qty * 100
                net_theta -= greeks["theta"] * qty * 100
                net_vega -= greeks["vega"] * qty * 100
            else:
                net_premium -= premium * qty
                net_delta += greeks["delta"] * qty * 100
                net_theta += greeks["theta"] * qty * 100
                net_vega += greeks["vega"] * qty * 100

        trade = {
            "id": int(datetime.now().timestamp()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "strategy": strategy_name,
            "underlying_entry_price": current_etf_price,
            "legs": legs,
            "net_premium_usd": round(net_premium * 100.0, 2), # 1 contract = 100 shares
            "type": "CREDIT" if net_premium >= 0 else "DEBIT",
            "greeks": {
                "delta": round(net_delta, 2),
                "theta": round(net_theta, 2),
                "vega": round(net_vega, 2)
            },
            "status": "OPEN",
            "floating_pnl_usd": 0.0
        }

        self.positions.append(trade)
        self.save_state()
        self.log("TRADE", f"Nueva posición abierta: [{symbol}] {strategy_name} | Prima Neta: ${trade['net_premium_usd']} USD")
        return trade
