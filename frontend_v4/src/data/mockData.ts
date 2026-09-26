export const portfolioSummary = {
  roiAnualizado: 18.5,
  maxDrawdown: 1.2,
  thetaDiario: 145,
  margenUsoPorcentaje: 0,
  margenLibre: 100000,
  masterNav: 100000,
  pnlPercentage: 0
};

export const collateralBreakdown = [
  { ticker: 'SGOV', desc: '0-3 Month T-Bill ETF', alloc: 40, value: 40000, reqMargin: 1, freedBp: 39600, yieldAnual: 2120 },
  { ticker: 'LQD', desc: 'iShares iBoxx $ Investment Grade', alloc: 20, value: 20000, reqMargin: 7, freedBp: 18600, yieldAnual: 1100 },
  { ticker: 'SPY', desc: 'SPDR S&P 500 ETF Trust', alloc: 20, value: 20000, reqMargin: 15, freedBp: 17000, yieldAnual: 280 },
  { ticker: 'QQQ', desc: 'Invesco QQQ Trust', alloc: 15, value: 15000, reqMargin: 15, freedBp: 12750, yieldAnual: 120 },
  { ticker: 'GLD', desc: 'SPDR Gold Shares', alloc: 5, value: 5000, reqMargin: 12, freedBp: 4400, yieldAnual: 0 },
];

export const activeTrades: any[] = [];
