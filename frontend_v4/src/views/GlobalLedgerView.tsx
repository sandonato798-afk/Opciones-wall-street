import React, { useState } from 'react';
import { activeTrades, portfolioSummary } from '../data/mockData';


export const GlobalLedgerView: React.FC = () => {
  const [filterLayer, setFilterLayer] = useState<string>('TODAS');

  const filtered = activeTrades.filter(t => {
    if (filterLayer !== 'TODAS' && t.layer !== filterLayer) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Title & Stats */}
      <div className="flex justify-between items-end border-b border-[#1f2633] pb-4">
        <div>
          <div className="text-xs text-[#00e676] flex items-center gap-2">
            <span>● SYNC 100% NY4</span>
            <span className="text-gray-500">|</span>
            <span>AUDITORÍA TRANSVERSAL MULTI-CAPA (34 OPS TOTAL)</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">REPOSITORIO GLOBAL <span className="text-sm font-normal text-gray-400">LEDGER V4.2</span></h1>
        </div>
      </div>

      {/* KPI Cards Consolidado */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">WIN RATE AUDIT (GLOBAL)</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">{portfolioSummary.winRate}%</div>
          <div className="text-xs text-gray-500 mt-1">{portfolioSummary.tradesPositivos}/{portfolioSummary.tradesTotales} Trades Positivos</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">THETA GLOBAL EXTRAÍDO</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+${portfolioSummary.thetaGlobalTotal.toLocaleString()}</div>
          <div className="text-xs text-gray-500 mt-1">Decay Engine (+${portfolioSummary.thetaDiario}/día)</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">ESTADO MASTER OPERATIVO</div>
          <div className="text-2xl font-bold text-white mt-1">5 ACTIVAS <span className="text-sm font-normal text-gray-500">/ 29 Cerradas</span></div>
          <div className="text-xs text-[#00e676] mt-1">Pool 100% Asignable</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">TOTAL PNL AUDITADO NETO</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+${portfolioSummary.pnlTotal.toLocaleString()}</div>
          <div className="text-xs text-[#00e676] mt-1">ROI Realizado: +{portfolioSummary.pnlPercentage}%</div>
        </div>
      </div>

      {/* Barra de Filtros */}
      <div className="flex gap-2 border-b border-[#1f2633] pb-3">
        {['TODAS', 'RUEDA', 'ALPHA', 'RSI', 'DAYTRADING', 'BULL_MARKET'].map(layer => (
          <button
            key={layer}
            onClick={() => setFilterLayer(layer)}
            className={`text-xs px-3 py-1.5 rounded transition ${
              filterLayer === layer ? 'bg-red-600 text-white font-bold' : 'bg-[#141a24] text-gray-400 hover:text-white'
            }`}
          >
            {layer}
          </button>
        ))}
      </div>

      {/* Tabla Transversal Forense */}
      <div className="bg-[#10141e] border border-[#1f2633] rounded overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#0c1018] text-gray-400 border-b border-[#1f2633]">
            <tr>
              <th className="p-3">ID / REF</th>
              <th className="p-3">CAPA & ESTRATEGIA</th>
              <th className="p-3">TICKER</th>
              <th className="p-3">STRIKES</th>
              <th className="p-3">DTE</th>
              <th className="p-3">DELTA</th>
              <th className="p-3">CRÉDITO/DÉBITO</th>
              <th className="p-3">SPOT</th>
              <th className="p-3">PNL FLOTANTE</th>
              <th className="p-3">ESTADO / PROTOCOLO</th>
              <th className="p-3 text-right">ACCIONES</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f2633]">
            {filtered.map(t => {
              const isProfit = t.pnlFlotante >= 0;
              return (
                <tr key={t.id} className="hover:bg-[#141924] transition">
                  <td className="p-3 font-semibold text-white">{t.id}</td>
                  <td className="p-3">
                    <div className="text-white font-medium">{t.layerTitle}</div>
                    <div className="text-[10px] text-gray-400">{t.strategy}</div>
                  </td>
                  <td className="p-3 font-bold text-white">{t.ticker}</td>
                  <td className="p-3">
                    {t.strike ? `$${t.strike}` : `$${t.strikeLong} / $${t.strikeShort}`}
                  </td>
                  <td className="p-3 font-semibold text-cyan-400">{t.dte}d</td>
                  <td className="p-3 text-cyan-400">{t.deltaNet > 0 ? `+${t.deltaNet}` : t.deltaNet} Δ</td>
                  <td className="p-3 text-[#00e676]">{t.entryNet >= 0 ? `+$${t.entryNet}` : `-$${Math.abs(t.entryNet)}`}</td>
                  <td className="p-3 text-white">${t.spotPrice}</td>
                  <td className={`p-3 font-bold ${isProfit ? 'text-[#00e676]' : 'text-red-400'}`}>
                    {isProfit ? `+$${t.pnlFlotante}` : `-$${Math.abs(t.pnlFlotante)}`}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] border ${
                      t.status === 'ALERTA_1555_ROLL_DEFENSIVO' ? 'bg-red-950 text-red-300 border-red-700 font-bold animate-pulse' :
                      t.status === 'TAKE_PROFIT_50_LISTO' ? 'bg-emerald-950 text-emerald-300 border-emerald-700' :
                      'bg-[#1b2230] text-gray-300 border-[#283245]'
                    }`}>
                      {t.statusLabel}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    {t.status === 'ALERTA_1555_ROLL_DEFENSIVO' ? (
                      <button className="bg-red-600 hover:bg-red-500 text-white font-bold text-[10px] px-2.5 py-1 rounded">
                        ROLL AHORA
                      </button>
                    ) : t.status === 'TAKE_PROFIT_50_LISTO' ? (
                      <button className="bg-[#00e676] hover:bg-[#00c853] text-black font-bold text-[10px] px-2.5 py-1 rounded">
                        CERRAR 50%
                      </button>
                    ) : (
                      <button className="border border-[#1f2633] hover:border-gray-500 text-gray-300 text-[10px] px-2 py-1 rounded">
                        AUDITAR
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
