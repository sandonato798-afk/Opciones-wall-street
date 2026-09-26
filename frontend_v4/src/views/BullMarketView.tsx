import React from 'react';
import { activeTrades } from '../data/mockData';

export const BullMarketView: React.FC = () => {
  const trade = activeTrades.find(t => t.id === '#20260901');
  if (!trade) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <span className="bg-red-900/60 border border-red-600 text-red-300 text-xs px-2 py-0.5 rounded font-bold">CAPA 05</span>
          <h1 className="text-2xl font-bold text-white mt-1">BULL MARKET PMCC <span className="text-sm font-normal text-gray-400">DIAGONAL SYNTHETIC LEAP OVERLAY</span></h1>
          <div className="text-xs text-gray-400 mt-1">UNDERLYING: SPY | SPOT: $771.35 | IV: 16.42%</div>
        </div>
        <div className="flex gap-2">
          <button className="text-xs bg-[#141a24] border border-[#1f2633] text-white px-3 py-2 rounded">
            ABRIR NUEVO PMCC
          </button>
          <button className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-2 rounded">
            ROLLEAR SHORT CALL SEMANAL
          </button>
        </div>
      </div>

      {/* Grid de 3 Columnas Forenses (Estándar Pantalla Alpha) */}
      <div className="grid grid-cols-3 gap-4">
        {/* Pata Long ITM */}
        <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-white font-bold">● PATA LONG (CALL ITM)</span>
            <span className="text-cyan-400">Δ +0.85 LEAP</span>
          </div>
          <div className="text-xs text-gray-400">Subrogación Sintética de Acciones SPY</div>
          <div className="pt-2 border-t border-[#1f2633] space-y-2 text-xs">
            <div className="flex justify-between"><span>Strike:</span><span className="text-white font-bold">$726.90 CALL</span></div>
            <div className="flex justify-between"><span>Vencimiento:</span><span className="text-white">2026-11-24 (75 DTE)</span></div>
            <div className="flex justify-between"><span>Prima Pagada:</span><span className="text-red-400">-$58.70 /sh (-$5,870 Total)</span></div>
            <div className="flex justify-between"><span>Valor de Mercado:</span><span className="text-[#00e676] font-bold">$5,401.00 Liquidez</span></div>
          </div>
        </div>

        {/* Pata Short Semanal */}
        <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-white font-bold">● PATA SHORT (RENTA OTM)</span>
            <span className="text-amber-400">Δ -0.14 CALL</span>
          </div>
          <div className="text-xs text-gray-400">Extracción Periódica de Prima / Escudo Semanal</div>
          <div className="pt-2 border-t border-[#1f2633] space-y-2 text-xs">
            <div className="flex justify-between"><span>Strike Ciclo #6:</span><span className="text-white font-bold">$787.00 CALL</span></div>
            <div className="flex justify-between"><span>Vencimiento:</span><span className="text-white">2026-09-30 (3 DTE)</span></div>
            <div className="flex justify-between"><span>Prima Recibida:</span><span className="text-[#00e676] font-bold">+$1.25 /sh (+$125.00)</span></div>
            <div className="flex justify-between"><span>Recompra Actual:</span><span className="text-amber-400">-$0.46 /sh (-$46.00)</span></div>
          </div>
        </div>

        {/* Estructura Combinada */}
        <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-white font-bold">● ESTRUCTURA COMBINADA</span>
            <span className="text-[#00e676]">SPREAD AUDIT</span>
          </div>
          <div className="text-xs text-gray-400">Consolidación Neta Sintética + Cashflow Reinvest</div>
          <div className="pt-2 border-t border-[#1f2633] space-y-2 text-xs">
            <div className="flex justify-between"><span>Inversión Inicial:</span><span className="text-white">-$5,572.00 Débito</span></div>
            <div className="flex justify-between"><span>Break-Even:</span><span className="text-amber-400 font-bold">$782.62 (Spot: $771.35)</span></div>
            <div className="flex justify-between"><span>Theta Rolles Acum.:</span><span className="text-[#00e676] font-bold">+$528.30 USD</span></div>
            <div className="flex justify-between"><span>PNL Combinado:</span><span className="text-[#00e676] font-bold">+2.41% Spread ROI</span></div>
          </div>
        </div>
      </div>

      {/* Historial de Rolles Semanales Auditados */}
      <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-sm font-bold text-white tracking-wide">HISTORIAL DE ROLLEOS SEMANALES Y CICLOS DE THETA (5 CICLOS AUDITADOS)</h2>
          <span className="text-xs text-[#00e676]">100% PROFIT RECORD</span>
        </div>
        <table className="w-full text-left text-xs">
          <thead className="text-gray-500 border-b border-[#1f2633]">
            <tr>
              <th className="pb-2">CICLO</th>
              <th className="pb-2">FECHA</th>
              <th className="pb-2">STRIKE VENDIDO</th>
              <th className="pb-2">PRIMA RECIBIDA</th>
              <th className="pb-2">RECOMPRA</th>
              <th className="pb-2">RESULTADO NETO</th>
              <th className="pb-2 text-right">ESTADO</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f2633]">
            {trade.rollCycles?.map(rc => (
              <tr key={rc.cycle} className="hover:bg-[#141924]">
                <td className="py-2.5 font-bold text-white">Ciclo #{rc.cycle}</td>
                <td className="py-2.5 text-gray-400">{rc.date}</td>
                <td className="py-2.5 text-white">${rc.strike.toFixed(2)} C</td>
                <td className="py-2.5 text-[#00e676] font-medium">+${rc.credit.toFixed(2)}</td>
                <td className="py-2.5 text-amber-400">-${rc.rebuy.toFixed(2)}</td>
                <td className="py-2.5 text-[#00e676] font-bold">+${rc.net.toFixed(2)}</td>
                <td className="py-2.5 text-right">
                  <span className="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">
                    {rc.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
