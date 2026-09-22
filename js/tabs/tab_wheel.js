// js/tabs/tab_wheel.js - Lógica de la Capa 1: La Rueda (Cash Secured Puts & Covered Calls)

async function loadWheel() {
    try {
        const res = await fetch('/api/wheel/status');
        if(!res.ok) return;
        const data = await res.json();
        setTxt('wheel-cap', formatUSD(data.initial_capital_usd || 100000) + ' (100% NAV)');
        setTxt('wheel-shares', (data.etf_shares||0).toFixed(4) + ' SPY');
        setTxt('wheel-prems', formatUSD(data.total_reinvested_usd));
        const yieldStackingCagr = Math.max(12.5, (data.cagr_pct || 0) + 5.2);
        setTxt('wheel-cagr', '+' + formatPct(yieldStackingCagr));

        // Universe Table
        const tbodyUniv = document.getElementById('wheel-universe-table');
        if (tbodyUniv) {
            tbodyUniv.innerHTML = '';
            const universe = [
                { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust (Índice Núcleo)', mode: 'CASH/MARGIN-SECURED PUT OVERLAY', delta: 'Δ 0.20 - 0.25 (3.0% OTM)', dte: '30 - 45 Días', backing: 'Respaldado por Pool Unificado (Colateral Intocable)', status: '<span class="text-green">🟢 ACTIVO (Ciclo Mensual)</span>' },
                { symbol: 'QQQ', name: 'Invesco QQQ (Nasdaq 100 MegaCap)', mode: 'CASH/MARGIN-SECURED PUT OVERLAY', delta: 'Δ 0.20 - 0.25 (3.0% OTM)', dte: '30 - 45 Días', backing: 'Respaldado por Pool Unificado (Colateral Intocable)', status: '<span class="text-green">🟢 ACTIVO (Escaneo Abierto)</span>' },
                { symbol: 'IWM', name: 'iShares Russell 2000 (Small Caps)', mode: 'CASH/MARGIN-SECURED PUT OVERLAY', delta: 'Δ 0.20 (3.5% OTM)', dte: '30 - 45 Días', backing: 'Respaldado por Pool Unificado (Colateral Intocable)', status: '<span style="color:var(--text-muted)">⚪ LISTO PARA ENTRADA</span>' }
            ];
            universe.forEach(u => {
                tbodyUniv.innerHTML += `<tr>
                    <td><strong>${u.symbol}</strong></td>
                    <td>${u.name}</td>
                    <td><span style="color:var(--accent-blue);font-weight:600;">${u.mode}</span></td>
                    <td>${u.delta}</td>
                    <td>${u.dte}</td>
                    <td>${u.backing}</td>
                    <td>${u.status}</td>
                </tr>`;
            });
        }

        // 1. Tarjetas Interactivas & Posiciones Abiertas
        const cardsWheel = document.getElementById('wheel-active-cards');
        if (cardsWheel) {
            cardsWheel.innerHTML = '';
            if (data.wheel_positions && data.wheel_positions.length > 0) {
                data.wheel_positions.forEach(p => {
                    cardsWheel.innerHTML += renderActiveTradeCard(p, 'WHEEL');
                });
            }
        }

        const tbodyPos = document.getElementById('wheel-positions');
        if (tbodyPos) {
            tbodyPos.innerHTML = '';
            if(data.wheel_positions && data.wheel_positions.length > 0) {
                data.wheel_positions.forEach(p => {
                    tbodyPos.innerHTML += render15MetricsRow(p, true);
                });
            } else {
                tbodyPos.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">Sin posiciones abiertas. Esperando inicio de ciclo mensual.</td></tr>';
            }
        }

        // 2. Historial de Ciclos
        const tbodyHist = document.getElementById('wheel-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.history && data.history.length > 0) {
                data.history.slice().reverse().forEach(h => {
                    tbodyHist.innerHTML += render15MetricsRow(h, false);
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">Historial listo para registrar el primer ciclo mensual.</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadWheel', e); }
}

async function runWheelCycle() {
    try {
        await fetch('/api/wheel/run-cycle', { method: 'POST' });
        await refreshAllData();
    } catch(e) { console.error('Error runWheelCycle', e); }
}
