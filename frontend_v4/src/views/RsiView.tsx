import React from 'react';

export const RsiView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded font-bold">CAPA 3 ACTIVADA</span>
            <span className="text-xs text-[#00e676]">● SCANNER 1DTE V-CRUSH ONLINE</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">RSI OPORTUNISTA <span className="text-sm font-normal text-gray-400">(VENTA DE PUTS 1DTE EN PÁNICO RSI &lt; 30)</span></h1>
        </div>
        <div className="flex gap-2">
          <button className="text-xs bg-[#00e676] hover:bg-[#00c853] text-black font-bold px-3 py-2 rounded">
            CERRAR AL 50% TP (+$295.00)
          </button>
          <button className="text-xs border border-[#1f2633] text-gray-300 px-3 py-2 rounded">
            MONITOREO 15:55 EST
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">MARGEN EN USO</div>
          <div className="text-2xl font-bold text-white mt-1">$14,726.00</div>
          <div className="text-xs text-gray-500 mt-1">Pool Unificado D+ARQ (100% Capacidad)</div>
        </div>

        <div className="bg-[#10141e] border border-red-900/60 p-4 rounded bg-red-950/20">
          <div className="text-[11px] text-red-400 uppercase font-bold">RSI ACTUAL (SPY M5)</div>
          <div className="text-2xl font-bold text-red-400 mt-1">28.4 <span className="text-xs font-normal text-red-300">SOBREVENTA &lt; 30</span></div>
          <div className="text-xs text-red-300 mt-1">Clímax Vendedor Detectado</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">SEÑALES ACTIVAS</div>
          <div className="text-2xl font-bold text-white mt-1">3 <span className="text-xs font-normal text-gray-400">QQQ, SPY, IWM</span></div>
          <div className="text-xs text-gray-500 mt-1">1 Posición Viva · 2 Pendientes Confirmación</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PNL TOTAL ACUMULADO</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+$509.00 <span className="text-xs font-normal text-[#00e676]">100% WR</span></div>
          <div className="text-xs text-gray-500 mt-1">3/3 Trades Ejecutados (0 Fallas)</div>
        </div>
      </div>

      {/* Regla Rigurosa 50% TP */}
      <div className="bg-[#10141e] border border-emerald-900/60 p-4 rounded flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-emerald-950 border border-emerald-700 flex items-center justify-center text-[#00e676] font-bold">✓</div>
          <div>
            <div className="text-xs font-bold text-white">PROTOCOLO RIGUROSO DE SALIDA 50% TP (REGLA PRIMA CERO)</div>
            <div className="text-[11px] text-gray-400">Toda venta de Put en pánico se cierra automáticamente al capturar el 50% de la prima recibida o antes de las 15:55 EST.</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-gray-400">TIMER CIERRE OBLIGATORIO</div>
          <div className="text-sm font-bold text-red-400 font-mono">02h : 18m : 42s</div>
        </div>
      </div>

      {/* Matriz Forense de Posición Activa */}
      <div className="bg-[#10141e] border border-[#1f2633] p-5 rounded space-y-4">
        <div className="flex justify-between items-center border-b border-[#1f2633] pb-3">
          <div>
            <span className="text-lg font-bold text-white">QQQ PUT OTM $736.30</span>
            <span className="ml-2 text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">EN CURSO // TP LISTO</span>
            <div className="text-xs text-gray-400 mt-0.5">Venta sistemática de volatilidad implícita en pico de pánico RSI 26.8</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-[#00e676] font-bold">100.0% CAPTURADO (TARGET HIT)</div>
            <div className="text-xl font-bold text-[#00e676]">+$295.00</div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 text-xs">
          <div className="space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">1. ESPECIFICACIÓN</div>
            <div>Activo: <span className="text-white font-bold">QQQ (NASDAQ 100)</span></div>
            <div>Strike: <span className="text-white font-bold">$736.30 PUT</span></div>
            <div>Buffer Seguridad: <span className="text-[#00e676]">3.50% de Cojín OTM</span></div>
          </div>
          <div className="space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">2. ENTRADA EN CLÍMAX</div>
            <div>Timestamp: <span className="text-white">09:41:12 EST</span></div>
            <div>RSI Entrada: <span className="text-red-400 font-bold">26.8 (Pánico Puro)</span></div>
            <div>Prima Recibida: <span className="text-[#00e676]">+$2.95 / sh</span></div>
          </div>
          <div className="space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">3. ESTATUS EN CURSO</div>
            <div>Estatus: <span className="text-[#00e676] font-bold">TAKE PROFIT LISTO</span></div>
            <div>Prima Actual: <span className="text-[#00e676]">$0.04 / $0.05</span></div>
            <div>Distancia Strike: <span className="text-[#00e676]">+1.01% OTM Safe</span></div>
          </div>
          <div className="space-y-1">
            <div className="text-gray-500 uppercase text-[10px]">4. Griegas & Cierre</div>
            <div>Delta: <span className="text-cyan-400">Δ -0.08</span></div>
            <div>Theta: <span className="text-[#00e676]">+ $42.10 / día</span></div>
            <div>IV Crush: <span className="text-[#00e676] font-bold">-14.2%</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
