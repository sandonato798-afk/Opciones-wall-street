import React, { useState } from 'react';
import type { LayerId } from './types/darq';
import { TerminalLayout } from './components/TerminalLayout';
import { HomeView } from './views/HomeView';
import { RuedaView } from './views/RuedaView';
import { AlphaTradeView } from './views/AlphaTradeView';
import { RsiView } from './views/RsiView';
import { DaytradingView } from './views/DaytradingView';
import { BullMarketView } from './views/BullMarketView';
import { GlobalLedgerView } from './views/GlobalLedgerView';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<LayerId>('HOME');

  const renderContent = () => {
    switch (currentTab) {
      case 'HOME':
        return <HomeView />;
      case 'RUEDA':
        return <RuedaView />;
      case 'ALPHA':
        return <AlphaTradeView />;
      case 'RSI':
        return <RsiView />;
      case 'DAYTRADING':
        return <DaytradingView />;
      case 'BULL_MARKET':
        return <BullMarketView />;
      case 'GLOBAL_LEDGER':
        return <GlobalLedgerView />;
      default:
        return <HomeView />;
    }
  };

  return (
    <TerminalLayout currentTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </TerminalLayout>
  );
};

export default App;
