// js/tabs/tab_daytrade.js - Lógica de la Capa 4: Daytrading Intradía ITM

async function loadDaytrade() {
    try {
        const res = await fetch('/api/daytrade/status');
        if(!res.ok) return;
        const data = await res.json();
        setTxt('dt-cap', formatUSD(10000 + (data.total_pnl_usd || 0)));
        
        let wr = data.stats?.win_rate || 0;
        setTxt('dt-wr', formatPct(wr));
        
        setTxt('dt-mode', data.config?.execution_mode || 'PAPER');
        setTxt('dt-pnl', sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd));
        setClass('dt-pnl', 'val ' + colorClass(data.total_pnl_usd));

        // 1. Posiciones Intradía Abiertas
        const tbodyOpen = document.getElementById('dt-open-positions');
        if (tbodyOpen) {
            tbodyOpen.innerHTML = '';
            if(data.open_positions && data.open_positions.length > 0) {
                data.open_positions.forEach(p => {
                    tbodyOpen.innerHTML += render15MetricsRow(p, true);
                });
            } else {
                tbodyOpen.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">Sin posiciones abiertas en este momento. Escaneando señales intradiarias cada 60s.</td></tr>';
            }
        }

        // 2. Historial de Operaciones Intradía Cerradas
        const tbodyHist = document.getElementById('dt-history');
        if (tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_trades && data.closed_trades.length > 0) {
                data.closed_trades.slice().reverse().forEach(p => {
                    tbodyHist.innerHTML += render15MetricsRow(p, false);
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">No hay historial de operaciones cerradas</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadDaytrade', e); }
}

async function runDaytradeScan() {
    try {
        await fetch('/api/daytrade/scan', { method: 'POST' });
        await refreshAllData();
    } catch(e) { console.error('Error runDaytradeScan', e); }
}

async function togglePaperLive() {
    try {
        const mode = document.getElementById('dt-mode').innerText === 'PAPER' ? 'LIVE_BROKER' : 'PAPER_TRADING';
        await fetch('/api/daytrade/mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: mode, broker: 'INTERACTIVE_BROKERS'})
        });
        await refreshAllData();
    } catch(e) { console.error('Error togglePaperLive', e); }
}
