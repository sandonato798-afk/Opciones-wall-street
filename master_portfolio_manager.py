# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from cloud_persistence import sync_state_to_github_async, load_state_from_github

INITIAL_MASTER_CAPITAL_USD = 100000.0
REINVESTMENT_THRESHOLD_USD = 500.0   # Auto-ejecuta reinversión cuando hay $500+ acumulados
REINVESTMENT_STATE_FILE = "reinvestment_state.json"

# Colateral diversificado institucional: 100% del NAV distribuido en 5 bloques de activos
COLLATERAL_PORTFOLIO = {
    "TREASURY": {
        "pct": 0.40, "yield_apy": 0.051, "margin_req_pct": 2.0,
        "primary": "SGOV",
        "tickers": ["SGOV", "BOXX", "TBIL", "CSHI", "VTIP", "IBTG"],
        "description": "Bonos Tesoro 0-3M / BOXX (5.1% APY)"
    },
    "CORP_AAA": {
        "pct": 0.20, "yield_apy": 0.058, "margin_req_pct": 7.5,
        "primary": "IGSB",
        "tickers": ["IGSB", "VCSH", "PFF"],
        "description": "Bonos Corporativos AAA / Preferidas (5.8% APY)"
    },
    "SPY": {
        "pct": 0.20, "yield_apy": 0.015, "margin_req_pct": 15.0,
        "primary": "SPY",
        "tickers": ["SPY", "VOO"],
        "description": "S&P 500 Core Equity + Covered Calls"
    },
    "QQQ": {
        "pct": 0.15, "yield_apy": 0.008, "margin_req_pct": 15.0,
        "primary": "QQQ",
        "tickers": ["QQQ"],
        "description": "Nasdaq 100 Growth + LEAPS Overlay"
    },
    "GLD": {
        "pct": 0.05, "yield_apy": 0.045, "margin_req_pct": 15.0,
        "primary": "GLD",
        "tickers": ["GLD"],
        "description": "Oro Físico (Cobertura Inflación)"
    }
}

WHEEL_ALLOWED_UNIVERSE = [
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "asset_class": "Índice Núcleo EE.UU.",
        "strategy_mode": "CASH/MARGIN-SECURED PUT OVERLAY",
        "target_delta": "Δ 0.20 - 0.25 (3% OTM)",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "Respaldado por Pool Unificado (Colateral Intocable)",
        "status": "ACTIVE_PRIMARY"
    },
    {
        "symbol": "QQQ",
        "name": "Invesco QQQ (Nasdaq 100)",
        "asset_class": "MegaCap Tecnología",
        "strategy_mode": "CASH/MARGIN-SECURED PUT OVERLAY",
        "target_delta": "Δ 0.20 - 0.25 (3% OTM)",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "Respaldado por Pool Unificado (Colateral Intocable)",
        "status": "ACTIVE_SECONDARY"
    },
    {
        "symbol": "IWM",
        "name": "iShares Russell 2000 ETF",
        "asset_class": "Small Caps EE.UU.",
        "strategy_mode": "CASH/MARGIN-SECURED PUT OVERLAY",
        "target_delta": "Δ 0.20 (3.5% OTM)",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "Respaldado por Pool Unificado (Colateral Intocable)",
        "status": "READY_STANDBY"
    }
]

class MasterPortfolioManager:
    """
    Orquestador Central del Portafolio Maestro Hibrido ($100,000 USD)
    - 4 Capas de Opciones bajo Portfolio Margin
    - Tesoreria diversificada institucional:
      * 40% Bonos Tesoro (SGOV, BOXX, TBIL, CSHI, VTIP, IBTG)
      * 20% Bonos Corporativos AAA / Preferidas (IGSB, VCSH, PFF)
      * 20% SPY / VOO Core Equity
      * 15% QQQ Nasdaq Tech Growth
      * 5% GLD Oro Físico
    - Motor de Reinversion Automatica: 50% SGOV / 30% SPY / 20% Alpha decouple
    """
    def __init__(self, wheel_engine, alpha_bot, rsi_bot, daytrade_bot, bullmarket_bot=None):
        self.wheel_engine = wheel_engine
        self.alpha_bot = alpha_bot
        self.rsi_bot = rsi_bot
        self.daytrade_bot = daytrade_bot
        self.bullmarket_bot = bullmarket_bot
        self.initial_capital = INITIAL_MASTER_CAPITAL_USD
        self._reinvestment_state = self._load_reinvestment_state()

    # ─────────────────────────────────────────────────────────────────────────
    # REINVESTMENT STATE PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def _load_reinvestment_state(self):
        """Carga estado de reinversion desde nube o disco."""
        cloud = load_state_from_github(REINVESTMENT_STATE_FILE)
        if cloud:
            return cloud
        if os.path.exists(REINVESTMENT_STATE_FILE):
            try:
                with open(REINVESTMENT_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_reinvested_usd": 0.0,
            "treasury_accumulated_usd": INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["TREASURY"]["pct"],
            "corp_aaa_accumulated_usd": INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["CORP_AAA"]["pct"],
            "spy_accumulated_usd":      INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["SPY"]["pct"],
            "qqq_accumulated_usd":      INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["QQQ"]["pct"],
            "gld_accumulated_usd":      INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["GLD"]["pct"],
            "last_reinvestment_date": None,
            "reinvestment_count": 0,
            "reinvestment_history": []
        }

    def _save_reinvestment_state(self):
        self._reinvestment_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(REINVESTMENT_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._reinvestment_state, f, indent=2, ensure_ascii=False)
            sync_state_to_github_async(REINVESTMENT_STATE_FILE, self._reinvestment_state)
        except Exception as e:
            print(f"[REINVESTMENT] Error guardando estado: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # COLLATERAL PORTFOLIO — LIVE PRICES
    # ─────────────────────────────────────────────────────────────────────────

    def _fetch_collateral_prices(self, nav):
        """Obtiene precios en vivo de SGOV, IGSB, SPY, QQQ y GLD."""
        prices = {"SGOV": 100.5, "IGSB": 53.0, "SPY": 560.0, "QQQ": 485.0, "GLD": 235.0}
        for symbol in ["SGOV", "IGSB", "SPY", "QQQ", "GLD"]:
            try:
                price = self.wheel_engine.fetch_etf_live_price(symbol)
                if price and price > 0:
                    prices[symbol] = price
            except Exception:
                pass

        state = self._reinvestment_state
        collateral = {}
        for block_key, cfg in COLLATERAL_PORTFOLIO.items():
            primary_sym = cfg["primary"]
            target_usd = round(nav * cfg["pct"], 2)
            actual_usd = round(state.get(f"{block_key.lower()}_accumulated_usd", target_usd), 2)
            annual_yield = round(actual_usd * cfg["yield_apy"], 2)
            collateral[block_key] = {
                "block_key": block_key,
                "symbol": primary_sym,
                "tickers": cfg["tickers"],
                "description": cfg["description"],
                "target_pct": round(cfg["pct"] * 100, 0),
                "target_usd": target_usd,
                "actual_usd": actual_usd,
                "price": prices.get(primary_sym, 100.0),
                "shares_equiv": round(actual_usd / prices.get(primary_sym, 100.0), 4),
                "annual_yield_usd": annual_yield,
                "monthly_yield_usd": round(annual_yield / 12, 2),
                "margin_req_pct": cfg["margin_req_pct"],
                "collateral_unlocked_usd": round(actual_usd * (1 - cfg["margin_req_pct"] / 100), 2)
            }

        total_collateral_actual = sum(c["actual_usd"] for c in collateral.values())
        total_annual_yield      = sum(c["annual_yield_usd"] for c in collateral.values())
        total_unlocked_bp       = sum(c["collateral_unlocked_usd"] for c in collateral.values())

        return {
            "breakdown": collateral,
            "total_collateral_usd": round(total_collateral_actual, 2),
            "total_collateral_pct": round((total_collateral_actual / (nav or 1)) * 100, 1),
            "total_unlocked_buying_power_usd": round(total_unlocked_bp, 2),
            "total_annual_yield_usd": round(total_annual_yield, 2),
            "total_monthly_yield_usd": round(total_annual_yield / 12, 2)
        }

    # ─────────────────────────────────────────────────────────────────────────
    # REINVESTMENT ENGINE — REDISTRIBUCIÓN PROPORCIONAL COLATERAL (40/20/20/15/5)
    # ─────────────────────────────────────────────────────────────────────────

    def _get_total_premiums_collected(self):
        """
        Suma exclusivamente el beneficio neto REALIZADO de operaciones 100% CERRADAS.
        Regla de Liquidez de Andrés: Posiciones abiertas o con Roll activo mantienen su capital 
        en búfer de trading y NO se transfieren al colateral hasta que la posición cierre definitivamente.
        """
        # 1. Rueda: solo ciclos completados y cerrados
        wheel_premiums = 0.0
        if hasattr(self.wheel_engine, 'history') and self.wheel_engine.history:
            wheel_premiums = sum(c.get("premium_collected_usd", 0.0) for c in self.wheel_engine.history if c.get("status") in ["CLOSED", "EXPIRED", "COMPLETED"])
        if wheel_premiums == 0.0:
            wheel_premiums = getattr(self.wheel_engine, 'accumulated_premiums_usd', 0.0)
            
        # 2. RSI: trades cerrados en closed_trades
        rsi_premiums = sum(t.get("realized_pnl_usd", 0.0) for t in getattr(self.rsi_bot, 'closed_trades', []) if t.get("realized_pnl_usd", 0.0) > 0)
        
        # 3. Daytrade: solo posiciones cerradas con estatus CLOSED_* (si está ROLLED, sigue abierta)
        dt_pnl = sum(t.get("realized_pnl_usd", 0.0) for t in getattr(self.daytrade_bot, 'history', []) 
                     if t.get("status") in ["CLOSED_TAKE_PROFIT", "CLOSED_EXPIRED", "CLOSED_EOD_PROFIT"] and t.get("realized_pnl_usd", 0.0) > 0)
        
        # 4. Alpha: cash neto generado tras desacoplar (Free Runner)
        alpha_premiums = sum(p.get("net_cash_generated_usd", 0.0) for p in getattr(self.alpha_bot, 'decoupled_calls', []))
        
        # 5. Bull Market: theta cobrado realizado en short calls expirados o rolleados con éxito
        bm_theta = getattr(self.bullmarket_bot, 'realized_theta_usd', getattr(self.bullmarket_bot, 'total_theta_collected_usd', 0.0)) if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot else 0.0
        
        return round(wheel_premiums + rsi_premiums + dt_pnl + alpha_premiums + bm_theta, 2)

    def check_and_execute_reinvestment(self):
        """
        Llamado periódicamente desde el background loop.
        Si el beneficio neto realizado de posiciones cerradas supera el threshold ($500 USD),
        ejecuta la REDISTRIBUCIÓN PROPORCIONAL al 100% sobre los 5 activos del Portafolio Margin:
        - 40% Bonos del Tesoro (SGOV / T-Bills)
        - 20% Bonos Corporativos AAA Corto Plazo (IGSB)
        - 20% S&P 500 Core Equity (SPY)
        - 15% Nasdaq 100 Growth (QQQ)
        - 5%  Oro Físico (GLD)
        """
        total_premiums     = self._get_total_premiums_collected()
        already_reinvested = self._reinvestment_state.get("total_reinvested_usd", 0.0)
        pending            = round(total_premiums - already_reinvested, 2)

        if pending < REINVESTMENT_THRESHOLD_USD:
            return {
                "status": "WAITING",
                "pending_usd": pending,
                "threshold_usd": REINVESTMENT_THRESHOLD_USD,
                "needed_usd": round(REINVESTMENT_THRESHOLD_USD - pending, 2)
            }

        # ── Calcular la redistribución proporcional exacta ──────────────
        treasury_40 = round(pending * 0.40, 2)
        corp_aaa_20 = round(pending * 0.20, 2)
        spy_20      = round(pending * 0.20, 2)
        qqq_15      = round(pending * 0.15, 2)
        gld_5       = round(pending * 0.05, 2)

        print(f"[REINVESTMENT] 🏛️ Ejecutando redistribución proporcional al Colateral (${pending:.2f} USD): "
              f"Treasury 40%: ${treasury_40} | Corp AAA 20%: ${corp_aaa_20} | SPY 20%: ${spy_20} | QQQ 15%: ${qqq_15} | GLD 5%: ${gld_5}")

        # ── Acumular en las 5 posiciones del Colateral ────────────────────
        self._reinvestment_state["treasury_accumulated_usd"] = round(self._reinvestment_state.get("treasury_accumulated_usd", 40000.0) + treasury_40, 2)
        self._reinvestment_state["sgov_accumulated_usd"]     = self._reinvestment_state["treasury_accumulated_usd"]
        self._reinvestment_state["corp_aaa_accumulated_usd"] = round(self._reinvestment_state.get("corp_aaa_accumulated_usd", 20000.0) + corp_aaa_20, 2)
        self._reinvestment_state["spy_accumulated_usd"]      = round(self._reinvestment_state.get("spy_accumulated_usd", 20000.0) + spy_20, 2)
        self._reinvestment_state["qqq_accumulated_usd"]      = round(self._reinvestment_state.get("qqq_accumulated_usd", 15000.0) + qqq_15, 2)
        self._reinvestment_state["gld_accumulated_usd"]      = round(self._reinvestment_state.get("gld_accumulated_usd", 5000.0) + gld_5, 2)

        # ── Actualizar estado global ──────────────────────────────────────
        self._reinvestment_state["total_reinvested_usd"] = round(already_reinvested + pending, 2)
        self._reinvestment_state["reinvestment_count"]   = self._reinvestment_state.get("reinvestment_count", 0) + 1
        self._reinvestment_state["last_reinvestment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "date": self._reinvestment_state["last_reinvestment_date"],
            "total_reinvested_usd": pending,
            "method": "PROPORTIONAL_COLLATERAL_40_20_20_15_5",
            "breakdown": {
                "treasury_40_usd": treasury_40,
                "corp_aaa_20_usd": corp_aaa_20,
                "spy_20_usd": spy_20,
                "qqq_15_usd": qqq_15,
                "gld_5_usd": gld_5
            }
        }
        self._reinvestment_state.setdefault("reinvestment_history", []).append(record)
        self._save_reinvestment_state()

        return {"status": "EXECUTED", "record": record}

    def get_reinvestment_status(self):
        """Retorna el estado del motor de reinversion para el dashboard."""
        total_premiums    = self._get_total_premiums_collected()
        already_reinvested = self._reinvestment_state.get("total_reinvested_usd", 0.0)
        pending           = round(total_premiums - already_reinvested, 2)
        return {
            "total_premiums_collected_usd": total_premiums,
            "total_reinvested_usd": already_reinvested,
            "pending_reinvestment_usd": pending,
            "pending_alpha_decouple_usd": self._reinvestment_state.get("pending_alpha_decouple_usd", 0.0),
            "threshold_usd": REINVESTMENT_THRESHOLD_USD,
            "pct_to_threshold": min(100.0, round((pending / REINVESTMENT_THRESHOLD_USD) * 100, 1)),
            "reinvestment_count": self._reinvestment_state.get("reinvestment_count", 0),
            "last_reinvestment_date": self._reinvestment_state.get("last_reinvestment_date"),
            "last_10_events": self._reinvestment_state.get("reinvestment_history", [])[-10:]
        }

    # ─────────────────────────────────────────────────────────────────────────
    # MASTER SUMMARY
    # ─────────────────────────────────────────────────────────────────────────

    def get_master_summary(self):
        # 1. Refrescar estados
        self.wheel_engine.load_state()
        if hasattr(self.alpha_bot, 'load_state'):       self.alpha_bot.load_state()
        if hasattr(self.rsi_bot, 'load_state'):         self.rsi_bot.load_state()
        self.daytrade_bot.load_state()
        if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot:
            self.bullmarket_bot.load_state()

        # 2. Datos de Mercado
        spy_price = self.wheel_engine.fetch_etf_live_price("SPY")

        # 3. Metricas por Capa (con fallbacks a 0.0 limpios)
        wheel_shares    = getattr(self.wheel_engine, 'etf_shares', 0.0)
        wheel_shares_val = round(wheel_shares * spy_price, 2)
        wheel_premiums  = getattr(self.wheel_engine, 'accumulated_premiums_usd', 0.0)
        wheel_reinvested = getattr(self.wheel_engine, 'total_reinvested_usd', 0.0)
        # PnL real sin ocultar perdidas de acciones compradas
        wheel_pnl_usd   = round(wheel_premiums + (wheel_shares_val - wheel_reinvested), 2)

        alpha_status   = self.alpha_bot.get_status() if hasattr(self.alpha_bot, 'get_status') else {}
        alpha_pnl_usd  = alpha_status.get("total_unrealized_pnl_usd", 0.0)

        rsi_status     = self.rsi_bot.get_status() if hasattr(self.rsi_bot, 'get_status') else {}
        rsi_pnl_usd    = rsi_status.get("total_pnl_usd", 0.0)

        dt_history     = getattr(self.daytrade_bot, 'history', [])
        dt_active      = getattr(self.daytrade_bot, 'active_trades', [])
        dt_pnl_usd     = round(sum(t.get("realized_pnl_usd", 0) for t in dt_history), 2)
        dt_stats       = {"total": len(dt_history), "wins": sum(1 for t in dt_history if t.get("realized_pnl_usd", 0) > 0), "losses": sum(1 for t in dt_history if t.get("realized_pnl_usd", 0) < 0), "win_rate": 0.0}
        if dt_stats["total"] > 0:
            dt_stats["win_rate"] = round(dt_stats["wins"] / dt_stats["total"] * 100, 1)

        bm_status      = self.bullmarket_bot.get_status() if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot else {}
        bm_pnl_usd     = bm_status.get("total_pnl_usd", 0.0)

        # 4. NAV Consolidado & Analiticas de Rendimiento
        total_pnl_usd    = round(wheel_pnl_usd + alpha_pnl_usd + rsi_pnl_usd + dt_pnl_usd + bm_pnl_usd, 2)
        consolidated_nav = round(self.initial_capital + total_pnl_usd, 2)
        total_roi_pct    = round((total_pnl_usd / self.initial_capital) * 100.0, 2)

        SYSTEM_INCEPTION_DATE = "2026-09-15"
        try:
            inception_dt = datetime.strptime(SYSTEM_INCEPTION_DATE, "%Y-%m-%d")
            days_active = max(1, (datetime.now() - inception_dt).days)
        except Exception:
            days_active = 1
        months_active = max(1.0, days_active / 30.44)

        annualized_roi_pct = round((total_roi_pct / days_active) * 365, 2) if days_active > 0 else 0.0
        projected_monthly_usd = round(total_pnl_usd / months_active, 2)

        # Theta Diario Real calculado sobre posiciones de opciones verdaderas
        global_theta_usd = 0.0
        # Sumar Theta de la Rueda si hay opciones emitidas
        wheel_positions = getattr(self.wheel_engine, 'wheel_positions', [])
        for pos in wheel_positions:
            if pos.get("status") in ["OPEN", "ACTIVE"]:
                # Aproximacion de theta por contrato (~0.05 a 0.15 theta diario por accion)
                global_theta_usd += round(pos.get("contracts", 1) * 100 * 0.08, 2)
        # Sumar Theta de RSI bot si hay trades abiertos
        for trade in getattr(self.rsi_bot, 'open_trades', []):
            global_theta_usd += round(trade.get("contracts", 1) * 100 * 0.12, 2)
        # Sumar Theta de Bull Market PMCC (Short Call semanal activa)
        if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot:
            for diag in getattr(self.bullmarket_bot, 'open_diagonals', []):
                global_theta_usd += round(diag.get("short_call_contracts", 1) * 100 * 0.15, 2)

        # Profit Factor Real
        dt_gross_profit = sum(t.get("realized_pnl_usd", 0) for t in dt_history if t.get("realized_pnl_usd", 0) > 0)
        dt_gross_loss   = sum(t.get("realized_pnl_usd", 0) for t in dt_history if t.get("realized_pnl_usd", 0) < 0)
        
        gross_profit = (wheel_pnl_usd if wheel_pnl_usd > 0 else 0) + dt_gross_profit + (rsi_pnl_usd if rsi_pnl_usd > 0 else 0) + (bm_pnl_usd if bm_pnl_usd > 0 else 0)
        gross_loss = abs(dt_gross_loss) + abs(rsi_pnl_usd if rsi_pnl_usd < 0 else 0) + abs(wheel_pnl_usd if wheel_pnl_usd < 0 else 0)
        
        if gross_profit == 0 and gross_loss == 0:
            profit_factor = 0.0
        elif gross_loss == 0:
            profit_factor = "N/A"
        else:
            profit_factor = round(gross_profit / gross_loss, 2)

        # Max Drawdown historico real por High Water Mark (HWM)
        peak_nav = self._reinvestment_state.get("peak_nav_usd", self.initial_capital)
        if consolidated_nav > peak_nav:
            peak_nav = consolidated_nav
            self._reinvestment_state["peak_nav_usd"] = peak_nav
            self._save_reinvestment_state()

        drawdown_usd = peak_nav - consolidated_nav
        max_drawdown_pct = round((drawdown_usd / peak_nav) * -100.0, 2) if peak_nav > 0 else 0.0
        if max_drawdown_pct > 0:
            max_drawdown_pct = 0.0

        # 5. Colateral
        collateral_data = self._fetch_collateral_prices(consolidated_nav)

        # 6. Margen (sin spreads)
        margin_rsi       = 0.0 if rsi_status.get("status_mode") == "IDLE_MONITORING" else 5000.0
        margin_daytrade  = sum(p.get('strike', 500) * 100 * p.get('contracts', 1) * 0.20 for p in dt_active)
        margin_bullmkt   = sum(d.get("net_debit_paid_usd", 4000.0) for d in getattr(self.bullmarket_bot, "open_diagonals", [])) if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot else 0.0
        total_margin_used = round(margin_daytrade + margin_rsi + margin_bullmkt + 5000.0, 2)
        free_margin       = max(0.0, round(consolidated_nav - total_margin_used, 2))
        margin_util_pct   = min(100.0, round((total_margin_used / consolidated_nav) * 100.0, 1)) if consolidated_nav > 0 else 0.0
        margin_status     = "OPTIMAL" if margin_util_pct <= 65.0 else ("WARNING" if margin_util_pct <= 80.0 else "DANGER")

        # 7. Reinversion
        reinvestment_status = self.get_reinvestment_status()

        return {
            "initial_master_capital_usd": self.initial_capital,
            "consolidated_nav_usd": consolidated_nav,
            "total_pnl_usd": total_pnl_usd,
            "total_roi_pct": total_roi_pct,
            "performance_analytics": {
                "inception_date": SYSTEM_INCEPTION_DATE,
                "days_active": days_active,
                "months_active": round(months_active, 1),
                "annualized_roi_pct": annualized_roi_pct,
                "projected_monthly_usd": projected_monthly_usd,
                "global_theta_usd_per_day": global_theta_usd,
                "max_drawdown_pct": max_drawdown_pct,
                "profit_factor": profit_factor
            },
            "spy_current_price": spy_price,
            "margin_status": margin_status,
            "treasury_sgov": {
                "allocated_usd": collateral_data["breakdown"].get("TREASURY", {}).get("actual_usd", 40000.0),
                "annual_yield_pct": 5.1,
                "annual_yield_usd": collateral_data["breakdown"].get("TREASURY", {}).get("annual_yield_usd", 2040.0),
                "monthly_yield_usd": collateral_data["breakdown"].get("TREASURY", {}).get("monthly_yield_usd", 170.0),
                "margin_requirement_pct": 2.0,
                "available_collateral_unlocked_usd": collateral_data["breakdown"].get("TREASURY", {}).get("collateral_unlocked_usd", 39200.0)
            },
            "collateral_portfolio": collateral_data,
            "reinvestment_matrix_50_30_20": {
                "total_premiums_collected_usd": reinvestment_status["total_premiums_collected_usd"],
                "total_reinvested_usd": reinvestment_status["total_reinvested_usd"],
                "pending_usd": reinvestment_status["pending_reinvestment_usd"],
                "pending_alpha_decouple_usd": reinvestment_status.get("pending_alpha_decouple_usd", 0.0),
                "pct_to_threshold": reinvestment_status["pct_to_threshold"],
                "threshold_usd": REINVESTMENT_THRESHOLD_USD,
                "treasury_40_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.40, 2),
                "corp_aaa_20_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.20, 2),
                "spy_20_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.20, 2),
                "qqq_15_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.15, 2),
                "gld_5_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.05, 2),
                # Aliases para compatibilidad con vistas previas
                "sgov_treasury_50_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.40, 2),
                "spy_shares_30_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.20, 2),
                "alpha_decouple_20_usd": 0.0,
                "last_execution": reinvestment_status["last_reinvestment_date"],
                "execution_count": reinvestment_status["reinvestment_count"]
            },
            "margin": {
                "total_equity": consolidated_nav,
                "total_margin_used_usd": total_margin_used,
                "free_margin_usd": free_margin,
                "margin_utilization_pct": margin_util_pct,
                "max_allowed_margin_pct": 65.0,
                "status": margin_status,
                "breakdown": {
                    "wheel_overlay_nav_usd": consolidated_nav,
                    "alpha_trade_margin_usd": 12000.0,
                    "rsi_opportunistic_margin_usd": margin_rsi,
                    "daytrade_intraday_margin_usd": margin_daytrade,
                    "bullmarket_margin_usd": margin_bullmkt,
                    "free_buffer_usd": free_margin
                }
            },
            "strategies_ledger": [
                {
                    "id": "wheel", "name": "Capa 1: La Rueda (Overlay 100% Colateral)",
                    "role": "Overlay de Renta sobre Cartera & Compounding 100%",
                    "target_asset": "SPY / QQQ / GLD / TLT",
                    "capital_allocated_usd": consolidated_nav, "capital_allocated_pct": 100.0,
                    "net_pnl_usd": wheel_pnl_usd, "shares_held": wheel_shares,
                    "shares_val_usd": wheel_shares_val,
                    "premiums_collected_usd": wheel_premiums, "status": "ACTIVE_COMPOUNDING_OVERLAY"
                },
                {
                    "id": "alpha", "name": "Capa 2: Alpha LEAPS Macro (MAX DTE)",
                    "role": "Multiplicador Alcista Zero-Cost a 2 Años",
                    "target_asset": "SPY / QQQ / XLK / XLF / XLV",
                    "capital_allocated_usd": 40000.0, "capital_allocated_pct": 40.0,
                    "net_pnl_usd": alpha_pnl_usd,
                    "decoupled_calls_count": alpha_status.get("decoupled_calls_count", 0),
                    "status": "ZERO_COST_LEAP"
                },
                {
                    "id": "rsi_opportunistic", "name": "Capa 3: RSI Oportunista 1DTE",
                    "role": "Explotacion de Panico & Picos de IV (RSI < 25)",
                    "target_asset": "SPY / QQQ / DIA",
                    "capital_allocated_usd": 25000.0, "capital_allocated_pct": 25.0,
                    "net_pnl_usd": rsi_pnl_usd,
                    "status": rsi_status.get("status_mode", "IDLE_MONITORING")
                },
                {
                    "id": "daytrade", "name": "Capa 4: Day Trading ITM 1-DTE",
                    "role": "Scalp ITM por Rebote & Ruptura",
                    "target_asset": "SPY / QQQ",
                    "capital_allocated_usd": 15000.0, "capital_allocated_pct": 15.0,
                    "net_pnl_usd": dt_pnl_usd, "win_rate_pct": dt_stats.get("win_rate", 0.0),
                    "closed_trades_count": len(dt_history), "status": "SCANNING_INTRADAY"
                },
                {
                    "id": "bullmarket", "name": "Capa 5: Bull Market (PMCC Diagonal Alcista)",
                    "role": "Sustituto Sintético Acciones (Δ 0.80) + Venta Semanal Theta (Δ 0.20)",
                    "target_asset": "SPY / QQQ / GLD / IWM / TLT",
                    "capital_allocated_usd": 15000.0, "capital_allocated_pct": 15.0,
                    "net_pnl_usd": bm_pnl_usd,
                    "theta_income_usd": bm_status.get("total_theta_collected_usd", 0.0),
                    "active_diagonals_count": len(getattr(self.bullmarket_bot, "open_diagonals", [])) if hasattr(self, 'bullmarket_bot') and self.bullmarket_bot else 0,
                    "status": "ACTIVE_WEEKLY_ROLLS"
                }
            ],
            "wheel_allowed_universe": WHEEL_ALLOWED_UNIVERSE
        }

    def get_unified_margin_pool(self):
        """
        Retorna el estado en tiempo real del Pool Unificado de Margen al 100%.
        Utilizado por todos los bots para verificar el Buying Power libre disponible.
        """
        summary = self.get_master_summary()
        margin_info = summary.get("margin", {})
        return {
            "total_account_equity_usd": margin_info.get("total_equity", self.initial_capital),
            "total_margin_used_usd": margin_info.get("total_margin_used_usd", 0.0),
            "free_margin_available_usd": margin_info.get("free_margin_usd", self.initial_capital * 0.85),
            "margin_utilization_pct": margin_info.get("margin_utilization_pct", 0.0),
            "max_safe_utilization_pct": 65.0,
            "status": margin_info.get("status", "OPTIMAL")
        }
