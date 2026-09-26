import React, { useState } from 'react';
import type { LayerId } from './types/darq';
import { TerminalLayout } from './components/TerminalLayout';
import { GlobalLedgerView } from './views/GlobalLedgerView';
import { BullMarketView } from './views/BullMarketView';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<LayerId>('GLOBAL_LEDGER');

  const renderContent = () => {
    switch (currentTab) {
      case 'GLOBAL_LEDGER':
        return <GlobalLedgerView />;
      case 'BULL_MARKET':
        return <BullMarketView />;
      default:
        return <GlobalLedgerView />;
    }
  };

  return (
    <TerminalLayout currentTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </TerminalLayout>
  );
};

export default App;
