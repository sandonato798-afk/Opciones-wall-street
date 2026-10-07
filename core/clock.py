# -*- coding: utf-8 -*-
"""
core/clock.py - Manejador de Tiempo y Calendario Institucional NYSE
Centraliza la zona horaria America/New_York y el calendario oficial de festivos y cierres tempranos.
"""

from datetime import datetime, time, date
import zoneinfo

ET_TIMEZONE = zoneinfo.ZoneInfo("America/New_York")

# Calendario oficial de feriados NYSE (2026 - 2030)
NYSE_HOLIDAYS = {
    # 2026
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # Martin Luther King Jr. Day
    date(2026, 2, 16),  # Washington's Birthday
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 25),  # Memorial Day
    date(2026, 6, 19),  # Juneteenth
    date(2026, 7, 3),   # Independence Day (Observed)
    date(2026, 9, 7),   # Labor Day
    date(2026, 11, 26), # Thanksgiving Day
    date(2026, 12, 25), # Christmas Day
    # 2027
    date(2027, 1, 1),
    date(2027, 1, 18),
    date(2027, 2, 15),
    date(2027, 3, 26),
    date(2027, 5, 31),
    date(2027, 6, 18),
    date(2027, 7, 5),
    date(2027, 9, 6),
    date(2027, 11, 25),
    date(2027, 12, 25),
}

# Cierres tempranos de NYSE (13:00 ET)
NYSE_EARLY_CLOSES = {
    date(2026, 7, 2): time(13, 0),   # Vispera de 4 de Julio
    date(2026, 11, 27): time(13, 0), # Black Friday
    date(2026, 12, 24): time(13, 0), # Nochebuena
}

def now_et() -> datetime:
    """Retorna la fecha y hora actual en la zona horaria de Nueva York (EST/EDT)."""
    return datetime.now(ET_TIMEZONE)

def is_nyse_trading_day(dt: date = None) -> bool:
    """Verifica si un dia es de operaciones normales en la Bolsa de Nueva York."""
    if dt is None:
        dt = now_et().date()
    # Fin de semana (5 = Sabado, 6 = Domingo)
    if dt.weekday() >= 5:
        return False
    # Feriado oficial
    if dt in NYSE_HOLIDAYS:
        return False
    return True

def is_nyse_market_open(dt: datetime = None) -> bool:
    """Verifica si el mercado de opciones regular de EE.UU. esta actualmente abierto."""
    if dt is None:
        dt = now_et()
    
    current_date = dt.date()
    if not is_nyse_trading_day(current_date):
        return False
    
    current_time = dt.time()
    open_time = time(9, 30)
    close_time = NYSE_EARLY_CLOSES.get(current_date, time(16, 0))
    
    return open_time <= current_time < close_time
