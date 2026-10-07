import React, { useState, useEffect } from 'react';

export const RuedaView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchWheelStatus = async () => {
    try {
      const res = await fetch('/api/wheel/status');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWheelStatus();
    const interval = setInterval(fetchWheelStatus, 15000); // 15 sec refresh
    return () => clearInterval(interval);
  }, []);

  const handleRunCycle = async () => {
    try {
      await fetch('/api/wheel/run-cycle', { method: 'POST' });
      fetchWheelStatus();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div className="text-gray-400 p-4">Sincronizando con IB Gateway...</div>;
  if (!data) return <div className="text-red-400 p-4">Error cargando estado de la Rueda.</div>;

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
        <button 
          onClick={handleRunCycle}
          className="bg-red-600 hover:bg-red-500 text-white font-bold text-xs px-4 py-2 rounded">
          EJECUTAR RUN CYCLE
        </button>
      </div>

      {/* KPI Cards Colateral */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">COLATERAL RESPALDADO</div>
          <div className="text-2xl font-bold text-white mt-1">${typeof data.initial_capital_usd === 'number' ? data.initial_capital_usd.toLocaleString() : "0.00"}</div>
          <div className="text-xs text-gray-400 mt-1">100% NAV (SGOV + GLD + TLT)</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">ACCIONES EN CARTERA</div>
          <div className="text-2xl font-bold text-white mt-1">{data.etf_shares} {data.etf_symbol}</div>
          <div className="text-xs text-cyan-400 mt-1">Covered Calls Activos | Θ {data.etf_shares > 0 ? '+1.0' : '0.0'}</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PRIMAS REINVERTIDAS</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">${typeof data.accumulated_premiums_usd === 'number' ? data.accumulated_premiums_usd.toLocaleString() : "0.00"}</div>
          <div className="text-xs text-gray-400 mt-1">Interés Compuesto </div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">CAGR TOTAL (YIELD STACKING)</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">{data.cagr_pct}%</div>
          <div className="text-xs text-gray-400 mt-1">Estimado</div>
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
              <span className={data.etf_symbol === 'SPY' ? "text-[#00e676]" : "text-gray-400"}>
                {data.etf_symbol === 'SPY' ? '● ACTIVO' : '○ INACTIVO'}
              </span>
            </div>
            <div className="text-gray-400 text-[11px] mt-1">Delta: - 0.20 - 0.25 (3.0% OTM) </div>
            <div className="text-[#00e676] text-[11px] mt-1">Pool Unificado Intocable</div>
          </div>
          <div className="bg-[#141924] border border-[#232936] p-3 rounded">
            <div className="flex justify-between font-bold text-white">
              <span>QQQ (Nasdaq 100)</span>
              <span className={data.etf_symbol === 'QQQ' ? "text-[#00e676]" : "text-gray-400"}>
                 {data.etf_symbol === 'QQQ' ? '● ACTIVO' : '○ INACTIVO'}
              </span>
            </div>
            <div className="text-gray-400 text-[11px] mt-1">Delta: - 0.20 - 0.25 (3.0% OTM) </div>
            <div className="text-[#00e676] text-[11px] mt-1">Pool Unificado Intocable</div>
          </div>
        </div>
      </div>

      {/* Posiciones Activas */}
      {data.wheel_positions && data.wheel_positions.length > 0 ? (
        data.wheel_positions.map((pos: any, idx: number) => (
          <div key={idx} className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-white">{pos.symbol} {pos.option_type} ${pos.strike}</span>
                  <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">EN CURSO ({pos.contracts}x)</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">Vencimiento: {pos.expiry} | Spot: ${data.etf_price}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-400">Prima Cobrada</div>
                <div className="text-xl font-bold text-[#00e676]">${typeof pos.premium_collected_usd === 'number' ? pos.premium_collected_usd.toLocaleString() : "0.00"}</div>
              </div>
            </div>
          </div>
        ))
      ) : (
         <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded text-center text-gray-500 text-sm">
            Sin operaciones en curso. Ejecute Run Cycle o espere a la apertura del mercado.
         </div>
      )}
    </div>
  );
};
