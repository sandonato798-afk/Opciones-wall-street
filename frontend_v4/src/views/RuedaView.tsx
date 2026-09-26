import React from 'react';

export const RuedaView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded font-bold">CAPA 1</span>
            <span className="text-xs text-gray-400">DEFCON: NIVEL 1</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">LA RUEDA <span className="text-sm font-normal text-gray-400">(OVERLAY SOBRE 100% CARTERA DE COLATERAL)</span></h1>
          <div className="text-xs text-gray-400 mt-1">SISTEMA SISTEMÁTICO DE RECOLECCIÓN DE PRIMAS IV CON GARANTÍA DE LIQUIDEZ REPO</div>
        </div>
        <button className="bg-red-600 hover:bg-red-500 text-white font-bold text-xs px-4 py-2 rounded">
          EJECUTAR RUN CYCLE
        </button>
      </div>

      {/* KPI Cards Colateral */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">COLATERAL RESPALDADO</div>
          <div className="text-2xl font-bold text-white mt-1">$100,000.00</div>
          <div className="text-xs text-gray-400 mt-1">100% NAV (SGOV + GLD + TLT)</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">ACCIONES EN CARTERA</div>
          <div className="text-2xl font-bold text-white mt-1">1.9685 SPY</div>
          <div className="text-xs text-cyan-400 mt-1">Covered Calls Activos | Δ +1.0</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PRIMAS REINVERTIDAS</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">$1,522.30</div>
          <div className="text-xs text-gray-400 mt-1">Interés Compuesto · Run Rate $380.50/m</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">CAGR TOTAL (YIELD STACKING)</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+12.50%</div>
          <div className="text-xs text-gray-400 mt-1">T-Bills 5.2% + Primas 7.3% (Sharpe 2.41)</div>
        </div>
      </div>

      {/* Universo de Activos Permitidos */}
      <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded space-y-3">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-white">UNIVERSO DE ACTIVOS PERMITIDOS (OVERLAY INSTITUCIONAL)</span>
          <span className="text-gray-400 text-[11px]">CRITERIO: HIGH LIQUIDITY / TIGHT SPREADS / LOW TAIL RISK</span>
        </div>
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="bg-[#141924] border border-[#232936] p-3 rounded">
            <div className="flex justify-between font-bold text-white">
              <span>SPY (S&P 500 ETF)</span>
              <span className="text-[#00e676]">● ACTIVO (Ciclo Mensual)</span>
            </div>
            <div className="text-gray-400 text-[11px] mt-1">Delta: Δ 0.20 - 0.25 (3.0% OTM) · 30-45 DTE</div>
            <div className="text-[#00e676] text-[11px] mt-1">Pool Unificado Intocable</div>
          </div>
          <div className="bg-[#141924] border border-[#232936] p-3 rounded">
            <div className="flex justify-between font-bold text-white">
              <span>QQQ (Nasdaq 100)</span>
              <span className="text-[#00e676]">● ACTIVO (Escaneo Abierto)</span>
            </div>
            <div className="text-gray-400 text-[11px] mt-1">Delta: Δ 0.20 - 0.25 (3.0% OTM) · 30-45 DTE</div>
            <div className="text-[#00e676] text-[11px] mt-1">Pool Unificado Intocable</div>
          </div>
          <div className="bg-[#141924] border border-[#232936] p-3 rounded">
            <div className="flex justify-between font-bold text-white">
              <span>IWM (Russell 2000)</span>
              <span className="text-gray-400">● LISTO PARA ENTRADA</span>
            </div>
            <div className="text-gray-400 text-[11px] mt-1">Delta: Δ 0.20 (3.5% OTM) · 30-45 DTE</div>
            <div className="text-gray-400 text-[11px] mt-1">Pool Unificado Intocable</div>
          </div>
        </div>
      </div>

      {/* Posición Activa con Protocolo 15:55 */}
      <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-white">SPY PUT $788.0 · 1DTE</span>
              <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">EN CURSO (1x)</span>
              <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded animate-pulse font-bold">
                ● ITM (-1.85%) - ROLL DEFENSIVO ANDRÉS
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">Strike: $788.0 | Spot Actual: $773.38 | Vencimiento: 2026-11-06 (45d)</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">PnL Flotante</div>
            <div className="text-xl font-bold text-[#00e676]">+$2,950.00</div>
          </div>
        </div>

        {/* Take Profit Progress Bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">PROGRESO TAKE PROFIT (50%): Cobrado $2,950.00</span>
            <span className="text-[#00e676] font-bold">100% COMPLETADO (Meta TP: +$1,475.00)</span>
          </div>
          <div className="w-full bg-[#181d28] h-2 rounded overflow-hidden">
            <div className="bg-[#00e676] h-full w-full"></div>
          </div>
        </div>

        {/* Mandato Andrés Box */}
        <div className="bg-red-950/40 border border-red-800/80 p-3 rounded text-xs flex items-center gap-3 text-red-200">
          <span className="text-red-400 font-bold uppercase shrink-0">Protocolo Andrés:</span>
          <span>Colateral intocable. Ante asignación: venta inmediata de acciones a las 09:30 EST + venta de Put a 6-8 semanas para resetear prima y apalancamiento neutro.</span>
        </div>
      </div>
    </div>
  );
};
