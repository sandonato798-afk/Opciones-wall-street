import React, { useState, useEffect } from 'react';

export const BullMarketView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/master/summary')
      .then(res => res.json())
      .then(d => {
        setData(d?.layer_status?.bull_market || null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const ibkrOnline = data !== null;
  const openDiagonals: any[] = data?.open_diagonals || [];
  const rollHistory: any[] = data?.weekly_rolls_history || [];
  const totalPnl = data?.total_pnl_usd ?? 0;
  const thetaCollected = data?.total_theta_collected_usd ?? 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00e676] animate-pulse text-sm font-mono">
          ● CARGANDO DATOS REALES IBKR CAPA 5...
        </div>
      </div>
    );
  }

  const fmt = (v: number) => v >= 0 ? `+$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : `-$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  const pnlColor = (v: number) => v > 0 ? 'text-[#00e676]' : v < 0 ? 'text-red-400' : 'text-gray-400';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <span className="bg-red-900/60 border border-red-600 text-red-300 text-xs px-2 py-0.5 rounded font-bold">CAPA 05</span>
          <h1 className="text-2xl font-bold text-white mt-1">BULL MARKET PMCC <span className="text-sm font-normal text-gray-400">DIAGONAL SYNTHETIC LEAP OVERLAY</span></h1>
          <div className={`text-xs mt-1 ${ibkrOnline ? 'text-[#00e676]' : 'text-yellow-400'}`}>
            {ibkrOnline ? '● DATOS EN VIVO IBKR PAPER' : '● IBKR STANDBY — MERCADO CERRADO'}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[11px] text-gray-500">PnL TOTAL CAPA</div>
          <div className={`text-2xl font-bold ${pnlColor(totalPnl)}`}>{fmt(totalPnl)}</div>
          <div className="text-xs text-gray-400">Theta Acum: {fmt(thetaCollected)}</div>
        </div>
      </div>

      {/* Estado real */}
      {openDiagonals.length === 0 ? (
        <div className="bg-[#10141e] border border-[#1f2633] p-8 rounded text-center space-y-2">
          <div className="text-[#00e676] text-lg font-bold">✓ SISTEMA LIMPIO</div>
          <div className="text-gray-400 text-sm">No hay diagonales PMCC abiertas. El sistema abrirá posiciones reales el lunes a las 09:30 EST cuando el mercado abra.</div>
          <div className="text-xs text-gray-500 mt-2">Broker: IBKR Paper Trading | Estado: Esperando apertura de mercado</div>
        </div>
      ) : (
        openDiagonals.map((d: any, i: number) => (
          <div key={i} className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
            <div className="flex justify-between items-center border-b border-[#1f2633] pb-3">
              <div>
                <span className="text-lg font-bold text-white">{d.symbol} PMCC — Long ${d.long_call_strike} / Short ${d.short_call_strike}</span>
                <div className="text-xs text-gray-400 mt-0.5">Exp Long: {d.long_call_expiry} | Exp Short: {d.short_call_expiry} ({d.short_call_dte} DTE)</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400">PnL No Realizado</div>
                <div className={`text-xl font-bold ${pnlColor(d.total_unrealized_pnl_usd || 0)}`}>{fmt(d.total_unrealized_pnl_usd || 0)}</div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
                <div className="text-gray-500 uppercase text-[10px]">PATA LONG (CALL ITM)</div>
                <div>Strike: <span className="text-white font-bold">${d.long_call_strike} CALL</span></div>
                <div>Vencimiento: <span className="text-white">{d.long_call_expiry}</span></div>
                <div>Delta: <span className="text-cyan-400">Δ {d.long_call_delta ?? '—'}</span></div>
                <div>Prima Pagada: <span className="text-red-400">-${d.long_call_premium_paid ?? 0}</span></div>
              </div>
              <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
                <div className="text-gray-500 uppercase text-[10px]">PATA SHORT (RENTA OTM)</div>
                <div>Strike: <span className="text-white font-bold">${d.short_call_strike} CALL</span></div>
                <div>Vencimiento: <span className="text-white">{d.short_call_expiry} ({d.short_call_dte} DTE)</span></div>
                <div>Delta: <span className="text-amber-400">Δ {d.short_call_delta ?? '—'}</span></div>
                <div>Prima: <span className="text-[#00e676]">+${d.short_call_premium_collected ?? 0}</span></div>
              </div>
              <div className="bg-[#141924] p-3 rounded border border-[#222a38] space-y-1">
                <div className="text-gray-500 uppercase text-[10px]">ESTRUCTURA COMBINADA</div>
                <div>Inversión Neta: <span className="text-white">${d.net_debit_usd ?? 0}</span></div>
                <div>Break-Even: <span className="text-amber-400">${d.breakeven ?? '—'}</span></div>
                <div>Theta Rolls: <span className="text-[#00e676]">+${d.theta_collected_usd ?? 0}</span></div>
                <div>ROI: <span className={pnlColor(d.total_unrealized_pnl_usd || 0)}>{fmt(d.total_unrealized_pnl_usd || 0)}</span></div>
              </div>
            </div>
          </div>
        ))
      )}

      {/* Historial de Rolles — solo datos reales del estado */}
      {rollHistory.length > 0 && (
        <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold text-white tracking-wide">HISTORIAL DE ROLLEOS SEMANALES AUDITADOS</h2>
            <span className="text-xs text-[#00e676]">{rollHistory.length} CICLOS REALES</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead className="text-gray-500 border-b border-[#1f2633]">
              <tr>
                <th className="pb-2">CICLO</th>
                <th className="pb-2">FECHA</th>
                <th className="pb-2">STRIKE VENDIDO</th>
                <th className="pb-2">PRIMA RECIBIDA</th>
                <th className="pb-2">RECOMPRA</th>
                <th className="pb-2 text-right">RESULTADO NETO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2633]">
              {rollHistory.map((rc: any, idx: number) => (
                <tr key={idx} className="hover:bg-[#141924]">
                  <td className="py-2.5 font-bold text-white">Ciclo #{rc.cycle ?? idx + 1}</td>
                  <td className="py-2.5 text-gray-400">{rc.date ?? rc.roll_date ?? '—'}</td>
                  <td className="py-2.5 text-white">${rc.strike?.toFixed(2) ?? '—'} C</td>
                  <td className="py-2.5 text-[#00e676] font-medium">+${rc.credit?.toFixed(2) ?? rc.premium_collected?.toFixed(2) ?? '0.00'}</td>
                  <td className="py-2.5 text-amber-400">-${rc.rebuy?.toFixed(2) ?? rc.buyback_cost?.toFixed(2) ?? '0.00'}</td>
                  <td className="py-2.5 text-right font-bold text-[#00e676]">+${rc.net?.toFixed(2) ?? rc.net_profit?.toFixed(2) ?? '0.00'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
