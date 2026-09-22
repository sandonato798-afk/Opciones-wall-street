# -*- coding: utf-8 -*-
"""
routes/bullmarket_routes.py - Endpoints para Capa 5: Bull Market PMCC (Diagonal Spread Alcista)
"""

def get_bullmarket_status(ctx, query):
    bot = ctx["bullmarket_bot"]
    bot.load_state()
    return 200, bot.get_status()

def post_bullmarket_open(ctx, payload):
    res = ctx["bullmarket_bot"].scan_market()
    return 200, res

def post_bullmarket_roll(ctx, payload):
    bot = ctx["bullmarket_bot"]
    diag_id = int(payload.get("diagonal_id", 0))
    if not diag_id and bot.open_diagonals:
        diag_id = bot.open_diagonals[0]["id"]
    res = bot.roll_short_call(diag_id)
    return 200, res

BULLMARKET_GET = {
    "/api/bullmarket/status": get_bullmarket_status
}

BULLMARKET_POST = {
    "/api/bullmarket/open": post_bullmarket_open,
    "/api/bullmarket/roll": post_bullmarket_roll
}
