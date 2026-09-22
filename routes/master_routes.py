# -*- coding: utf-8 -*-
"""
routes/master_routes.py - Endpoints para Portfolio Master, Colateral, Reinversión y Engine
"""

import os
import json

def get_master_summary(ctx, query):
    summary = ctx["master_portfolio"].get_master_summary()
    summary["health_pings"] = ctx["health_pings"]
    return 200, summary

def get_collateral_status(ctx, query):
    summary = ctx["master_portfolio"].get_master_summary()
    return 200, summary.get("collateral_portfolio", {})

def get_reinvestment_status(ctx, query):
    return 200, ctx["master_portfolio"].get_reinvestment_status()

def post_reinvestment_execute(ctx, payload):
    master_portfolio = ctx["master_portfolio"]
    total = master_portfolio._get_total_premiums_collected()
    already = master_portfolio._reinvestment_state.get("total_reinvested_usd", 0.0)
    pending = round(total - already, 2)
    if pending <= 0:
        return 200, {"status": "NOTHING_PENDING", "pending_usd": pending}
    result = master_portfolio.check_and_execute_reinvestment()
    return 200, result

def get_etfs(ctx, query):
    etfs = ctx["engine"].fetch_live_etf_prices()
    return 200, etfs

def get_option_chain(ctx, query):
    symbol = query.get("symbol", ["SPY"])[0]
    dte = int(query.get("dte", [30])[0])
    chain_data = ctx["engine"].generate_option_chain(symbol, dte=dte)
    return 200, chain_data

def get_portfolio(ctx, query):
    engine = ctx["engine"]
    state = {
        "portfolio_capital": engine.portfolio_capital,
        "positions": engine.positions,
        "trade_history": engine.trade_history
    }
    return 200, state

def post_payoff(ctx, payload):
    legs = payload.get("legs", [])
    payoff = ctx["engine"].calculate_strategy_payoff(legs)
    return 200, payoff

def post_trade(ctx, payload):
    symbol = payload.get("symbol", "SPY")
    strategy = payload.get("strategy", "Estrategia Simulado Opciones")
    legs = payload.get("legs", [])
    if not legs:
        return 400, {"error": "Debe especificar al menos una leg (opción)"}
    trade = ctx["engine"].open_paper_trade(symbol, strategy, legs)
    return 200, {"status": "SUCCESS", "trade": trade}

def get_backtest_1y(ctx, query):
    bt_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backtest_results_1y.json")
    if os.path.exists(bt_file):
        with open(bt_file, "r", encoding="utf-8") as f:
            bt_data = json.load(f)
        return 200, bt_data
    else:
        from backtest_historical_1y import run_1y_backtest
        res = run_1y_backtest()
        return 200, res

MASTER_GET = {
    "/api/master/summary": get_master_summary,
    "/api/collateral/status": get_collateral_status,
    "/api/reinvestment/status": get_reinvestment_status,
    "/api/etfs": get_etfs,
    "/api/option-chain": get_option_chain,
    "/api/portfolio": get_portfolio,
    "/api/backtest/1y": get_backtest_1y
}

MASTER_POST = {
    "/api/reinvestment/execute": post_reinvestment_execute,
    "/api/payoff": post_payoff,
    "/api/trade": post_trade
}
