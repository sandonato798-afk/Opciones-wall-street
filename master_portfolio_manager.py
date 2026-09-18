# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from cloud_persistence import sync_state_to_github_async, load_state_from_github

INITIAL_MASTER_CAPITAL_USD = 100000.0
REINVESTMENT_THRESHOLD_USD = 500.0   # Auto-ejecuta reinversión cuando hay $500+ acumulados
REINVESTMENT_STATE_FILE = "reinvestment_state.json"

# Colateral diversificado: 100% del NAV distribuido en activos remunerados y descorrelacionados
COLLATERAL_PORTFOLIO = {
    "SGOV": {"pct": 0.50, "yield_apy": 0.052, "margin_req_pct": 2.0,
             "description": "T-Bills 0-3M (5.2% APY Garantizado)"},
    "GLD":  {"pct": 0.25, "yield_apy": 0.045, "margin_req_pct": 15.0,
             "description": "Gold ETF + Covered Calls (4.5% APY)"},
    "TLT":  {"pct": 0.15, "yield_apy": 0.043, "margin_req_pct": 10.0,
             "description": "Bonos 20Y + Covered Calls (4.3% APY)"},
    "SPY":  {"pct": 0.10, "yield_apy": 0.015, "margin_req_pct": 15.0,
             "description": "S&P 500 Equity en Cartera + Dividendos"}
}

WHEEL_ALLOWED_UNIVERSE = [
    {
        "symbol": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "asset_class": "Índice Núcleo (Core Equity)",
        "strategy_mode": "CASH_SECURED_PUT / COVERED_CALL",
        "target_delta": "Δ 0.20 - 0.25",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "100% Respaldado por SGOV T-Bills",
        "status": "ACTIVE_PRIMARY"
    },
    {
        "symbol": "QQQ",
        "name": "Invesco QQQ (Nasdaq 100)",
        "asset_class": "MegaCap Tecnología",
        "strategy_mode": "CASH_SECURED_PUT / COVERED_CALL",
        "target_delta": "Δ 0.20 - 0.25",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "100% Respaldado por SGOV T-Bills",
        "status": "ACTIVE_SECONDARY"
    },
    {
        "symbol": "GLD",
        "name": "SPDR Gold Shares",
        "asset_class": "Oro Físico (Hedge Inflación)",
        "strategy_mode": "COVERED_CALL SOBRE TENENCIA",
        "target_delta": "Δ 0.25 - 0.30",
        "target_dte": "30 Días",
        "collateral_backing": "Cuotas de GLD en Cartera",
        "status": "ACTIVE_YIELD_BOOST"
    },
    {
        "symbol": "TLT",
        "name": "iShares 20+ Year Treasury Bond",
        "asset_class": "Bonos del Tesoro 20Y",
        "strategy_mode": "COVERED_CALL SOBRE TENENCIA",
        "target_delta": "Δ 0.25 - 0.30",
        "target_dte": "30 Días",
        "collateral_backing": "Cuotas de TLT en Cartera",
        "status": "ACTIVE_YIELD_BOOST"
    },
    {
        "symbol": "IWM",
        "name": "iShares Russell 2000 ETF",
        "asset_class": "Small Caps EE.UU.",
        "strategy_mode": "CASH_SECURED_PUT",
        "target_delta": "Δ 0.20",
        "target_dte": "30 - 45 Días",
        "collateral_backing": "Margen Libre Disponible",
        "status": "READY_STANDBY"
    }
]

class MasterPortfolioManager:
    """
    Orquestador Central del Portafolio Maestro Hibrido ($100,000 USD)
    - 4 Capas de Opciones bajo Portfolio Margin
    - Tesoreria diversificada: SGOV (30%) + GLD (20%) + TLT (10%)
    - Motor de Reinversion Automatica: 50% SGOV / 30% SPY / 20% Alpha decouple
    - Capa 1: La Rueda (Overlay 100% NAV)
    - Capa 2: Alpha LEAPS Macro (MAX DTE, indices + sectoriales)
    - Capa 3: RSI Oportunista (Naked Put 1DTE, RSI<25)
    - Capa 4: Daytrading ITM (Put +1%, 1DTE, TP 50%)
    """
    def __init__(self, wheel_engine, alpha_bot, rsi_bot, daytrade_bot):
        self.wheel_engine = wheel_engine
        self.alpha_bot = alpha_bot
        self.rsi_bot = rsi_bot
        self.daytrade_bot = daytrade_bot
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
            "sgov_accumulated_usd": INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["SGOV"]["pct"],
            "gld_accumulated_usd":  INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["GLD"]["pct"],
            "tlt_accumulated_usd":  INITIAL_MASTER_CAPITAL_USD * COLLATERAL_PORTFOLIO["TLT"]["pct"],
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
        """Obtiene precios en vivo de GLD y TLT. SGOV ~ $100 estable."""
        prices = {"SGOV": 100.0, "GLD": 230.0, "TLT": 95.0}
        for symbol in ["GLD", "TLT"]:
            try:
                price = self.wheel_engine.fetch_etf_live_price(symbol)
                if price and price > 0:
                    prices[symbol] = price
            except Exception:
                pass

        state = self._reinvestment_state
        collateral = {}
        for sym, cfg in COLLATERAL_PORTFOLIO.items():
            target_usd = round(nav * cfg["pct"], 2)
            actual_usd = round(state.get(f"{sym.lower()}_accumulated_usd", target_usd), 2)
            annual_yield = round(actual_usd * cfg["yield_apy"], 2)
            collateral[sym] = {
                "symbol": sym,
                "description": cfg["description"],
                "target_pct": round(cfg["pct"] * 100, 0),
                "target_usd": target_usd,
                "actual_usd": actual_usd,
                "price": prices[sym],
                "shares_equiv": round(actual_usd / prices[sym], 4),
                "annual_yield_usd": annual_yield,
                "monthly_yield_usd": round(annual_yield / 12, 2),
                "margin_req_pct": cfg["margin_req_pct"],
                "collateral_unlocked_usd": round(actual_usd * (1 - cfg["margin_req_pct"] / 100), 2)
            }

        total_collateral_usd = sum(c["actual_usd"] for c in collateral.values())
        total_unlocked_usd   = sum(c["collateral_unlocked_usd"] for c in collateral.values())
        total_yield_annual   = sum(c["annual_yield_usd"] for c in collateral.values())

        return {
            "breakdown": collateral,
            "total_collateral_usd": round(total_collateral_usd, 2),
            "total_collateral_pct": round((total_collateral_usd / nav) * 100, 1) if nav > 0 else 60.0,
            "total_unlocked_buying_power_usd": round(total_unlocked_usd, 2),
            "total_annual_yield_usd": round(total_yield_annual, 2),
            "total_monthly_yield_usd": round(total_yield_annual / 12, 2),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # AUTOMATIC REINVESTMENT ENGINE
    # ─────────────────────────────────────────────────────────────────────────

    def _get_total_premiums_collected(self):
        """Suma todas las primas brutas generadas por las 4 capas."""
        wheel_premiums   = getattr(self.wheel_engine, 'accumulated_premiums_usd', 0.0)
        rsi_premiums     = getattr(self.rsi_bot, 'total_premiums_collected', 0.0)
        dt_pnl           = sum(t.get("realized_pnl_usd", 0) for t in getattr(self.daytrade_bot, 'history', []) if t.get("realized_pnl_usd", 0) > 0)
        return round(wheel_premiums + rsi_premiums + dt_pnl, 2)

    def check_and_execute_reinvestment(self):
        """
        Llamado cada 60s desde el background loop.
        Si las primas nuevas acumuladas superan el threshold de $500,
        ejecuta automaticamente el split 50/30/20.
        """
        total_premiums    = self._get_total_premiums_collected()
        already_reinvested = self._reinvestment_state.get("total_reinvested_usd", 0.0)
        pending           = round(total_premiums - already_reinvested, 2)

        if pending < REINVESTMENT_THRESHOLD_USD:
            return {
                "status": "WAITING",
                "pending_usd": pending,
                "threshold_usd": REINVESTMENT_THRESHOLD_USD,
                "needed_usd": round(REINVESTMENT_THRESHOLD_USD - pending, 2)
            }

        # ── Calcular el split ──────────────────────────────────────────────
        sgov_50 = round(pending * 0.50, 2)
        spy_30  = round(pending * 0.30, 2)
        alpha_20 = round(pending * 0.20, 2)

        print(f"[REINVESTMENT] Ejecutando reinversion de ${pending:.2f} "
              f"→ SGOV: ${sgov_50} | SPY: ${spy_30} | Alpha: ${alpha_20}")

        # ── 30% → Comprar acciones SPY via Rueda ──────────────────────────
        wheel_result = None
        try:
            wheel_result = self.wheel_engine.transfer_profit_to_wheel(spy_30)
            print(f"[REINVESTMENT] SPY +{wheel_result.get('shares_bought', 0):.4f} shares compradas via Rueda.")
        except Exception as e:
            print(f"[REINVESTMENT] Error transfiriendo a Rueda: {e}")

        # ── 20% → Intentar decouple de Alpha Trade ────────────────────────
        alpha_result = None
        try:
            for pos in getattr(self.alpha_bot, 'open_positions', []):
                if not pos.get("decoupled"):
                    buyback_cost = pos.get("short_put_current_buyback_cost", 9999.0)
                    if alpha_20 >= buyback_cost:
                        alpha_result = self.alpha_bot.decouple_short_put(pos["id"], alpha_20)
                        print(f"[REINVESTMENT] Alpha decouple ejecutado: {alpha_result.get('message','')}")
                    else:
                        print(f"[REINVESTMENT] Alpha: fondos insuficientes (${alpha_20:.0f} vs "
                              f"${buyback_cost:.0f} requeridos). Acumulando para proximo ciclo.")
                    break
        except Exception as e:
            print(f"[REINVESTMENT] Error en decouple Alpha: {e}")

        # ── 50% → Registrar incremento en SGOV ───────────────────────────
        self._reinvestment_state["sgov_accumulated_usd"] = round(
            self._reinvestment_state.get("sgov_accumulated_usd", 30000.0) + sgov_50, 2)

        # ── Actualizar estado ─────────────────────────────────────────────
        self._reinvestment_state["total_reinvested_usd"] = round(already_reinvested + pending, 2)
        self._reinvestment_state["reinvestment_count"]   = self._reinvestment_state.get("reinvestment_count", 0) + 1
        self._reinvestment_state["last_reinvestment_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "date": self._reinvestment_state["last_reinvestment_date"],
            "total_reinvested_usd": pending,
            "sgov_50_usd": sgov_50,
            "spy_30_usd": spy_30,
            "alpha_20_usd": alpha_20,
            "wheel_shares_bought": wheel_result.get("shares_bought", 0) if wheel_result else 0,
            "alpha_decoupled": alpha_result.get("success", False) if alpha_result else False
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
        if hasattr(self.alpha_bot, 'load_state'):   self.alpha_bot.load_state()
        if hasattr(self.rsi_bot, 'load_state'):     self.rsi_bot.load_state()
        self.daytrade_bot.load_state()

        # 2. Datos de Mercado
        spy_price = self.wheel_engine.fetch_etf_live_price("SPY")

        # 3. Metricas por Capa
        wheel_shares    = getattr(self.wheel_engine, 'etf_shares', 0.7579)
        wheel_shares_val = round(wheel_shares * spy_price, 2)
        wheel_premiums  = getattr(self.wheel_engine, 'accumulated_premiums_usd', 574.0)
        wheel_reinvested = getattr(self.wheel_engine, 'total_reinvested_usd', 574.0)
        wheel_pnl_usd   = round(wheel_premiums + max(0.0, wheel_shares_val - wheel_reinvested), 2)

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

        # 4. NAV Consolidado & Analiticas de Rendimiento
        total_pnl_usd    = round(wheel_pnl_usd + alpha_pnl_usd + rsi_pnl_usd + dt_pnl_usd, 2)
        consolidated_nav = round(self.initial_capital + total_pnl_usd, 2)
        total_roi_pct    = round((total_pnl_usd / self.initial_capital) * 100.0, 2)

        SYSTEM_INCEPTION_DATE = "2026-09-15"
        inception_dt = datetime.strptime(SYSTEM_INCEPTION_DATE, "%Y-%m-%d")
        days_active = max(1, (datetime.now() - inception_dt).days)
        months_active = max(1.0, days_active / 30.44)

        annualized_roi_pct = round((total_roi_pct / days_active) * 365, 2) if days_active > 0 else 0.0
        projected_monthly_usd = round(total_pnl_usd / months_active, 2)

        wheel_theta = wheel_premiums / 45.0
        global_theta_usd = round(wheel_theta, 2)

        gross_profit = wheel_pnl_usd + (dt_stats["wins"] * 450) + (rsi_pnl_usd if rsi_pnl_usd > 0 else 0)
        gross_loss = abs((dt_stats["losses"] * -240) + (rsi_pnl_usd if rsi_pnl_usd < 0 else 0))
        if gross_profit == 0 and gross_loss == 0:
            profit_factor = 0.0
        elif gross_loss == 0:
            profit_factor = 99.9
        else:
            profit_factor = round(gross_profit / gross_loss, 2)

        mdd_proxy_usd = abs(gross_loss) * 1.5
        max_drawdown_pct = round((mdd_proxy_usd / self.initial_capital) * -100.0, 2)
        if max_drawdown_pct > 0:
            max_drawdown_pct = 0.0

        # 5. Colateral
        collateral_data = self._fetch_collateral_prices(consolidated_nav)

        # 6. Margen (sin spreads)
        margin_rsi       = 0.0 if rsi_status.get("status_mode") == "IDLE_MONITORING" else 5000.0
        margin_daytrade  = sum(p.get('strike', 500) * 100 * p.get('contracts', 1) * 0.20 for p in dt_active)
        total_margin_used = round(margin_daytrade + margin_rsi + 5000.0, 2)
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
            # Colateral diversificado (replaces treasury_sgov para compatibilidad se mantiene alias)
            "treasury_sgov": {
                "allocated_usd": collateral_data["breakdown"]["SGOV"]["actual_usd"],
                "annual_yield_pct": 5.2,
                "annual_yield_usd": collateral_data["breakdown"]["SGOV"]["annual_yield_usd"],
                "monthly_yield_usd": collateral_data["breakdown"]["SGOV"]["monthly_yield_usd"],
                "margin_requirement_pct": 2.0,
                "available_collateral_unlocked_usd": collateral_data["breakdown"]["SGOV"]["collateral_unlocked_usd"]
            },
            "collateral_portfolio": collateral_data,
            "reinvestment_matrix_50_30_20": {
                "total_premiums_collected_usd": reinvestment_status["total_premiums_collected_usd"],
                "total_reinvested_usd": reinvestment_status["total_reinvested_usd"],
                "pending_usd": reinvestment_status["pending_reinvestment_usd"],
                "pct_to_threshold": reinvestment_status["pct_to_threshold"],
                "threshold_usd": REINVESTMENT_THRESHOLD_USD,
                "sgov_treasury_50_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.50, 2),
                "spy_shares_30_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.30, 2),
                "alpha_decouple_20_usd": round(reinvestment_status["pending_reinvestment_usd"] * 0.20, 2),
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
                    "closed_trades_count": len(closed_dt_trades), "status": "SCANNING_INTRADAY"
                }
            ],
            "wheel_allowed_universe": WHEEL_ALLOWED_UNIVERSE
        }
