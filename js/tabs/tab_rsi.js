// js/tabs/tab_rsi.js - Lógica de la Capa 3: RSI Oportunista 1DTE

async function loadRsi() {
    try {
        const res = await fetch('/api/rsi-opportunistic/status');
        if(!res.ok) return;
        const data = await res.json();
        const marginUsed = (data.open_trades || []).reduce((acc, t) => acc + (t.margin_required_usd || ((t.put_strike || t.strike || 0) * 100 * (t.contracts || 1) * 0.20) || 0), 0);
        setTxt('rsi-cap', formatUSD(marginUsed));
        
        const rsiVal = data.current_market_indicators?.SPY?.rsi || 30.0;
        setTxt('rsi-val', Number(rsiVal).toFixed(1));
        setClass('rsi-val', 'val ' + (rsiVal < 30 ? 'text-red' : (rsiVal > 70 ? 'text-green' : '')));
        
        const totalOpps = (data.open_trades?.length || 0) + (data.closed_trades?.length || 0);
        setTxt('rsi-opps', totalOpps);
        
        const totalPnl = data.total_pnl_usd || 0;
        setTxt('rsi-pnl', sign(totalPnl) + formatUSD(totalPnl));
        setClass('rsi-pnl', 'val ' + colorClass(totalPnl));

        // 1. Tarjetas Interactivas & Posiciones Abiertas
        const cardsRsi = document.getElementById('rsi-active-cards');
        if (cardsRsi) {
            cardsRsi.innerHTML = '';
            if (data.open_trades && data.open_trades.length > 0) {
                data.open_trades.forEach(p => {
                    cardsRsi.innerHTML += renderActiveTradeCard(p, 'RSI 1DTE');
                });
            }
        }

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
