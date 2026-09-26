export type LayerId = 'HOME' | 'RUEDA' | 'ALPHA' | 'RSI' | 'DAYTRADING' | 'BULL_MARKET' | 'GLOBAL_LEDGER';

export type ProtocolStatus = 
  | 'ACTIVA' 
  | 'ACTIVO_ROLLEANDO' 
  | 'TAKE_PROFIT_50_LISTO' 
  | 'ALERTA_1555_ROLL_DEFENSIVO' 
  | 'EXPIRADO_CERO' 
  | 'DESACOPLADO_RISK_FREE';

export interface RollCycle {
  cycle: number;
  date: string;
  strike: number;
  credit: number;
  rebuy: number;
  net: number;
  status: string;
}

export interface TradePosition {
  id: string;
  layer: LayerId;
  layerTitle: string;
  ticker: string;
  strategy: string;
  strikeLong?: number;
  strikeShort?: number;
  strike?: number;
  dte: number;
  deltaNet: number;
  spotPrice: number;
  entryNet: number;
  currentRebuy: number;
  pnlFlotante: number;
  status: ProtocolStatus;
  statusLabel: string;
  protocolWarning?: string;
  breakEven?: number;
  rollCycles?: RollCycle[];
}

export interface PortfolioSummary {
  masterNav: number;
  initialCapital: number;
  pnlTotal: number;
  pnlPercentage: number;
  roiAnualizado: number;
  maxDrawdown: number;
  thetaDiario: number;
  thetaGlobalTotal: number;
  margenLibre: number;
  margenUsoPorcentaje: number;
  winRate: number;
  tradesPositivos: number;
  tradesTotales: number;
}
