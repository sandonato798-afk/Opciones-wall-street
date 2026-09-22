// js/tabs/tab_alpha.js - Lógica de la Capa 2: Alpha Sintéticos LEAPS Macro

async function loadAlpha() {
    try {
        const res = await fetch('/api/alpha/status');
        if(!res.ok) return;
        const data = await res.json();
        let putRisk = 0;
        if (data.open_positions && data.open_positions.length > 0) {
            putRisk = data.open_positions.reduce((acc, p) => acc + (p.short_put_current_buyback_cost || 0), 0);
        }
        setTxt('alpha-cap', formatUSD(putRisk));
        setTxt('alpha-risk', formatUSD(putRisk));
        
        const unrealizedPnl = data.total_unrealized_pnl_usd || 0;
        setTxt('alpha-leaps', formatUSD(unrealizedPnl));
        
        setTxt('alpha-pnl', sign(unrealizedPnl) + formatUSD(unrealizedPnl));
        setClass('alpha-pnl', 'val ' + colorClass(unrealizedPnl));

        // 1. Posiciones Sintéticas Abiertas y Long Calls (Estructura Short / Long / Combinado)
        const tbodyPos = document.getElementById('alpha-positions');
        if (tbodyPos) {
            tbodyPos.innerHTML = '';
            let count = 0;
            if(data.open_positions && data.open_positions.length > 0) {
                data.open_positions.forEach(p => {
                    tbodyPos.innerHTML += renderAlphaMatrixTable(p, true);
                    count++;
                });
            }
            if(data.decoupled_calls && data.decoupled_calls.length > 0) {
                data.decoupled_calls.forEach(p => {
                    tbodyPos.innerHTML += renderAlphaMatrixTable(p, true);
                    count++;
                });
            }
            if (count === 0) {
                tbodyPos.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);">No hay posiciones sintéticas abiertas en este momento.</div>';
            }
        }

        // 2. Historial de Alpha
        const tbodyHist = document.getElementById('alpha-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_positions && data.closed_positions.length > 0) {
                data.closed_positions.slice().reverse().forEach(p => {
                    tbodyHist.innerHTML += renderAlphaMatrixTable(p, false);
                });
            } else {
                tbodyHist.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);">Sin sintéticos cerrados aún en el historial (1 sintético QQQ en monitoreo).</div>';
            }
        }
    } catch(e) { console.error('Error loadAlpha', e); }
}

async function runAlphaDecouple() {
    try {
        await fetch('/api/alpha/decouple', { method: 'POST' });
        await refreshAllData();
    } catch(e) { console.error('Error runAlphaDecouple', e); }
}
