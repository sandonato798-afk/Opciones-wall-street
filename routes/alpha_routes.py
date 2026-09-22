# -*- coding: utf-8 -*-
"""
routes/alpha_routes.py - Endpoints para Capa 2: Alpha Sintéticos LEAPS Macro
"""

def get_alpha_status(ctx, query):
    return 200, ctx["alpha_bot"].get_status()

def post_alpha_decouple(ctx, payload):
    pos_id = int(payload.get("position_id", 0))
    available_funds = float(payload.get("available_funds_usd", 1000.0))
    res = ctx["alpha_bot"].decouple_short_put(pos_id, available_funds)
    return 200, res

ALPHA_GET = {
    "/api/alpha/status": get_alpha_status
}

ALPHA_POST = {
    "/api/alpha/decouple": post_alpha_decouple
}
