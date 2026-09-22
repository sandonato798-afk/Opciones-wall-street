// js/tabs/tab_rsi.js - Lógica de la Capa 3: RSI Oportunista 1DTE

async function loadRsi() {
    try {
        const res = await fetch('/api/rsi-opportunistic/status');
        if(!res.ok) return;
        const data = await res.json();
        const allocCap = data.allocated_capital || 15000;
        const totalPnl = data.total_pnl_usd || 0;
        setTxt('rsi-cap', formatUSD(allocCap + totalPnl));
        
        const rsiVal = data.current_market_indicators?.SPY?.rsi || 30.0;
        setTxt('rsi-val', Number(rsiVal).toFixed(1));
        setClass('rsi-val', 'val ' + (rsiVal < 30 ? 'text-red' : (rsiVal > 70 ? 'text-green' : '')));
        
        const totalOpps = (data.open_trades?.length || 0) + (data.closed_trades?.length || 0);
        setTxt('rsi-opps', totalOpps);
        
        setTxt('rsi-pnl', sign(totalPnl) + formatUSD(totalPnl));
        setClass('rsi-pnl', 'val ' + colorClass(totalPnl));

        // 1. Operaciones 1DTE Abiertas
        const tbodyPos = document.getElementById('rsi-positions');
        if (tbodyPos) {
            tbodyPos.innerHTML = '';
            if(data.open_trades && data.open_trades.length > 0) {
                data.open_trades.forEach(p => {
                    tbodyPos.innerHTML += render15MetricsRow(p, true);
                });
            } else {
                tbodyPos.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">Sin operaciones abiertas. Escaneando mercado para caídas con RSI &lt; 30.</td></tr>';
            }
        }

        // 2. Historial de Operaciones 1DTE Cerradas
        const tbodyHist = document.getElementById('rsi-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_trades && data.closed_trades.length > 0) {
                data.closed_trades.slice().reverse().forEach(p => {
                    tbodyHist.innerHTML += render15MetricsRow(p, false);
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">No hay operaciones 1DTE cerradas registradas</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadRsi', e); }
}
