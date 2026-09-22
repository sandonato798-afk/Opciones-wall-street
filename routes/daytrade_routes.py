# -*- coding: utf-8 -*-
"""
routes/daytrade_routes.py - Endpoints para Capa 4: Daytrading Intradía ITM
"""

def get_daytrade_status(ctx, query):
    daytrade_bot = ctx["daytrade_bot"]
    daytrade_config = ctx["daytrade_config"]
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
        "config": daytrade_config,
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
    return 200, state

def post_daytrade_scan(ctx, payload):
    daytrade_bot = ctx["daytrade_bot"]
    daytrade_bot.scan_market()
    daytrade_bot.manage_open_position()
    return 200, {
        "status": "SUCCESS",
        "message": "Escaneo intradiario completado.",
        "active_trades": daytrade_bot.active_trades
    }

def post_daytrade_mode(ctx, payload):
    mode = payload.get("mode", "PAPER_TRADING")
    broker = payload.get("broker", "INTERACTIVE_BROKERS")
    ctx["daytrade_config"]["execution_mode"] = mode
    ctx["daytrade_config"]["broker_name"] = broker
    return 200, {"status": "SUCCESS", "mode": mode, "broker": broker}

DAYTRADE_GET = {
    "/api/daytrade/status": get_daytrade_status
}

DAYTRADE_POST = {
    "/api/daytrade/scan": post_daytrade_scan,
    "/api/daytrade/mode": post_daytrade_mode
}
