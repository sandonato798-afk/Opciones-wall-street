import React, { useState, useEffect } from 'react';

export const GlobalLedgerView: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('TODAS');
  const [lastRefresh, setLastRefresh] = useState<string>('—');

  const fetchData = () => {
    fetch('/api/ibkr/positions')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLastRefresh(new Date().toLocaleTimeString('es-AR'));
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh cada 30 segundos durante horario de mercado
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00e676] animate-pulse text-sm font-mono">
          ● SINCRONIZANDO CON IBKR PAPER TRADING...
        </div>
      </div>
    );
  }

  const connected = data?.ibkr_connected ?? false;
  const account = data?.account || {};
  const totals = data?.portfolio_totals || {};
  const positions: any[] = data?.positions || [];
  const options: any[] = data?.options || [];
  const stocks: any[] = data?.stocks || [];

  const filtered = filterType === 'TODAS' ? positions
    : filterType === 'OPT' ? options
    : stocks;

  const fmtUsd = (v: number) => `$${(v ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  const fmtPnl = (v: number) => {
    if (!v && v !== 0) return '—';
    return v >= 0
      ? `+$${v.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
      : `-$${Math.abs(v).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  };
  const pnlColor = (v: number) => v > 0 ? 'text-[#00e676]' : v < 0 ? 'text-red-400' : 'text-gray-400';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-[#00e676] animate-pulse' : 'bg-red-500'}`}></span>
            <span className={`text-xs font-bold ${connected ? 'text-[#00e676]' : 'text-red-400'}`}>
              {connected ? 'IBKR PAPER TRADING — ESPEJO EN VIVO' : 'IBKR OFFLINE — DATOS CUANDO CONECTE'}
            </span>
            <span className="text-gray-500 text-xs">Latencia: {data?.ibkr_latency_ms ?? '—'} ms</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">
            REPOSITORIO GLOBAL <span className="text-sm font-normal text-gray-400">— PORTFOLIO IBKR REAL</span>
          </h1>
          <div className="text-xs text-gray-500 mt-1">Último sync: {lastRefresh} | Auto-refresh: 30s</div>
        </div>
        <button
          onClick={fetchData}
          className="text-xs bg-[#141a24] border border-[#1f2633] hover:border-[#00e676] text-gray-300 hover:text-[#00e676] px-4 py-2 rounded transition-colors"
        >
          ↻ FORZAR SYNC
        </button>
      </div>

      {/* KPIs de Cuenta — datos 100% IBKR */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">NAV REAL (NET LIQUIDATION)</div>
          <div className="text-2xl font-bold text-white mt-1">{fmtUsd(account.nav)}</div>
          <div className="text-xs text-gray-500 mt-1">Fuente: IBKR accountValues()</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">CASH DISPONIBLE</div>
          <div className="text-2xl font-bold text-white mt-1">{fmtUsd(account.cash)}</div>
          <div className="text-xs text-gray-500 mt-1">TotalCashValue · Settled Cash</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PnL NO REALIZADO</div>
          <div className={`text-2xl font-bold mt-1 ${pnlColor(account.unrealized_pnl)}`}>
            {fmtPnl(account.unrealized_pnl)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Posiciones Abiertas · IBKR Real</div>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PnL REALIZADO (YTD)</div>
          <div className={`text-2xl font-bold mt-1 ${pnlColor(account.realized_pnl)}`}>
            {fmtPnl(account.realized_pnl)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Operaciones Cerradas · IBKR Real</div>
        </div>
      </div>

      {/* Resumen del Portfolio */}
      <div className="grid grid-cols-3 gap-4 text-xs">
        <div className="bg-[#10141e] border border-[#1f2633] p-3 rounded flex justify-between items-center">
          <span className="text-gray-400">TOTAL POSICIONES</span>
          <span className="text-white font-bold text-lg">{totals.total_positions ?? 0}</span>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-3 rounded flex justify-between items-center">
          <span className="text-gray-400">OPCIONES ABIERTAS</span>
          <span className="text-cyan-400 font-bold text-lg">{totals.total_options ?? 0}</span>
        </div>
        <div className="bg-[#10141e] border border-[#1f2633] p-3 rounded flex justify-between items-center">
          <span className="text-gray-400">VALOR DE MERCADO TOTAL</span>
          <span className="text-white font-bold text-lg">{fmtUsd(totals.total_market_value ?? 0)}</span>
        </div>
      </div>

      {/* Tabla de Posiciones — espejo exacto IBKR */}
      <div className="bg-[#10141e] border border-[#1f2633] rounded overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-[#1f2633]">
          <span className="text-sm font-bold text-white uppercase">
            POSICIONES ABIERTAS — IBKR PAPER ACCOUNT
          </span>
          <div className="flex gap-2">
            {['TODAS', 'OPT', 'STK'].map(f => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                className={`text-[11px] px-3 py-1 rounded border transition-colors ${
                  filterType === f
                    ? 'bg-[#00e676] text-black border-[#00e676] font-bold'
                    : 'text-gray-400 border-[#1f2633] hover:border-[#00e676]'
                }`}
              >
                {f === 'TODAS' ? 'TODAS' : f === 'OPT' ? 'OPCIONES' : 'ACCIONES'}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <div className="text-[#00e676] text-lg font-bold">
              {connected ? '✓ CUENTA LIMPIA' : '⏳ ESPERANDO CONEXIÓN IBKR'}
            </div>
            <div className="text-gray-400 text-sm">
              {connected
                ? 'No hay posiciones abiertas en tu cuenta paper de IBKR. El sistema abrirá posiciones reales el lunes cuando el mercado abra a las 09:30 EST.'
                : 'Iniciá IB Gateway para ver las posiciones en vivo.'}
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-[#0c1018] text-gray-400 border-b border-[#1f2633]">
                <tr>
                  <th className="p-3 text-left">SÍMBOLO</th>
                  <th className="p-3 text-left">TIPO</th>
                  <th className="p-3 text-left">POSICIÓN</th>
                  <th className="p-3 text-left">STRIKE / EXP</th>
                  <th className="p-3 text-right">PRECIO MKTV</th>
                  <th className="p-3 text-right">VALOR MERCADO</th>
                  <th className="p-3 text-right">COSTO PROM.</th>
                  <th className="p-3 text-right">PnL NO REAL.</th>
                  <th className="p-3 text-right">PnL REAL.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2633]">
                {filtered.map((pos: any, i: number) => (
                  <tr key={i} className="hover:bg-[#141924] transition-colors">
                    <td className="p-3 font-bold text-white">{pos.symbol}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        pos.sec_type === 'OPT'
                          ? 'bg-cyan-950 text-cyan-300 border-cyan-800'
                          : 'bg-blue-950 text-blue-300 border-blue-800'
                      }`}>
                        {pos.sec_type === 'OPT'
                          ? `${pos.right === 'C' ? 'CALL' : 'PUT'}`
                          : 'ACCIÓN'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`font-bold ${pos.position < 0 ? 'text-red-400' : 'text-[#00e676]'}`}>
                        {pos.position > 0 ? '+' : ''}{pos.position}
                        <span className="text-gray-500 font-normal ml-1">
                          {pos.position < 0 ? 'SHORT' : 'LONG'}
                        </span>
                      </span>
                    </td>
                    <td className="p-3 text-gray-300">
                      {pos.sec_type === 'OPT'
                        ? `$${pos.strike} | ${pos.expiry}`
                        : '—'}
                    </td>
                    <td className="p-3 text-right text-white">{fmtUsd(pos.market_price)}</td>
                    <td className="p-3 text-right text-white">{fmtUsd(pos.market_value)}</td>
                    <td className="p-3 text-right text-gray-300">{fmtUsd(pos.avg_cost)}</td>
                    <td className={`p-3 text-right font-bold ${pnlColor(pos.unrealized_pnl)}`}>
                      {fmtPnl(pos.unrealized_pnl)}
                    </td>
                    <td className={`p-3 text-right ${pnlColor(pos.realized_pnl)}`}>
                      {fmtPnl(pos.realized_pnl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Nota de fuente de datos */}
      <div className="text-[11px] text-gray-600 text-center">
        Todos los datos provienen directamente de <span className="text-gray-400 font-bold">ib.portfolio()</span> — API nativa de Interactive Brokers.
        Espejo exacto de lo que muestra tu cuenta paper en TWS / IB Gateway.
      </div>
    </div>
  );
};
