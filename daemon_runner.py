import time
import os
from datetime import datetime
from daytrade_options_bot import DayTradeOptionsBot, CONFIG

SCAN_INTERVAL_SECONDS = 60  # Scan every 1 minute during market hours

def is_wall_street_market_open():
    """
    Wall Street Market Hours: Mon-Fri 9:30 AM - 4:00 PM EST (10:30 - 17:00 AR)
    """
    now = datetime.now()
    if now.weekday() >= 5: # Saturday / Sunday
        return False
    
    hour = now.hour
    minute = now.minute
    time_num = hour * 100 + minute

    # Market Hours approx 10:30 AM to 17:00 PM local AR time
    if 1030 <= time_num <= 1700:
        return True
    return False

def main_loop():
    print("=" * 70)
    print("🚀 BOT DE DAY TRADING DE OPCIONES 24/7 EN LA NUBE (DAEMON RUNNER)")
    print(f"⚡ Modo de Ejecución: {CONFIG['execution_mode']} (Broker: {CONFIG['broker_name']})")
    print(f"⏱️ Intervalo de Escaneo: Cada {SCAN_INTERVAL_SECONDS} segundos durante horario de mercado.")
    print("=" * 70)

    bot = DayTradeOptionsBot()

    while True:
        try:
            if is_wall_street_market_open():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Mercado ABIERTO. Ejecutando escaneo intradiario...")
                bot.run_intraday_scan()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Mercado CERRADO. Esperando apertura de Wall Street...")

            time.sleep(SCAN_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n🛑 Daemon detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ Error en ciclo daemon: {e}. Reintentando en 30s...")
            time.sleep(30)

if __name__ == "__main__":
    main_loop()
