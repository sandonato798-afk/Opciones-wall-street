// js/tabs/tab_bullmarket.js - Lógica de la Capa 5: Bull Market PMCC (Diagonal Spread Alcista)

async function loadBullMarket() {
    try {
        const res = await fetch('/api/bullmarket/status');
        if(!res.ok) return;
        const data = await res.json();
        const totalPnl = data.total_pnl_usd || 0;
        const totalTheta = data.total_theta_collected_usd || 0;
        
        let totalLongVal = 0;
        let marginUsed = 0;
        if (data.open_diagonals && data.open_diagonals.length > 0) {
            totalLongVal = data.open_diagonals.reduce((acc, d) => acc + (d.long_call_current_value_usd || d.long_call_premium_paid || 0), 0);
            marginUsed = data.open_diagonals.reduce((acc, d) => acc + (d.margin_required_usd || d.long_call_premium_paid || 0), 0);
        }
        
        setTxt('bm-cap', formatUSD(marginUsed));
        setTxt('bm-long-val', formatUSD(totalLongVal));
        setTxt('bm-theta-val', '+' + formatUSD(totalTheta));
        setTxt('bm-pnl', sign(totalPnl) + formatUSD(totalPnl));
        setClass('bm-pnl', 'val ' + colorClass(totalPnl));

        // 1. Posiciones PMCC Abiertas y Cerradas
        const tbodyPos = document.getElementById('bullmarket-positions');
        if (tbodyPos) {
            tbodyPos.innerHTML = '';
            let count = 0;
            if(data.open_diagonals && data.open_diagonals.length > 0) {
                data.open_diagonals.forEach(p => {
                    tbodyPos.innerHTML += renderBullMarketMatrixTable(p, true);
                    count++;
                });
            }
            if(data.closed_diagonals && data.closed_diagonals.length > 0) {
                data.closed_diagonals.forEach(p => {
                    tbodyPos.innerHTML += renderBullMarketMatrixTable(p, false);
                    count++;
                });
            }
            if (count === 0) {
                tbodyPos.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);">No hay posiciones Poor Man’s Covered Call abiertas en este momento.</div>';
            }
        }

        // 2. Historial de Rolleos Semanales
        const tbodyRolls = document.getElementById('bullmarket-rolls-history');
        if(tbodyRolls) {
            tbodyRolls.innerHTML = '';
            if(data.weekly_rolls_history && data.weekly_rolls_history.length > 0) {
                data.weekly_rolls_history.slice().reverse().forEach(r => {
                    tbodyRolls.innerHTML += `
                    <tr>
                        <td><strong>${r.roll_date || '-'}</strong></td>
                        <td><strong>${r.symbol || 'SPY'}</strong></td>
                        <td><span class="badge-short">Ciclo #${r.cycle_num || 1}</span></td>
                        <td>$${r.short_strike || '-'}</td>
                        <td>${r.expiration || '-'}</td>
                        <td class="text-green">+${formatUSD(r.premium_collected_usd)}</td>
                        <td class="text-red">-${formatUSD(r.recompra_paid_usd)}</td>
                        <td class="text-green"><strong>+${formatUSD(r.net_theta_profit_usd)}</strong></td>
                        <td><span class="badge-long">${r.status || 'ROLLED'}</span></td>
                    </tr>`;
                });
            } else {
                tbodyRolls.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-muted);">No hay rolleos semanales registrados aún</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadBullMarket', e); }
}

async function runBullMarketRoll() {
    try {
        await fetch('/api/bullmarket/roll', { method: 'POST' });
        await refreshAllData();
    } catch(e) { console.error('Error runBullMarketRoll', e); }
}

async function openBullMarketPMCC() {
    try {
        await fetch('/api/bullmarket/open', { method: 'POST' });
        await refreshAllData();
    } catch(e) { console.error('Error openBullMarketPMCC', e); }
}
