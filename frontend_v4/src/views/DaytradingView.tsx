import React from 'react';

export const DaytradingView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded font-bold">CAPA 04</span>
            <span className="text-xs text-white">INTRADAY SCALPING & 0-3 DTE DESK</span>
            <span className="text-xs text-red-400 bg-red-950/60 border border-red-800 px-2 py-0.5 rounded font-bold animate-pulse">
              HORIZONTE LÍMITE: 01h 28m 38s
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">DAYTRADING INTRADÍA <span className="text-sm font-normal text-gray-400">(0-3 DTE & MANDATO TÁCTICO 15:55)</span></h1>
        </div>
        <div className="flex gap-2">
          <button className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-2 rounded">
            EJECUTAR ROLL DEFENSIVO CON CRÉDITO
          </button>
          <button className="text-xs bg-[#141a24] border border-[#1f2633] text-gray-300 px-3 py-2 rounded">
            CERRAR A MERCADO
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">MARGEN EN USO</div>
          <div className="text-2xl font-bold text-white mt-1">$15,510.00</div>
          <div className="text-xs text-gray-500 mt-1">Pool Unificado 100% Asignado</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">WIN RATE AUDITADO</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">92.3%</div>
          <div className="text-xs text-gray-500 mt-1">12 Ganadas / 1 Fallida (Sharpe 2.84)</div>
        </div>

        <div className="bg-[#10141e] border border-red-900/60 bg-red-950/20 p-4 rounded">
          <div className="text-[11px] text-red-400 uppercase font-bold">PNL FLOTANTE INTRADÍA</div>
          <div className="text-2xl font-bold text-red-400 mt-1">-$279.00</div>
          <div className="text-xs text-red-300 mt-1">1 Contrato Activo en Defender Roll</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">CERRADO ACUMULADO YTD</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+$3,140.00</div>
          <div className="text-xs text-[#00e676] mt-1">Retorno Nominal +20.24% (48 Trades)</div>
        </div>
      </div>

      {/* Banner Urgente Protocolo 15:55 */}
      <div className="bg-red-950/60 border border-red-700 p-5 rounded space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-sm font-bold text-white">¡PROTOCOLO 15:55 EST ACTIVO! (CUT-OFF MERCADO: 16:00 EST)</span>
          </div>
          <span className="text-xs text-red-300 font-bold border border-red-600 px-2 py-0.5 rounded">MANDATO TÁCTICO ANDRÉS</span>
        </div>
        <p className="text-xs text-gray-200">
          Prohibido cruzar liquidación nocturna en contrato ITM intradía. Requiere cierre neto positivo o <strong className="text-white">Roll Defensivo con Crédito</strong> extendido hacia 6-8 semanas para neutralizar riesgo de asignación forzada sobre equity collateral.
        </p>
        <div className="flex items-center justify-between pt-2 border-t border-red-800/60 text-xs">
          <span className="text-[#00e676] font-bold">
            Recomendación Algorítmica: Roll Out & Down hacia Strike $770.00 PUT (+42 días) con crédito de +$0.45/sh
          </span>
          <button className="bg-[#00e676] hover:bg-[#00c853] text-black font-bold px-3 py-1.5 rounded">
            APROBAR ROLL SUGERIDO
          </button>
        </div>
      </div>

      {/* Matriz Forense de Posición en Defender Chain */}
      <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
        <div className="flex justify-between items-center border-b border-[#1f2633] pb-3">
          <div>
            <span className="text-base font-bold text-white">MATRIZ FORENSE DE POSICIÓN AUDITADA: SPY 1DTE DEFENDER CHAIN</span>
            <div className="text-xs text-red-400 mt-0.5">STATUS: EN CURSO / ITM -0.54% (Strike $775.50 vs Spot $771.35)</div>
          </div>
          <span className="text-xs text-gray-400">LAST SYNCH: 14:26:22 EST</span>
        </div>

        <div className="grid grid-cols-4 gap-4 text-xs">
          <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">BLOQUE 01: DERIVADO</div>
            <div>Tipo: <span className="text-red-400 font-bold">PUT VENDIDA (SHORT)</span></div>
            <div>Strike: <span className="text-white font-bold">$775.50 ITM DEFENDER</span></div>
            <div>Vencimiento: <span className="text-red-400">0 DTE REMANENTE</span></div>
            <div>Riesgo: <span className="text-red-400 font-bold">NO CUBIERTO / NAKED RISK</span></div>
          </div>

          <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">BLOQUE 02: APERTURA</div>
            <div>Hora: <span className="text-white">14:23:01 EST</span></div>
            <div>Spot Open: <span className="text-white">$773.12 USD</span></div>
            <div>Prima Bid: <span className="text-[#00e676] font-bold">$8.19 / share</span></div>
            <div>Crédito Entrada: <span className="text-[#00e676]">+$257.00 NET CASH</span></div>
          </div>

          <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">BLOQUE 03: ESTATUS ACTUAL</div>
            <div>Spot SPY: <span className="text-white font-bold">$771.35 (-$1.77)</span></div>
            <div>Prima Recompra: <span className="text-amber-400 font-bold">$8.88 / share</span></div>
            <div>Costo Recompra: <span className="text-amber-400">$888.00 Gross</span></div>
            <div>Breach Distance: <span className="text-red-400 font-bold">-$4.15 BELOW STRIKE</span></div>
          </div>

          <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">BLOQUE 04: GRIEGAS</div>
            <div>PnL Flotante: <span className="text-red-400 font-bold">-$279.00 USD</span></div>
            <div>Delta (Δ): <span className="text-cyan-400 font-bold">-0.68 Δ (ACCEL)</span></div>
            <div>Theta (Θ): <span className="text-[#00e676]">+$42.10 / DÍA</span></div>
            <div>Vega Risk: <span className="text-gray-300">-$12.40 / 1% IV</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
