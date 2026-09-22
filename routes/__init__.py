# -*- coding: utf-8 -*-
"""
routes/__init__.py - Enrutador Central del Backend
Combina todos los endpoints modulares de las 5 capas y el Master Portfolio.
"""

from routes.master_routes import MASTER_GET, MASTER_POST
from routes.wheel_routes import WHEEL_GET, WHEEL_POST
from routes.alpha_routes import ALPHA_GET, ALPHA_POST
from routes.rsi_routes import RSI_GET, RSI_POST
from routes.daytrade_routes import DAYTRADE_GET, DAYTRADE_POST
from routes.bullmarket_routes import BULLMARKET_GET, BULLMARKET_POST

ALL_GET_ROUTES = {}
ALL_GET_ROUTES.update(MASTER_GET)
ALL_GET_ROUTES.update(WHEEL_GET)
ALL_GET_ROUTES.update(ALPHA_GET)
ALL_GET_ROUTES.update(RSI_GET)
ALL_GET_ROUTES.update(DAYTRADE_GET)
ALL_GET_ROUTES.update(BULLMARKET_GET)

ALL_POST_ROUTES = {}
ALL_POST_ROUTES.update(MASTER_POST)
ALL_POST_ROUTES.update(WHEEL_POST)
ALL_POST_ROUTES.update(ALPHA_POST)
ALL_POST_ROUTES.update(RSI_POST)
ALL_POST_ROUTES.update(DAYTRADE_POST)
ALL_POST_ROUTES.update(BULLMARKET_POST)

def dispatch_get(path, query, ctx):
    handler = ALL_GET_ROUTES.get(path)
    if handler:
        return handler(ctx, query)
    return None, None

def dispatch_post(path, payload, ctx):
    handler = ALL_POST_ROUTES.get(path)
    if handler:
        return handler(ctx, payload)
    return None, None
