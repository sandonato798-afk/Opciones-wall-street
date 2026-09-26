# -*- coding: utf-8 -*-
"""
routes/history_routes.py - Endpoint de Historial Unificado de las 5 Capas
Combina todos los trades en un único timeline cronológico para auditoría y evaluación.
"""

import json
import os
from datetime import datetime

CAPA_NOMBRES = {
    1: "Rueda (Wheel)",
    2: "Alpha LEAPS",
    3: "RSI Oportunista",
    4: "Daytrade 1-DTE",
    5: "Bull Market PMCC"
}

CAPA_COLORES = {
    1: "green",
    2: "blue",
    3: "orange",
    4: "red",
    5: "purple"
}


def _parse_ts(ts_str):
    """Parsea timestamps en distintos formatos a datetime."""
    if not ts_str:
        return datetime.min
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts_str, fmt)
        except Exception:
            continue
    return datetime.min


def _get_wheel_trades(ctx):
    """Extrae historial de Capa 1: Rueda."""
    trades = []
    wheel = ctx.get("wheel_engine")
    if not wheel:
        return trades

    for rec in getattr(wheel, "history", []):
        t_type = rec.get("type", "")
        pnl = None
        status = "ACTIVE"

        if "CLOSED" in t_type or "PROFIT" in t_type:
            pnl = rec.get("premium_collected_usd", rec.get("net_credit_usd", 0))
            status = "CLOSED_PROFIT"
        elif "ROLL" in t_type:
            pnl = rec.get("net_credit_usd", 0)
            status = "ROLLED"
        elif "ASSIGNMENT" in t_type:
            status = "ASSIGNED"
        else:
            pnl = rec.get("premium_collected_usd", 0)
            status = "ACTIVE"

        trades.append({
            "id": rec.get("id", f"WHEEL_{rec.get('timestamp','')}"),
            "capa": 1,
            "capa_nombre": CAPA_NOMBRES[1],
            "capa_color": CAPA_COLORES[1],
            "tipo": t_type,
            "simbolo": rec.get("symbol", "SPY"),
            "strike": rec.get("strike", rec.get("new_put_strike")),
            "premium_usd": rec.get("premium_collected_usd", rec.get("net_credit_usd")),
            "pnl_usd": pnl,
            "estado": status,
            "timestamp": rec.get("timestamp", ""),
            "modo": "SIMULADO",
            "detalle": rec
        })

    for pos in getattr(wheel, "wheel_positions", []):
        trades.append({
            "id": pos.get("id", ""),
            "capa": 1,
            "capa_nombre": CAPA_NOMBRES[1],
            "capa_color": CAPA_COLORES[1],
            "tipo": pos.get("strategy_type", "CSP"),
            "simbolo": pos.get("symbol", "SPY"),
            "strike": pos.get("strike"),
            "premium_usd": pos.get("premium_collected_usd"),
            "pnl_usd": None,
            "estado": pos.get("status", "ACTIVE"),
            "timestamp": pos.get("issued_date", ""),
            "expiracion": pos.get("expiration_date"),
            "modo": "SIMULADO",
            "detalle": pos
        })

    return trades


def _get_alpha_trades(ctx):
    """Extrae historial de Capa 2: Alpha LEAPS."""
    trades = []
    alpha = ctx.get("alpha_bot")
    if not alpha:
        return trades

    for pos in getattr(alpha, "open_positions", []):
        trades.append({
            "id": str(pos.get("id", "")),
            "capa": 2,
            "capa_nombre": CAPA_NOMBRES[2],
            "capa_color": CAPA_COLORES[2],
            "tipo": pos.get("strategy", "ZERO_COST_SYNTHETIC"),
            "simbolo": pos.get("symbol", "QQQ"),
            "strike": pos.get("long_call_strike"),
            "premium_usd": pos.get("long_call_premium_paid"),
            "pnl_usd": pos.get("unrealized_pnl_usd"),
            "estado": pos.get("status", "ACTIVE"),
            "timestamp": pos.get("entry_date", ""),
            "modo": "SIMULADO",
            "detalle": pos
        })

    for pos in getattr(alpha, "decoupled_calls", []):
        trades.append({
            "id": str(pos.get("id", "")),
            "capa": 2,
            "capa_nombre": CAPA_NOMBRES[2],
            "capa_color": CAPA_COLORES[2],
            "tipo": "RISK_FREE_LONG_CALL",
            "simbolo": pos.get("symbol", "QQQ"),
            "strike": pos.get("long_call_strike"),
            "premium_usd": pos.get("long_call_premium_paid"),
            "pnl_usd": pos.get("unrealized_pnl_usd"),
            "estado": pos.get("status", "RISK_FREE"),
            "timestamp": pos.get("entry_date", ""),
            "modo": "SIMULADO",
            "detalle": pos
        })

    for pos in getattr(alpha, "closed_positions", []):
        trades.append({
            "id": str(pos.get("id", "")),
            "capa": 2,
            "capa_nombre": CAPA_NOMBRES[2],
            "capa_color": CAPA_COLORES[2],
            "tipo": "CLOSED_SYNTHETIC",
            "simbolo": pos.get("symbol", "QQQ"),
            "strike": pos.get("long_call_strike"),
            "premium_usd": pos.get("long_call_premium_paid"),
            "pnl_usd": pos.get("realized_pnl_usd", 0),
            "estado": "CLOSED",
            "timestamp": pos.get("close_date", pos.get("entry_date", "")),
            "modo": "SIMULADO",
            "detalle": pos
        })

    return trades


def _get_rsi_trades(ctx):
    """Extrae historial de Capa 3: RSI Oportunista."""
    trades = []
    rsi = ctx.get("rsi_bot")
    if not rsi:
        return trades

    for t in getattr(rsi, "open_trades", []):
        trades.append({
            "id": t.get("id", ""),
            "capa": 3,
            "capa_nombre": CAPA_NOMBRES[3],
            "capa_color": CAPA_COLORES[3],
            "tipo": "SHORT_PUT_1DTE",
            "simbolo": t.get("symbol", "SPY"),
            "strike": t.get("strike"),
            "premium_usd": t.get("premium_collected_usd"),
            "pnl_usd": t.get("unrealized_pnl_usd", 0),
            "estado": "ACTIVE",
            "timestamp": t.get("entry_time", t.get("timestamp", "")),
            "modo": "SIMULADO",
            "detalle": t
        })

    for t in getattr(rsi, "closed_trades", []):
        trades.append({
            "id": t.get("id", ""),
            "capa": 3,
            "capa_nombre": CAPA_NOMBRES[3],
            "capa_color": CAPA_COLORES[3],
            "tipo": t.get("close_reason", "CLOSED"),
            "simbolo": t.get("symbol", "SPY"),
            "strike": t.get("strike"),
            "premium_usd": t.get("premium_collected_usd"),
            "pnl_usd": t.get("pnl_usd", 0),
            "estado": "CLOSED_PROFIT" if t.get("pnl_usd", 0) > 0 else "CLOSED_LOSS",
            "timestamp": t.get("close_time", t.get("timestamp", "")),
            "modo": "SIMULADO",
            "detalle": t
        })

    return trades


def _get_daytrade_trades(ctx):
    """Extrae historial de Capa 4: Daytrade."""
    trades = []
    daytrade = ctx.get("daytrade_bot")
    if not daytrade:
        return trades

    for t in getattr(daytrade, "active_trades", []):
        trades.append({
            "id": t.get("id", ""),
            "capa": 4,
            "capa_nombre": CAPA_NOMBRES[4],
            "capa_color": CAPA_COLORES[4],
            "tipo": t.get("strategy", "ITM_PUT_1DTE"),
            "simbolo": t.get("symbol", "SPY"),
            "strike": t.get("strike"),
            "premium_usd": t.get("premium_collected_usd"),
            "pnl_usd": t.get("unrealized_pnl_usd", 0),
            "estado": "ACTIVE",
            "timestamp": t.get("entry_date", t.get("timestamp", "")),
            "modo": "SIMULADO",
            "detalle": t
        })

    for t in getattr(daytrade, "history", []):
        pnl = t.get("pnl_usd", t.get("net_pnl_usd", 0))
        trades.append({
            "id": t.get("id", f"DAY_{t.get('timestamp','')}"),
            "capa": 4,
            "capa_nombre": CAPA_NOMBRES[4],
            "capa_color": CAPA_COLORES[4],
            "tipo": t.get("close_reason", t.get("type", "CLOSED")),
            "simbolo": t.get("symbol", "SPY"),
            "strike": t.get("strike"),
            "premium_usd": t.get("premium_collected_usd"),
            "pnl_usd": pnl,
            "estado": "CLOSED_PROFIT" if pnl and pnl > 0 else "CLOSED_LOSS",
            "timestamp": t.get("close_date", t.get("timestamp", "")),
            "modo": "SIMULADO",
            "detalle": t
        })

    return trades


def _get_bullmarket_trades(ctx):
    """Extrae historial de Capa 5: Bull Market PMCC."""
    trades = []
    bull = ctx.get("bullmarket_bot")
    if not bull:
        return trades

    for d in getattr(bull, "open_diagonals", []):
        trades.append({
            "id": d.get("id", ""),
            "capa": 5,
            "capa_nombre": CAPA_NOMBRES[5],
            "capa_color": CAPA_COLORES[5],
            "tipo": "PMCC_DIAGONAL",
            "simbolo": d.get("symbol", "SPY"),
            "strike": d.get("long_call_strike"),
            "premium_usd": d.get("long_call_premium_paid"),
            "pnl_usd": d.get("long_call_unrealized_pnl_usd", 0),
            "estado": "ACTIVE",
            "timestamp": d.get("entry_date", ""),
            "modo": "SIMULADO",
            "detalle": d
        })

    for roll in getattr(bull, "weekly_rolls_history", []):
        pnl = roll.get("net_theta_profit_usd", 0)
        trades.append({
            "id": f"BULL_ROLL_{roll.get('trade_id','')}_C{roll.get('cycle_num','')}",
            "capa": 5,
            "capa_nombre": CAPA_NOMBRES[5],
            "capa_color": CAPA_COLORES[5],
            "tipo": "SHORT_CALL_ROLL",
            "simbolo": roll.get("symbol", "SPY"),
            "strike": roll.get("short_strike"),
            "premium_usd": roll.get("premium_collected_usd"),
            "pnl_usd": pnl,
            "estado": roll.get("status", "ROLLED"),
            "timestamp": roll.get("roll_date", ""),
            "modo": "SIMULADO",
            "detalle": roll
        })

    return trades


def get_unified_history(ctx, query):
    """
    GET /api/history/unified
    Retorna el timeline completo de las 5 capas, ordenado por fecha descendente.
    Incluye resumen global de PnL, win rate y métricas por capa.
    """
    all_trades = []
    all_trades.extend(_get_wheel_trades(ctx))
    all_trades.extend(_get_alpha_trades(ctx))
    all_trades.extend(_get_rsi_trades(ctx))
    all_trades.extend(_get_daytrade_trades(ctx))
    all_trades.extend(_get_bullmarket_trades(ctx))

    # Ordenar cronológicamente (más reciente primero)
    all_trades.sort(key=lambda t: _parse_ts(t.get("timestamp", "")), reverse=True)

    # Filtros opcionales por query params
    filtro_capa = query.get("capa", [None])[0]
    filtro_estado = query.get("estado", [None])[0]
    filtro_simbolo = query.get("simbolo", [None])[0]

    if filtro_capa:
        try:
            all_trades = [t for t in all_trades if t["capa"] == int(filtro_capa)]
        except Exception:
            pass
    if filtro_estado:
        all_trades = [t for t in all_trades if filtro_estado.upper() in t["estado"].upper()]
    if filtro_simbolo:
        all_trades = [t for t in all_trades if t["simbolo"] == filtro_simbolo.upper()]

    # Métricas globales
    trades_con_pnl = [t for t in all_trades if t.get("pnl_usd") is not None]
    cerrados = [t for t in trades_con_pnl if "CLOSED" in t["estado"] or "ROLLED" in t["estado"]]
    ganadores = [t for t in cerrados if (t.get("pnl_usd") or 0) > 0]
    pnl_total = sum(t.get("pnl_usd") or 0 for t in cerrados)
    win_rate = round(len(ganadores) / len(cerrados) * 100, 1) if cerrados else 0.0

    # Resumen por capa
    por_capa = {}
    for capa_num in range(1, 6):
        capa_trades = [t for t in all_trades if t["capa"] == capa_num]
        capa_cerrados = [t for t in capa_trades if "CLOSED" in t.get("estado", "") or "ROLLED" in t.get("estado", "")]
        capa_pnl = sum(t.get("pnl_usd") or 0 for t in capa_cerrados)
        capa_ganadores = [t for t in capa_cerrados if (t.get("pnl_usd") or 0) > 0]
        por_capa[str(capa_num)] = {
            "nombre": CAPA_NOMBRES[capa_num],
            "color": CAPA_COLORES[capa_num],
            "total_trades": len(capa_trades),
            "trades_activos": len([t for t in capa_trades if "ACTIVE" in t.get("estado", "")]),
            "trades_cerrados": len(capa_cerrados),
            "pnl_neto_usd": round(capa_pnl, 2),
            "win_rate_pct": round(len(capa_ganadores) / len(capa_cerrados) * 100, 1) if capa_cerrados else 0.0
        }

    return 200, {
        "trades": all_trades,
        "resumen": {
            "total_trades": len(all_trades),
            "trades_activos": len([t for t in all_trades if "ACTIVE" in t.get("estado", "")]),
            "trades_cerrados": len(cerrados),
            "pnl_neto_usd": round(pnl_total, 2),
            "win_rate_pct": win_rate,
            "por_capa": por_capa
        }
    }


HISTORY_GET = {
    "/api/history/unified": get_unified_history,
}
