import React from 'react';
import type { LayerId } from '../types/darq';
import { portfolioSummary } from '../data/mockData';

interface Props {
  currentTab: LayerId;
  onSelectTab: (tab: LayerId) => void;
  children: React.ReactNode;
}

export const TerminalLayout: React.FC<Props> = ({ currentTab, onSelectTab, children }) => {
  const menuItems: { id: LayerId; label: string; badge?: string }[] = [
    { id: 'HOME', label: 'HOME (OVERVIEW)' },
    { id: 'RUEDA', label: 'RUEDA (CAPA 1)' },
    { id: 'ALPHA', label: 'ALPHA (CAPA 2)' },
    { id: 'RSI', label: 'RSI (CAPA 3)' },
    { id: 'DAYTRADING', label: 'DAYTRADING (CAPA 4)', badge: '15:55' },
    { id: 'BULL_MARKET', label: 'BULL MARKET PMCC (CAPA 5)' },
    { id: 'GLOBAL_LEDGER', label: 'REPOSITORIO GLOBAL' },
  ];

  return (
    <div className="flex h-screen w-screen bg-[#0a0e16] text-gray-200 font-mono select-none overflow-hidden">
      {/* Sidebar Izquierda */}
      <aside className="w-64 border-r border-[#1f2633] bg-[#0c1018] flex flex-col justify-between shrink-0">
        <div>
          {/* Logo Header */}
          <div className="p-4 border-b border-[#1f2633] flex items-center gap-2">
            <div className="w-7 h-7 bg-[#00e676] rounded flex items-center justify-center font-bold text-black text-sm">
              D+
            </div>
            <div>
              <div className="font-bold text-sm tracking-wider text-white">D+ARQ TERMINAL</div>
              <div className="text-[10px] text-gray-500">OPTIONS V4.2 MIL-SPEC</div>
            </div>
          </div>

          {/* Menú de Capas */}
          <nav className="p-3 space-y-1">
            <div className="text-[10px] text-gray-500 uppercase px-2 mb-2 font-bold tracking-wider">Trading Layers</div>
            {menuItems.map(item => {
              const active = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded text-xs transition ${
                    active 
                      ? 'bg-red-950/70 border-l-4 border-red-500 text-white font-bold' 
                      : 'text-gray-400 hover:bg-[#141a24] hover:text-gray-200'
                  }`}
                >
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className="text-[9px] bg-red-900/60 border border-red-600 text-red-300 px-1 rounded animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Telemetría Footer Sidebar */}
        <div className="p-3 border-t border-[#1f2633] text-[11px] text-gray-500 space-y-1">
          <div className="flex justify-between">
            <span>NETWORK</span>
            <span className="text-[#00e676]">● 14ms | NY4</span>
          </div>
          <div className="flex justify-between">
            <span>SYNTH POOL</span>
            <span className="text-[#00e5ff]">DELTA +0.182 Δ</span>
          </div>
          <div className="flex justify-between">
            <span>AUDIT LEDGER</span>
            <span className="text-gray-400">HASH 8A4F..01</span>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 border-b border-[#1f2633] bg-[#0c1018] px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-xs">
              <span className="w-2 h-2 rounded-full bg-[#00e676] animate-pulse"></span>
              <span className="text-white font-bold">SYSTEM LIVE</span>
            </div>
            <div className="text-xs text-gray-400">
              PORTFOLIO NAV: 
              <span className="text-white font-bold mx-2">${portfolioSummary.masterNav.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              <span className="text-[#00e676] font-bold">+{portfolioSummary.pnlPercentage}%</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="text-xs border border-[#1f2633] hover:border-gray-500 px-3 py-1.5 rounded text-gray-300">
              ESCANEAR SEÑALES
            </button>
            <button className="text-xs bg-red-600 hover:bg-red-500 text-white font-bold px-3 py-1.5 rounded">
              EXPORTAR AUDITORÍA
            </button>
          </div>
        </header>

        {/* Renderizado de Pantalla */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0a0e16]">
          {children}
        </main>
      </div>
    </div>
  );
};
