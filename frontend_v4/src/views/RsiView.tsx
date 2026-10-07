import React, { useState, useEffect } from 'react';

export const RsiView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('/api/rsi-opportunistic/status');
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-gray-400 p-4">Sincronizando con IB Gateway...</div>;
  if (!data) return <div className="text-red-400 p-4">Error cargando estado RSI.</div>;

  const pnl = data.total_pnl_usd || 0;
  const pnlClass = pnl >= 0 ? "text-[#00e676]" : "text-red-400";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded font-bold">CAPA 3 ACTIVADA</span>
            <span className="text-xs text-[#00e676]">● SCANNER 1DTE V-CRUSH ONLINE</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">RSI OPORTUNISTA <span className="text-sm font-normal text-gray-400">(VENTA DE PUTS 1DTE EN PÁNICO RSI {'<'} 30)</span></h1>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">MARGEN ASIGNADO</div>
          <div className="text-2xl font-bold text-white mt-1">${typeof data.allocated_capital === 'number' ? data.allocated_capital.toLocaleString() : "0.00"}</div>
          <div className="text-xs text-gray-500 mt-1">Pool Unificado D+ARQ</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">ÚLTIMO RSI SPY</div>
          <div className="text-2xl font-bold text-white mt-1">{data.last_rsi_scanned?.SPY || "N/A"}</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PNL TOTAL ACUMULADO</div>
          <div className={`text-2xl font-bold mt-1 ${pnlClass}`}>
            ${typeof pnl === 'number' && !isNaN(pnl) ? pnl.toLocaleString() : "0.00"}
          </div>
        </div>
      </div>

      {/* Posiciones */}
      {data.open_trades && data.open_trades.length > 0 ? (
        data.open_trades.map((pos: any, idx: number) => (
          <div key={idx} className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
             <div className="text-lg font-bold text-white">{pos.symbol} {pos.option_type} ${pos.strike} (1DTE)</div>
             <div className="grid grid-cols-3 text-xs gap-4">
               <div>
                 <span className="text-gray-400">RSI de Entrada:</span> {pos.entry_rsi}
               </div>
               <div>
                 <span className="text-gray-400">Prima Cobrada:</span> ${pos.premium_collected_usd}
               </div>
               <div>
                 <span className="text-gray-400">Estado:</span> {pos.status}
               </div>
             </div>
          </div>
        ))
      ) : (
        <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded text-center text-gray-500 text-sm">
          Sin operaciones RSI activas (Mercado sin pánico extremo).
        </div>
      )}
    </div>
  );
};
