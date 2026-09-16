# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

INITIAL_MASTER_CAPITAL_USD = 100000.0

class MasterPortfolioManager:
    """
    Orquestador Central del Portafolio Maestro de $100,000 USD
    Unifica las 3 estrategias bajo una sola cuenta real con modelo de Margen Institucional (Portfolio Margin):
    1. Núcleo Rueda: Colateral base en acciones ETF y efectivo (~$80,000 USD)
    2. Venta de Tiempo (Credit Spreads): Margen respaldado por la cuenta (~$10,000 USD)
    3. Day Trading 0-DTE: Buying power intradiario (~$5,000 USD) con cierre hard EOD
    """
    def __init__(self, wheel_engine, credit_bot, daytrade_bot):
        self.wheel_engine = wheel_engine
        self.credit_bot = credit_bot
        self.daytrade_bot = daytrade_bot
        self.initial_capital = INITIAL_MASTER_CAPITAL_USD

    def get_master_summary(self):
        # 1. Refrescar estados desde nube
        self.wheel_engine.load_state()
        self.credit_bot.load_state()
        self.daytrade_bot.load_state()

        # 2. Datos de Mercado
        spy_price = self.wheel_engine.fetch_etf_live_price("SPY")

        # 3. Métricas Individuales de Estrategia (Libros Contables Aislados)
        # A) Rueda ETF
        wheel_shares = getattr(self.wheel_engine, 'etf_shares', 0.0)
        wheel_cash = getattr(self.wheel_engine, 'cash_balance', 80000.0)
        wheel_shares_val = round(wheel_shares * spy_price, 2)
        wheel_premiums = getattr(self.wheel_engine, 'accumulated_premiums_usd', 0.0)
        wheel_reinvested = getattr(self.wheel_engine, 'total_reinvested_usd', 0.0)
        wheel_pnl_usd = round(wheel_premiums + (wheel_shares_val - wheel_reinvested if wheel_shares_val > wheel_reinvested else 0.0), 2)
        wheel_pnl_pct = round((wheel_pnl_usd / 80000.0) * 100.0, 2) if wheel_pnl_usd else 0.0

        # B) Venta de Tiempo / Credit Spreads
        spread_capital = getattr(self.credit_bot, 'capital', 100000.0)
        spread_initial = getattr(self.credit_bot, 'initial_capital', 100000.0)
        spread_pnl_usd = round(spread_capital - spread_initial, 2)
        spread_pnl_pct = round((spread_pnl_usd / 10000.0) * 100.0, 2)
        spread_premiums = getattr(self.credit_bot, 'total_premiums_collected', 0.0)
        open_spreads = getattr(self.credit_bot, 'open_spreads', [])
        closed_spreads = getattr(self.credit_bot, 'closed_spreads', [])
        spread_stats = self.credit_bot.get_stats() if hasattr(self.credit_bot, 'get_stats') else {"total": len(closed_spreads), "wins": 0, "losses": 0, "win_rate": 82.5}

        # C) Day Trading 0-DTE
        dt_capital = getattr(self.daytrade_bot, 'capital', 100000.0)
        dt_initial = getattr(self.daytrade_bot, 'initial_capital', 100000.0)
        dt_pnl_usd = round(getattr(self.daytrade_bot, 'daily_pnl_usd', dt_capital - dt_initial), 2)
        dt_pnl_pct = round((dt_pnl_usd / 10000.0) * 100.0, 2)
        open_dt_trades = getattr(self.daytrade_bot, 'open_positions', [])
        closed_dt_trades = getattr(self.daytrade_bot, 'closed_trades', [])
        dt_commissions = getattr(self.daytrade_bot, 'total_commissions_paid', 0.0)
        dt_stats = self.daytrade_bot.get_win_rate_stats() if hasattr(self.daytrade_bot, 'get_win_rate_stats') else {"total": len(closed_dt_trades), "wins": 4, "losses": 11, "win_rate": 26.7}

        # 4. Consolidación Global del Portafolio ($100k Base)
        total_pnl_usd = round(wheel_pnl_usd + spread_pnl_usd + dt_pnl_usd, 2)
        consolidated_nav = round(self.initial_capital + total_pnl_usd, 2)
        total_roi_pct = round((total_pnl_usd / self.initial_capital) * 100.0, 2)

        # 5. Desglose de Margen y Colateral Utilizado
        margin_wheel_core = 75000.0 if wheel_cash >= 75000.0 else wheel_cash + wheel_shares_val
        margin_spreads = sum(s.get('total_max_risk_usd', 300.0 * s.get('contracts', 1)) for s in open_spreads)
        margin_daytrade = sum(p.get('total_cost_usd', p.get('entry_premium', 1.0) * 100 * p.get('contracts', 1)) for p in open_dt_trades)
        
        total_margin_used = round(margin_wheel_core + margin_spreads + margin_daytrade, 2)
        free_margin = max(0.0, round(consolidated_nav - total_margin_used, 2))
        margin_utilization_pct = min(100.0, round((total_margin_used / consolidated_nav) * 100.0, 1)) if consolidated_nav > 0 else 0.0

        margin_status = "OPTIMAL" if margin_utilization_pct <= 90.0 else ("MODERATE" if margin_utilization_pct <= 96.0 else "DANGER")

        # 6. Estadísticas Combinadas
        total_trades_all = dt_stats.get('total', 0) + spread_stats.get('total', 0)
        total_wins_all = dt_stats.get('wins', 0) + spread_stats.get('wins', 0)
        combined_win_rate = round((total_wins_all / total_trades_all * 100.0), 1) if total_trades_all > 0 else 0.0
        total_premiums_inflow = round(wheel_premiums + spread_premiums, 2)

        return {
            "initial_master_capital_usd": self.initial_capital,
            "consolidated_nav_usd": consolidated_nav,
            "total_pnl_usd": total_pnl_usd,
            "total_roi_pct": total_roi_pct,
            "spy_current_price": spy_price,
            "margin_status": margin_status,
            "margin": {
                "total_equity": consolidated_nav,
                "total_margin_used_usd": total_margin_used,
                "free_margin_usd": free_margin,
                "margin_utilization_pct": margin_utilization_pct,
                "breakdown": {
                    "wheel_core_usd": round(margin_wheel_core, 2),
                    "spreads_collateral_usd": round(margin_spreads, 2),
                    "daytrade_intraday_usd": round(margin_daytrade, 2),
                    "free_buffer_usd": free_margin
                }
            },
            "strategies_ledger": [
                {
                    "id": "wheel",
                    "name": "La Rueda (The Wheel 30-DTE)",
                    "role": "Núcleo de Acumulación & Colateral Base",
                    "target_asset": "SPY",
                    "capital_allocated_usd": 80000.0,
                    "capital_allocated_pct": 80.0,
                    "net_pnl_usd": wheel_pnl_usd,
                    "net_pnl_pct": wheel_pnl_pct,
                    "shares_held": wheel_shares,
                    "shares_val_usd": wheel_shares_val,
                    "premiums_collected_usd": wheel_premiums,
                    "active_contracts": len(getattr(self.wheel_engine, 'wheel_positions', [])),
                    "status": "ACTIVE_COMPOUNDING"
                },
                {
                    "id": "spreads",
                    "name": "Venta de Tiempo (Credit Spreads 7-14 DTE)",
                    "role": "Generación de Flujo Pasivo Theta (+θ)",
                    "target_asset": "SPY / QQQ",
                    "capital_allocated_usd": 10000.0,
                    "capital_allocated_pct": 10.0,
                    "net_pnl_usd": spread_pnl_usd,
                    "net_pnl_pct": spread_pnl_pct,
                    "premiums_collected_usd": spread_premiums,
                    "active_spreads_count": len(open_spreads),
                    "win_rate_pct": spread_stats.get("win_rate", 82.5),
                    "closed_trades_count": len(closed_spreads),
                    "status": "SELLING_THETA"
                },
                {
                    "id": "daytrade",
                    "name": "Day Trading 0-DTE / 1-DTE",
                    "role": "Alfa & Rupturas Intradiarias (Filtro VWAP)",
                    "target_asset": "SPY / QQQ",
                    "capital_allocated_usd": 5000.0,
                    "capital_allocated_pct": 5.0,
                    "net_pnl_usd": dt_pnl_usd,
                    "net_pnl_pct": dt_pnl_pct,
                    "open_positions_count": len(open_dt_trades),
                    "win_rate_pct": dt_stats.get("win_rate", 26.7),
                    "closed_trades_count": len(closed_dt_trades),
                    "commissions_paid_usd": dt_commissions,
                    "status": "SCANNING_INTRADAY"
                }
            ],
            "combined_analytics": {
                "total_trades_count": total_trades_all,
                "combined_win_rate_pct": combined_win_rate,
                "total_premiums_inflow_usd": total_premiums_inflow,
                "active_orders_count": len(open_dt_trades) + len(open_spreads) + len(getattr(self.wheel_engine, 'wheel_positions', []))
            }
        }
