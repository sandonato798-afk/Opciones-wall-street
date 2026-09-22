# -*- coding: utf-8 -*-
"""
routes/rsi_routes.py - Endpoints para Capa 3: RSI Oportunista 1DTE
"""

def get_rsi_status(ctx, query):
    return 200, ctx["rsi_bot"].get_status()

RSI_GET = {
    "/api/rsi-opportunistic/status": get_rsi_status
}

RSI_POST = {}
