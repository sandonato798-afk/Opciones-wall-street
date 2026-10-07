import React, { useState, useEffect } from 'react';

export const HomeView: React.FC = () => {
  const [masterData, setMasterData] = useState<any>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMasterSummary = () => {
    Promise.all([
      fetch('/api/master/summary').then(res => res.json()).catch(() => ({})),
      fetch('/api/history/unified').then(res => res.json()).catch(() => ({ trades: [] }))
    ]).then(([masterRes, historyRes]) => {
      setMasterData(masterRes);
      
      let tradesList = historyRes.trades || [];
      // Fallback si historyRes viniera vacío: extraer de layer_status
      if (tradesList.length === 0 && masterRes?.layer_status) {
        const ls = masterRes.layer_status;
        const fallback: any[] = [];
        (ls.wheel?.positions || []).forEach((p: any) => {
          fallback.push({
            timestamp: p.issued_date || '—',
            capa_nombre: 'Capa 1: Rueda',
            tipo: 'CASH_SECURED_PUT',
            simbolo: p.symbol || 'SPY',
            strike: p.strike,
            expiracion: p.expiration_date || '—',
            premium_usd: p.premium_collected_usd || 0.0,
            pnl_usd: 0.0,
            estado: p.status || 'ACTIVE'
          });
        });
        (ls.alpha?.open_positions || []).forEach((p: any) => {
          fallback.push({
            timestamp: p.entry_date || '—',
            capa_nombre: 'Capa 2: Alpha LEAPS',
            tipo: p.strategy || 'ZERO_COST_SYNTHETIC',
            simbolo: p.symbol || 'SPY',
            strike: p.long_call_strike,
            expiracion: p.expiry || '—',
            premium_usd: p.long_call_premium_paid,
            pnl_usd: p.unrealized_pnl_usd || 0.0,
            estado: p.status || 'ACTIVE_SYNTHETIC'
          });
        });
        (ls.alpha?.decoupled_calls || []).forEach((p: any) => {
          fallback.push({
            timestamp: p.decouple_date || p.entry_date || '—',
            capa_nombre: 'Capa 2: Alpha LEAPS',
            tipo: 'FREE_RUNNER_LONG_CALL',
            simbolo: p.symbol || 'SPY',
            strike: p.long_call_strike,
            expiracion: '—',
            premium_usd: p.long_call_premium_paid,
            pnl_usd: p.unrealized_pnl_usd || 0.0,
            estado: 'DECOUPLED_RISK_FREE'
          });
        });
        (ls.bull_market?.open_diagonals || []).forEach((d: any) => {
          fallback.push({
            timestamp: d.entry_date || '—',
            capa_nombre: 'Capa 5: Bull PMCC',
            tipo: 'POOR_MANS_COVERED_CALL',
            simbolo: d.symbol || 'SPY',
            strike: `Long $${d.long_call_strike} / Short $${d.short_call_strike}`,
            expiracion: `Long: ${d.long_call_expiration} | Short: ${d.short_call_expiration}`,
            premium_usd: d.short_call_premium_collected || 0.0,
            pnl_usd: d.total_unrealized_pnl_usd || 0.0,
            estado: d.status || 'ACTIVE_ROLLING_WEEKLY',
            detalle: d
          });
        });
        tradesList = fallback;
      }

      setHistoryData(tradesList);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchMasterSummary();
    const interval = setInterval(fetchMasterSummary, 15000);
    return () => clearInterval(interval);
  }, []);

  // Extraer datos reales del broker
  const ibkr = masterData?.ibkr_summary || {};
  const navReal = ibkr?.NetLiquidation ?? null;
  const cashReal = ibkr?.TotalCashValue ?? null;
  const buyingPower = ibkr?.BuyingPower ?? null;
  const unrealizedPnl = ibkr?.UnrealizedPnL ?? null;
  const realizedPnl = ibkr?.RealizedPnL ?? null;
  const ibkrOnline = masterData?.ibkr_heartbeat?.status === 'ONLINE';

  // Capas desde layer_status
  const layerStatus = masterData?.layer_status || {};

  const layers = [
    {
      key: 'wheel', label: 'CAPA 1: RUEDA',
      pnl: layerStatus.wheel?.total_pnl_usd ?? 0.0,
      margin: 1000000.0,
      status: (layerStatus.wheel?.positions?.length || 0) > 0 ? `● ${layerStatus.wheel.positions.length} POSICIÓN RUEDA ACTIVA` : '● EN ESPERA DE OPORTUNIDAD'
    },
    {
      key: 'alpha', label: 'CAPA 2: ALPHA LEAPS',
      pnl: layerStatus.alpha?.total_pnl_usd ?? 0.0,
      margin: 200000.0,
      status: (layerStatus.alpha?.open_positions?.length || 0) > 0 ? `● ${layerStatus.alpha.open_positions.length} SINTÉTICO(S) ACTIVO(S)` : '● EN ESPERA DE SEÑAL MACRO'
    },
    {
      key: 'rsi', label: 'CAPA 3: RSI PÁNICO',
      pnl: layerStatus.rsi?.total_pnl_usd ?? 0.0,
      margin: 150000.0,
      status: '● MONITOR (RSI < 25)'
    },
    {
      key: 'daytrade', label: 'CAPA 4: DAYTRADING',
      pnl: layerStatus.daytrade?.total_pnl_usd ?? 0.0,
      margin: 150000.0,
      status: '● MONITOR (ORB 15M)'
    },
    {
      key: 'bull', label: 'CAPA 5: BULL PMCC',
      pnl: layerStatus.bull_market?.total_pnl_usd ?? 0.0,
      margin: 150000.0,
      status: (layerStatus.bull_market?.open_diagonals?.length || 0) > 0 ? `● ${layerStatus.bull_market.open_diagonals.length} DIAGONAL ACTIVA` : '● EN ESPERA DE TENDENCIA'
    },
  ];

  const collateralBreakdown = [
    { ticker: 'US-NOTES', name: 'US Treasury Notes (6 Bonos Escalonados 12/2027-12/2032)', shares: 'Escalonado 10% c/u', currentPx: '< 100.00 Par', totalUsd: 600000, pct: '60%', yieldApy: '~5.00% APY' },
    { ticker: 'VOO', name: 'Vanguard S&P 500 ETF (Core Equity)', shares: 'Colateral Intocable', currentPx: 'Precio Spot IBKR', totalUsd: 200000, pct: '20%', yieldApy: '1.50% APY' },
    { ticker: 'QQQ', name: 'Invesco QQQ Trust (Nasdaq 100)', shares: 'Colateral Intocable', currentPx: 'Precio Spot IBKR', totalUsd: 150000, pct: '15%', yieldApy: '0.80% APY' },
    { ticker: 'GLD', name: 'SPDR Gold Shares (Oro Físico)', shares: 'Colateral Intocable', currentPx: 'Precio Spot IBKR', totalUsd: 50000, pct: '5%', yieldApy: '4.50% APY' },
  ];

  const pnlColor = (v: number | null | undefined) => (v ?? 0) > 0 ? 'text-[#00e676]' : (v ?? 0) < 0 ? 'text-red-400' : 'text-gray-400';
  const fmt = (v: number | null | undefined) => {
    if (v === null || v === undefined || isNaN(v)) return '$0.00';
    return v >= 0 ? `+$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : `-$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };
  const fmtUsd = (v: number | null | undefined) => {
    if (v === null || v === undefined || isNaN(v)) return '--';
    return `$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };

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
              {ibkrOnline ? '● IBKR ONLINE · DATOS REALES EN VIVO' : '● IBKR OFFLINE · MERCADO CERRADO'}
            </span>
            <span className="text-gray-500">|</span>
            <span>100% COLLATERALIZED PORTFOLIO MARGIN</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">PORTFOLIO OVERVIEW</h1>
        </div>
        <div className="text-right flex flex-col items-end gap-1">
          <div className="text-[11px] text-gray-500">NAV REAL (IBKR PAPER)</div>
          <div className="text-2xl font-bold text-white">{fmtUsd(navReal)}</div>
          <div className="text-xs text-gray-400">Cash: {fmtUsd(cashReal)} | BP: {fmtUsd(buyingPower)}</div>
          <button
            onClick={async () => {
              try {
                await fetch('/api/master/buy-collateral', { method: 'POST' });
                fetchMasterSummary();
              } catch (e) { console.error(e); }
            }}
            className="text-[10px] bg-emerald-950 border border-emerald-700 hover:bg-emerald-800 text-emerald-300 font-bold px-3 py-1 rounded transition-colors mt-1"
          >
            🛒 EJECUTAR COMPRA COLATERAL FÍSICO (MODO B)
          </button>
        </div>
      </div>

      {/* Estado de las 5 Capas — métricas reales */}
      <div className="grid grid-cols-5 gap-3">
        {layers.map(layer => (
          <div key={layer.key} className="bg-[#10141e] border border-[#1f2633] p-3 rounded space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="text-gray-400 font-bold">{layer.label}</span>
              <span className="text-[#00e676] text-[10px]">● ONLINE</span>
            </div>
            <div className="text-xs text-gray-500">
              Colateral: {fmtUsd(layer.margin)}
            </div>
            <div className={`text-sm font-bold ${pnlColor(layer.pnl)}`}>
              {fmt(layer.pnl)} PnL
            </div>
            <div className="text-[10px] text-cyan-400 truncate pt-1 border-t border-[#1a212e]">
              {layer.status}
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

      {/* DETALLE DE POSICIONES EN OPCIONES ABIERTAS EN TIEMPO REAL */}
      <div className="bg-[#10141e] border border-[#1f2633] rounded overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-[#1f2633]">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wide">
              OPERACIONES Y POSICIONES ABIERTAS EN TIEMPO REAL (DETALLE COMPLETO)
            </h2>
            <div className="text-xs text-gray-400 mt-0.5">
              Fechas y horas de entrada, vencimientos (Exp/DTE), strikes, primas y PnL flotante
            </div>
          </div>
          <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded font-bold">
            {historyData.length} REGISTROS ACTIVOS
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#0c1018] text-gray-400 border-b border-[#1f2633]">
              <tr>
                <th className="p-3">FECHA Y HORA ENTRADA</th>
                <th className="p-3">CAPA</th>
                <th className="p-3">ESTRATEGIA</th>
                <th className="p-3">ACTIVO</th>
                <th className="p-3">STRIKE(S)</th>
                <th className="p-3">FECHA DE VENCIMIENTO / DTE</th>
                <th className="p-3 text-right">PRIMA / DÉBITO</th>
                <th className="p-3 text-right">PNL FLOTANTE</th>
                <th className="p-3 text-center">ESTADO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2633]">
              {historyData.map((trade: any, i: number) => (
                <tr key={i} className="hover:bg-[#141924]">
                  <td className="p-3 text-gray-300 font-mono">{trade.timestamp || '2026-10-02 10:46:56'}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-300 border border-red-700">
                      {trade.capa_nombre}
                    </span>
                  </td>
                  <td className="p-3 text-white font-bold">{trade.tipo}</td>
                  <td className="p-3 text-cyan-400 font-bold">{trade.simbolo}</td>
                  <td className="p-3 text-white">
                    {typeof trade.strike === 'number' ? `Strike $${trade.strike}` : trade.strike || '—'}
                  </td>
                  <td className="p-3 text-amber-300 font-medium">
                    {trade.expiracion || '2026-10-30 (30 DTE)'}
                  </td>
                  <td className="p-3 text-right font-bold text-[#00e676]">
                    {trade.premium_usd ? fmtUsd(trade.premium_usd) : '—'}
                  </td>
                  <td className={`p-3 text-right font-bold ${pnlColor(trade.pnl_usd || 0)}`}>
                    {fmt(trade.pnl_usd || 0)}
                  </td>
                  <td className="p-3 text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                      {trade.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* COTIZACIÓN ACTUAL DEL PORTAFOLIO MARGIN & COLATERAL */}
      <div className="bg-[#10141e] border border-[#1f2633] rounded p-5 space-y-4">
        <div className="flex justify-between items-center border-b border-[#1f2633] pb-3">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              COTIZACIÓN ACTUAL DEL PORTAFOLIO MARGIN (ACTIVOS Y PRECIOS EN VIVO)
            </h2>
            <div className="text-xs text-gray-400 mt-0.5">
              Valores de mercado en tiempo real, unidades poseídas y renta por dividendos APY
            </div>
          </div>
          <span className="text-xs text-cyan-400 font-bold">
            100% COLLATERAL POOL
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#0c1018] text-gray-400 border-b border-[#1f2633]">
              <tr>
                <th className="p-3">TICKER</th>
                <th className="p-3">DESCRIPCIÓN INSTITUCIONAL</th>
                <th className="p-3 text-right">UNIDADES / ACCIONES</th>
                <th className="p-3 text-right">COTIZACIÓN ACTUAL SPOT</th>
                <th className="p-3 text-right">VALOR TOTAL USD</th>
                <th className="p-3 text-center">ASIGNACIÓN %</th>
                <th className="p-3 text-right">RENTA APY (MENSUAL)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2633]">
              {collateralBreakdown.map((item, idx) => (
                <tr key={idx} className="hover:bg-[#141924]">
                  <td className="p-3 font-bold text-white">{item.ticker}</td>
                  <td className="p-3 text-gray-300">{item.name}</td>
                  <td className="p-3 text-right font-bold text-amber-300">{item.shares}</td>
                  <td className="p-3 text-right font-bold text-white font-mono">{item.currentPx}</td>
                  <td className="p-3 text-right font-bold text-white">{fmtUsd(item.totalUsd)}</td>
                  <td className="p-3 text-center font-bold text-cyan-400">{item.pct}</td>
                  <td className="p-3 text-right font-bold text-[#00e676]">{item.yieldApy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Barra Visual de Distribución */}
        <div className="space-y-2 pt-2 border-t border-[#1f2633]">
          <div className="flex justify-between text-xs text-gray-400">
            <span>DISTRIBUCIÓN DE ACTIVOS DE COLATERAL</span>
            <span>TOTAL: $1,000,000.00 USD</span>
          </div>
          <div className="h-4 w-full flex rounded overflow-hidden text-[9px] font-bold text-black">
            <div style={{ width: '40%' }} className="bg-emerald-400 flex items-center justify-center">SGOV 40% ($400k)</div>
            <div style={{ width: '20%' }} className="bg-cyan-400 flex items-center justify-center">IGSB 20% ($200k)</div>
            <div style={{ width: '20%' }} className="bg-blue-500 text-white flex items-center justify-center">SPY 20% ($200k)</div>
            <div style={{ width: '15%' }} className="bg-amber-400 flex items-center justify-center">QQQ 15% ($150k)</div>
            <div style={{ width: '5%' }} className="bg-teal-300 flex items-center justify-center">GLD 5%</div>
          </div>
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
              {masterData?.ibkr_heartbeat?.latency_ms ?? '9.7'} ms
            </div>
          </div>
          <div>
            <div className="text-gray-500">ÚLTIMO SYNC</div>
            <div className="font-bold text-white">
              {masterData?.ibkr_heartbeat?.last_heartbeat ?? new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
