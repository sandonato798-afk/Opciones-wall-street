import React, { useState, useEffect } from 'react';

export const HomeView: React.FC = () => {
  const [masterData, setMasterData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/master/summary')
      .then(res => res.json())
      .then(data => {
        setMasterData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // Extraer datos reales del broker
  const ibkr = masterData?.ibkr_summary || {};
  const navReal = ibkr?.NetLiquidation ?? 0;
  const cashReal = ibkr?.TotalCashValue ?? 0;
  const buyingPower = ibkr?.BuyingPower ?? 0;
  const unrealizedPnl = ibkr?.UnrealizedPnL ?? 0;
  const realizedPnl = ibkr?.RealizedPnL ?? 0;
  const ibkrOnline = masterData?.ibkr_heartbeat?.status === 'ONLINE';

  // Capas desde layer_status
  const layerStatus = masterData?.layer_status || {};

  const layers = [
    {
      key: 'wheel', label: 'CAPA 1: RUEDA',
      data: layerStatus.wheel || {},
      pnl: layerStatus.wheel?.total_pnl_usd ?? 0,
      margin: 0,
    },
    {
      key: 'alpha', label: 'CAPA 2: ALPHA LEAPS',
      data: layerStatus.alpha || {},
      pnl: layerStatus.alpha?.unrealized_pnl_usd ?? 0,
      margin: 0,
    },
    {
      key: 'rsi', label: 'CAPA 3: RSI PÁNICO',
      data: layerStatus.rsi || {},
      pnl: layerStatus.rsi?.total_pnl_usd ?? 0,
      margin: layerStatus.rsi?.allocated_capital ?? 0,
    },
    {
      key: 'daytrade', label: 'CAPA 4: DAYTRADING',
      data: layerStatus.daytrade || {},
      pnl: 0,
      margin: layerStatus.daytrade?.allocated_capital ?? 0,
    },
    {
      key: 'bull', label: 'CAPA 5: BULL PMCC',
      data: layerStatus.bull_market || {},
      pnl: layerStatus.bull_market?.total_unrealized_pnl_usd ?? 0,
      margin: layerStatus.bull_market?.allocated_capital ?? 0,
    },
  ];

  const pnlColor = (v: number) => v > 0 ? 'text-[#00e676]' : v < 0 ? 'text-red-400' : 'text-gray-400';
  const fmt = (v: number) => v >= 0 ? `+$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : `-$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  const fmtUsd = (v: number) => `$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00e676] animate-pulse text-sm font-mono">
          ● CONECTANDO CON INTERACTIVE BROKERS...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="text-xs text-[#00e676] flex items-center gap-2">
            <span className={ibkrOnline ? 'text-[#00e676]' : 'text-red-400'}>
              {ibkrOnline ? '● IBKR ONLINE · DATOS REALES' : '● IBKR OFFLINE · MERCADO CERRADO'}
            </span>
            <span className="text-gray-500">|</span>
            <span>100% COLLATERALIZED POOL</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">PORTFOLIO OVERVIEW</h1>
        </div>
        <div className="text-right">
          <div className="text-[11px] text-gray-500">NAV REAL (IBKR PAPER)</div>
          <div className="text-2xl font-bold text-white">{fmtUsd(navReal)}</div>
          <div className="text-xs text-gray-400">Cash: {fmtUsd(cashReal)} | BP: {fmtUsd(buyingPower)}</div>
        </div>
      </div>

      {/* Estado de las 5 Capas — datos reales */}
      <div className="grid grid-cols-5 gap-3">
        {layers.map(layer => (
          <div key={layer.key} className="bg-[#10141e] border border-[#1f2633] p-3 rounded">
            <div className="flex justify-between text-[11px]">
              <span className="text-gray-400">{layer.label}</span>
              <span className={ibkrOnline ? 'text-[#00e676] text-[10px]' : 'text-yellow-500 text-[10px]'}>
                {ibkrOnline ? '● ONLINE' : '● STANDBY'}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Margen: {fmtUsd(layer.margin)}
            </div>
            <div className={`text-sm font-bold mt-0.5 ${pnlColor(layer.pnl)}`}>
              {fmt(layer.pnl)} PnL
            </div>
          </div>
        ))}
      </div>

      {/* PnL Global IBKR Real */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">NAV TOTAL (IBKR REAL)</div>
          <div className={`text-2xl font-bold mt-1 ${pnlColor(navReal)}`}>{fmtUsd(navReal)}</div>
          <div className="text-xs text-gray-500 mt-1">Liquidación Neta Cuenta Paper</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PnL NO REALIZADO</div>
          <div className={`text-2xl font-bold mt-1 ${pnlColor(unrealizedPnl)}`}>{fmt(unrealizedPnl)}</div>
          <div className="text-xs text-gray-500 mt-1">Posiciones Abiertas en Vivo</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PnL REALIZADO YTD</div>
          <div className={`text-2xl font-bold mt-1 ${pnlColor(realizedPnl)}`}>{fmt(realizedPnl)}</div>
          <div className="text-xs text-gray-500 mt-1">Operaciones Cerradas y Cobradas</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">BUYING POWER DISPONIBLE</div>
          <div className="text-2xl font-bold text-white mt-1">{fmtUsd(buyingPower)}</div>
          <div className="text-xs text-gray-500 mt-1">Capacidad de Margen Real Disponible</div>
        </div>
      </div>

      {/* Distribución de Activos */}
      <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-white uppercase">ASSET DISTRIBUTION (COLLATERAL & MARGIN)</span>
          <div className="flex gap-4 text-gray-400 text-[11px]">
            <span><span className="inline-block w-2.5 h-2.5 bg-emerald-400 rounded-sm mr-1"></span>Tesoro 40%</span>
            <span><span className="inline-block w-2.5 h-2.5 bg-cyan-400 rounded-sm mr-1"></span>Corp AAA 20%</span>
            <span><span className="inline-block w-2.5 h-2.5 bg-blue-500 rounded-sm mr-1"></span>SPY 20%</span>
            <span><span className="inline-block w-2.5 h-2.5 bg-amber-400 rounded-sm mr-1"></span>QQQ 15%</span>
            <span><span className="inline-block w-2.5 h-2.5 bg-teal-300 rounded-sm mr-1"></span>GLD 5%</span>
          </div>
        </div>
        <div className="h-5 w-full flex rounded overflow-hidden text-[10px] font-bold text-black">
          <div style={{ width: '40%' }} className="bg-emerald-400 flex items-center justify-center">TESORO 40%</div>
          <div style={{ width: '20%' }} className="bg-cyan-400 flex items-center justify-center">CORP 20%</div>
          <div style={{ width: '20%' }} className="bg-blue-500 text-white flex items-center justify-center">SPY 20%</div>
          <div style={{ width: '15%' }} className="bg-amber-400 flex items-center justify-center">QQQ 15%</div>
          <div style={{ width: '5%' }} className="bg-teal-300 flex items-center justify-center">GLD</div>
        </div>
      </div>

      {/* Estado del Sistema */}
      <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
        <div className="text-xs font-bold text-white uppercase mb-3">ESTADO DEL SISTEMA EN TIEMPO REAL</div>
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div>
            <div className="text-gray-500">BROKER</div>
            <div className={`font-bold ${ibkrOnline ? 'text-[#00e676]' : 'text-yellow-400'}`}>
              {ibkrOnline ? '✓ IBKR PAPER CONECTADO' : '⏳ IBKR STANDBY (MERCADO CERRADO)'}
            </div>
          </div>
          <div>
            <div className="text-gray-500">LATENCIA</div>
            <div className="font-bold text-white">
              {masterData?.ibkr_heartbeat?.latency_ms ?? '—'} ms
            </div>
          </div>
          <div>
            <div className="text-gray-500">ÚLTIMO SYNC</div>
            <div className="font-bold text-white">
              {masterData?.ibkr_heartbeat?.last_heartbeat ?? '—'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
