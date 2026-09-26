import React from 'react';

export const AlphaTradeView: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-[#1f2633] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-red-950 text-red-300 border border-red-700 px-2 py-0.5 rounded font-bold">ALPHA ENGINE</span>
            <span className="text-xs text-cyan-400">DELTA PORTFOLIO +0.86 Δ</span>
            <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">MODO: LIBRE (DESACOPLADO)</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide mt-1">CAPA 2: ALPHA TRADE <span className="text-sm font-normal text-gray-400">(SINTÉTICOS LEAPS A COSTO CERO)</span></h1>
        </div>
        <button className="bg-red-600 hover:bg-red-500 text-white font-bold text-xs px-4 py-2 rounded">
          DESACOPLAR PUT (RECOMPRA)
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">MARGEN EN USO</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">$0.00</div>
          <div className="text-xs text-gray-500 mt-1">Pool 100% Liberado | Colateral en Riesgo: $0.00</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">VALOR LONG CALLS</div>
          <div className="text-2xl font-bold text-white mt-1">$10,274.00</div>
          <div className="text-xs text-gray-400 mt-1">2 Contratos Strike $715 (In The Money)</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">COSTO RECOMPRA PUT</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">$0.00</div>
          <div className="text-xs text-[#00e676] mt-1">Cerrada a $0.05 ($10.00 Total) · Efectivo Libre: +$1,440</div>
        </div>

        <div className="bg-[#10141e] border border-[#1f2633] p-4 rounded">
          <div className="text-[11px] text-gray-400 uppercase">PNL NO REALIZADO TOTAL</div>
          <div className="text-2xl font-bold text-[#00e676] mt-1">+$10,274.00</div>
          <div className="text-xs text-[#00e676] mt-1">+121.5% ROC · Retorno sobre Riesgo: ∞</div>
        </div>
      </div>

      {/* Matriz Forense de 3 Columnas (Estándar Pantalla Alpha) */}
      <div className="bg-[#10141e] border border-[#1f2633] rounded overflow-hidden">
        <div className="p-4 border-b border-[#1f2633] flex justify-between items-center">
          <span className="text-sm font-bold text-white">QQQ — SINTÉTICO ZERO-COST LEAPS (ID: #178960001)</span>
          <span className="text-xs text-[#00e676] bg-emerald-950 border border-emerald-800 px-2.5 py-0.5 rounded">
            ● 100% RIESGO CERO (PUT DESACOPLADA)
          </span>
        </div>

        <table className="w-full text-xs">
          <thead className="bg-[#0c1018] text-gray-400 border-b border-[#1f2633]">
            <tr>
              <th className="p-3 text-left w-1/4">MÉTRICA AUDITADA</th>
              <th className="p-3 text-left w-1/4 text-red-400 font-bold">POSICIÓN SHORT (PUT CRÉDITO)</th>
              <th className="p-3 text-left w-1/4 text-cyan-400 font-bold">POSICIÓN LONG (CALL FINANCIADO)</th>
              <th className="p-3 text-left w-1/4 text-[#00e676] font-bold">COMBINADO (ESTRUCTURA AUDITADA)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f2633]">
            {/* Bloque 1 */}
            <tr className="bg-[#0f141f] text-[11px] font-bold text-gray-400">
              <td colSpan={4} className="px-3 py-1.5 uppercase">1. Especificación y Contratos</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Opción / Tipo Estructura</td>
              <td className="p-3 text-amber-300">PUT (Short Recomprado)</td>
              <td className="p-3 text-[#00e676]">CALL (Risk-Free Corriendo)</td>
              <td className="p-3 font-semibold text-white">Sintético Alcista Desacoplado</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Strike (K)</td>
              <td className="p-3 text-white font-bold">$670.00</td>
              <td className="p-3 text-white font-bold">$715.00</td>
              <td className="p-3 text-gray-300">K-Short $670 / K-Long $715</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Vencimiento & DTE</td>
              <td className="p-3 text-white">2027-01-03 (120 DTE)</td>
              <td className="p-3 text-white">2027-01-03 (120 DTE)</td>
              <td className="p-3 text-cyan-400">2027-01-03 (120 DTE Remanentes)</td>
            </tr>

            {/* Bloque 2 */}
            <tr className="bg-[#0f141f] text-[11px] font-bold text-gray-400">
              <td colSpan={4} className="px-3 py-1.5 uppercase">2. Condiciones de Apertura (Creación a Coste Cero)</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Precio Underlying Apertura</td>
              <td className="p-3 text-white">$692.50</td>
              <td className="p-3 text-white">$692.50</td>
              <td className="p-3 text-gray-400">Base Spot: $692.50</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Prima en Apertura</td>
              <td className="p-3 text-[#00e676] font-bold">+$7.25 / sh (Recibida)</td>
              <td className="p-3 text-red-400 font-bold">-$7.25 / sh (Pagada)</td>
              <td className="p-3 text-[#00e676] font-bold">$0.00 / sh (Paridad Cero)</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Neto Entrada</td>
              <td className="p-3 text-[#00e676] font-bold">+$1,450.00 (Cobrado)</td>
              <td className="p-3 text-red-400 font-bold">-$1,450.00 (Pagado)</td>
              <td className="p-3 text-white font-bold">$0.00 Inversión Inicial Neta</td>
            </tr>

            {/* Bloque 3 */}
            <tr className="bg-[#0f141f] text-[11px] font-bold text-gray-400">
              <td colSpan={4} className="px-3 py-1.5 uppercase">3. Cierre y Estatus Operativo (Desacople)</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Estatus de Mercado</td>
              <td className="p-3 text-[#00e676]">Recomprada ($0.05 / sh)</td>
              <td className="p-3 text-[#00e676] font-bold">● EN CURSO (Corriendo)</td>
              <td className="p-3 text-[#00e676]">Long Call Abierta Risk-Free</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Valor Actual / Recompra</td>
              <td className="p-3 text-white font-bold">$10.00 Total Cierre</td>
              <td className="p-3 text-[#00e676] font-bold">+$10,274.00 (Valor Flotante)</td>
              <td className="p-3 text-[#00e676] font-bold">+$10,264.00 Retorno Neto Sintético</td>
            </tr>

            {/* Bloque 4 */}
            <tr className="bg-[#0f141f] text-[11px] font-bold text-gray-400">
              <td colSpan={4} className="px-3 py-1.5 uppercase">4. Balance Final y Retorno</td>
            </tr>
            <tr>
              <td className="p-3 text-gray-400">Ganancia Neta Total</td>
              <td className="p-3 text-[#00e676] font-bold">+$1,440.00</td>
              <td className="p-3 text-[#00e676] font-bold">+$8,824.00</td>
              <td className="p-3 text-[#00e676] text-sm font-bold">+$10,264.00 (Beneficio Consolidado)</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
