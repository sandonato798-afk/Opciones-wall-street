# -*- coding: utf-8 -*-
"""
routes/ibkr_routes.py - Endpoints de espejo directo del portfolio IBKR
Expone en vivo lo que la cuenta de Paper Trading tiene abierto.
"""


def _get_ibkr_positions(ctx, query):
    """
    GET /api/ibkr/positions
    Devuelve todas las posiciones reales de la cuenta IBKR Paper Trading.
    Espejo exacto de la pantalla de Portfolio en TWS / IB Gateway.
    """
    try:
        adapter = ctx.get("ibkr_adapter")
        if not adapter:
            return 500, {"error": "IBKR adapter no disponible"}

        positions = adapter.get_live_positions()
        summary = adapter.get_account_summary()
        heartbeat = adapter.ping_heartbeat()

        # Calcular totales desde posiciones reales
        total_unrealized = sum(p.get("unrealized_pnl", 0) for p in positions)
        total_realized = sum(p.get("realized_pnl", 0) for p in positions)
        total_market_value = sum(p.get("market_value", 0) for p in positions)

        # Separar acciones de opciones
        stocks = [p for p in positions if p.get("sec_type") == "STK"]
        options = [p for p in positions if p.get("sec_type") == "OPT"]

        return 200, {
            "ibkr_connected": heartbeat.get("status") == "ONLINE",
            "ibkr_latency_ms": heartbeat.get("latency_ms"),
            "last_sync": heartbeat.get("last_heartbeat"),
            "account": {
                "nav": summary.get("NetLiquidation", 0.0),
                "cash": summary.get("TotalCashValue", 0.0),
                "buying_power": summary.get("BuyingPower", 0.0),
                "available_funds": summary.get("AvailableFunds", 0.0),
                "unrealized_pnl": summary.get("UnrealizedPnL", 0.0),
                "realized_pnl": summary.get("RealizedPnL", 0.0),
            },
            "portfolio_totals": {
                "total_positions": len(positions),
                "total_stocks": len(stocks),
                "total_options": len(options),
                "total_market_value": round(total_market_value, 2),
                "total_unrealized_pnl": round(total_unrealized, 2),
                "total_realized_pnl": round(total_realized, 2),
            },
            "positions": positions,
            "stocks": stocks,
            "options": options,
        }

    except Exception as e:
        return 500, {"error": f"Error leyendo portfolio IBKR: {str(e)}"}


IBKR_GET = {
    "/api/ibkr/positions": _get_ibkr_positions,
}

IBKR_POST = {}
