# -*- coding: utf-8 -*-
"""
market_calendar.py - Calendario Centralizado de Mercado NYSE/NASDAQ
Módulo único de verdad para todos los bots del sistema.
Evita operaciones en fines de semana, feriados y fuera de horario.
"""

from datetime import datetime, date, time, timedelta, timezone

# Zona horaria EST (Eastern Standard Time = UTC-5 en invierno, UTC-4 en verano)
# Usamos offset fijo de -4 para EDT (horario de verano, vigente en la mayor parte del año bursátil)
EST = timezone(timedelta(hours=-4))  # EDT (Mar-Nov)
EST_WINTER = timezone(timedelta(hours=-5))  # EST (Nov-Mar)

# ─────────────────────────────────────────────────────────────────────────────
# FERIADOS NYSE — Mercado CERRADO estos días (sin operaciones)
# ─────────────────────────────────────────────────────────────────────────────
NYSE_HOLIDAYS = {
    # 2026
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # Martin Luther King Jr. Day
    date(2026, 2, 16),  # Presidents' Day
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 25),  # Memorial Day
    date(2026, 7, 3),   # Independence Day (observed)
    date(2026, 9, 7),   # Labor Day
    date(2026, 11, 26), # Thanksgiving Day
    date(2026, 11, 27), # Black Friday (cierre anticipado 13:00 EST — tratamos como cerrado)
    date(2026, 12, 25), # Christmas Day

    # 2027
    date(2027, 1, 1),   # New Year's Day
    date(2027, 1, 18),  # Martin Luther King Jr. Day
    date(2027, 2, 15),  # Presidents' Day
    date(2027, 3, 26),  # Good Friday
    date(2027, 5, 31),  # Memorial Day
    date(2027, 7, 5),   # Independence Day (observed)
    date(2027, 9, 6),   # Labor Day
    date(2027, 11, 25), # Thanksgiving Day
    date(2027, 12, 24), # Christmas Day (observed)
}

# Días de cierre anticipado (13:00 EST) — el bot NO abre posiciones nuevas
NYSE_EARLY_CLOSE = {
    date(2026, 11, 27),  # Black Friday 2026
    date(2026, 12, 24),  # Christmas Eve 2026
    date(2027, 7, 2),    # Day before Independence Day 2027
    date(2027, 11, 26),  # Black Friday 2027
    date(2027, 12, 24),  # Christmas Eve 2027
}

# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────

def _now_est() -> datetime:
    """Retorna el datetime actual en hora EST/EDT."""
    # Detección automática de horario de verano (simplificada)
    now_utc = datetime.now(timezone.utc)
    # DST: segundo domingo de marzo → primer domingo de noviembre
    year = now_utc.year
    dst_start = _nth_weekday(year, 3, 6, 2)   # 2do domingo de marzo
    dst_end   = _nth_weekday(year, 11, 6, 1)  # 1er domingo de noviembre
    if dst_start <= now_utc.date() < dst_end:
        return now_utc.astimezone(EST)
    else:
        return now_utc.astimezone(EST_WINTER)

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Retorna el n-ésimo día de la semana (0=lunes, 6=domingo) del mes dado."""
    d = date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)

def is_trading_day(check_date: date = None) -> bool:
    """
    Retorna True si el día es un día hábil bursátil (lunes-viernes, no feriado NYSE).
    Si check_date es None, usa el día actual en EST.
    """
    if check_date is None:
        check_date = _now_est().date()
    # Fin de semana
    if check_date.weekday() >= 5:  # 5=sábado, 6=domingo
        return False
    # Feriado NYSE
    if check_date in NYSE_HOLIDAYS:
        return False
    return True

def is_market_open() -> bool:
    """
    Retorna True si el mercado NYSE está abierto AHORA MISMO.
    Horario regular: lunes-viernes 09:30-16:00 EST (excluyendo feriados).
    """
    now_est = _now_est()
    today = now_est.date()

    if not is_trading_day(today):
        return False

    # Horario regular: 09:30 - 16:00
    market_open  = time(9, 30)
    market_close = time(16, 0)

    # Cierre anticipado (13:00 EST)
    if today in NYSE_EARLY_CLOSE:
        market_close = time(13, 0)

    current_time = now_est.time()
    return market_open <= current_time < market_close

def is_pre_market() -> bool:
    """Retorna True si estamos en pre-market (04:00-09:30 EST) en día hábil."""
    now_est = _now_est()
    if not is_trading_day(now_est.date()):
        return False
    t = now_est.time()
    return time(4, 0) <= t < time(9, 30)

def is_near_close(minutes_before: int = 15) -> bool:
    """Retorna True si faltan menos de N minutos para el cierre del mercado."""
    now_est = _now_est()
    if not is_trading_day(now_est.date()):
        return False
    close_time = time(13, 0) if now_est.date() in NYSE_EARLY_CLOSE else time(16, 0)
    close_dt = datetime.combine(now_est.date(), close_time, tzinfo=now_est.tzinfo)
    return datetime.now(now_est.tzinfo) >= close_dt - timedelta(minutes=minutes_before)

def next_market_open() -> datetime:
    """Retorna el datetime (en EST) de la próxima apertura del mercado."""
    now_est = _now_est()
    check = now_est.date()

    for _ in range(10):  # buscar en los próximos 10 días
        if is_trading_day(check):
            open_dt = datetime.combine(check, time(9, 30), tzinfo=now_est.tzinfo)
            if open_dt > now_est:
                return open_dt
        check += timedelta(days=1)

    return None  # no debería ocurrir

def calendar_status() -> dict:
    """
    Retorna un dict completo del estado del calendario para el dashboard.
    Compatible con el endpoint /api/calendar/status
    """
    now_est = _now_est()
    today = now_est.date()
    open_now = is_market_open()
    trading_today = is_trading_day(today)
    next_open = next_market_open()

    reason_closed = None
    if not open_now:
        if today.weekday() == 5:
            reason_closed = "SABADO"
        elif today.weekday() == 6:
            reason_closed = "DOMINGO"
        elif today in NYSE_HOLIDAYS:
            reason_closed = "FERIADO_NYSE"
        elif not is_trading_day(today):
            reason_closed = "DIA_NO_HABIL"
        elif now_est.time() < time(9, 30):
            reason_closed = "PRE_MARKET"
        else:
            reason_closed = "POST_MARKET"

    # Próximos feriados (30 días)
    upcoming_holidays = []
    for h in sorted(NYSE_HOLIDAYS):
        if today < h <= today + timedelta(days=30):
            upcoming_holidays.append(h.isoformat())

    return {
        "market_open": open_now,
        "trading_day": trading_today,
        "current_time_est": now_est.strftime("%Y-%m-%d %H:%M:%S EST"),
        "current_time_arg": datetime.now().strftime("%Y-%m-%d %H:%M:%S ARG"),
        "reason_closed": reason_closed,
        "is_early_close_day": today in NYSE_EARLY_CLOSE,
        "next_market_open_est": next_open.strftime("%Y-%m-%d %H:%M:%S EST") if next_open else None,
        "upcoming_holidays": upcoming_holidays,
        "status_emoji": "🟢 ABIERTO" if open_now else "🔴 CERRADO"
    }


if __name__ == "__main__":
    import json
    print(json.dumps(calendar_status(), indent=2, ensure_ascii=False))
