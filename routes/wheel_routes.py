# -*- coding: utf-8 -*-
"""
routes/wheel_routes.py - Endpoints para Capa 1: La Rueda (Cash Secured Puts & Covered Calls)
"""

def get_wheel_status(ctx, query):
    wheel_engine = ctx["wheel_engine"]
    wheel_config = ctx["wheel_config"]
    etf_price = wheel_engine.fetch_etf_live_price(wheel_config["etf_target"])
    nav_usd = round(wheel_engine.cash_balance + (wheel_engine.etf_shares * etf_price), 2)
    cagr = round((((nav_usd / wheel_engine.initial_capital) ** 1) - 1) * 100.0, 2)

    state = {
        "config": wheel_config,
        "initial_capital_usd": wheel_engine.initial_capital,
        "cash_balance": wheel_engine.cash_balance,
        "etf_symbol": wheel_config["etf_target"],
        "etf_price": etf_price,
        "etf_shares": wheel_engine.etf_shares,
        "portfolio_nav_usd": nav_usd,
        "accumulated_premiums_usd": wheel_engine.accumulated_premiums_usd,
        "total_reinvested_usd": wheel_engine.total_reinvested_usd,
        "cagr_pct": cagr,
        "wheel_positions": wheel_engine.wheel_positions,
        "history": wheel_engine.history
    }
    return 200, state

def get_wheel_projections(ctx, query):
    projections = ctx["wheel_engine"].calculate_compounding_projections(years=10)
    return 200, projections

def post_wheel_run_cycle(ctx, payload):
    cycle_result = ctx["wheel_engine"].run_wheel_cycle()
    return 200, {"status": "SUCCESS", "cycle": cycle_result}

def post_wheel_transfer_profit(ctx, payload):
    amount = float(payload.get("amount_usd", 0.0))
    if amount <= 0:
        return 400, {"error": "Monto inválido"}
    res = ctx["wheel_engine"].transfer_profit_to_wheel(amount)
    return 200, {"status": "SUCCESS", "result": res}

WHEEL_GET = {
    "/api/wheel/status": get_wheel_status,
    "/api/wheel/projections": get_wheel_projections
}

WHEEL_POST = {
    "/api/wheel/run-cycle": post_wheel_run_cycle,
    "/api/wheel/transfer-profit": post_wheel_transfer_profit
}
