// State
let appData = {};

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    refreshAllData();
    setInterval(refreshAllData, 15000);
});

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.dataset.tab;
            document.getElementById(target).classList.add('active');
        });
    });
}

async function refreshAllData() {
    await Promise.all([
        loadMaster(),
        loadWheel(),
        loadSpreads(),
        loadAlpha(),
        loadRsi(),
        loadDaytrade()
    ]);
}

function formatUSD(num) {
    if (num === null || num === undefined) num = 0;
    const isNeg = num < 0;
    const absVal = Math.abs(num);
    const formatted = absVal.toLocaleString('en-US', {minimumFractionDigits: 2});
    return (isNeg ? '-$' : '$') + formatted;
}
function formatPct(num) {
    return (num || 0).toFixed(2) + '%';
}
function colorClass(num) {
    return num >= 0 ? 'text-green' : 'text-red';
}
function sign(num) {
    return num > 0 ? '+' : '';
}

async function loadMaster() {
    try {
        const res = await fetch('/api/master/summary');
        if(!res.ok) return;
        const data = await res.json();
        
        // Header
        document.getElementById('global-nav').innerText = formatUSD(data.consolidated_nav_usd);
        const roiEl = document.getElementById('global-roi');
        roiEl.innerText = sign(data.total_roi_pct) + formatPct(data.total_roi_pct);
        roiEl.className = colorClass(data.total_roi_pct);
        
        // Home tab
        document.getElementById('home-master-nav').innerText = formatUSD(data.consolidated_nav_usd);
        document.getElementById('home-master-initial').innerText = formatUSD(data.initial_master_capital_usd);
        const homePnl = document.getElementById('home-master-pnl');
        homePnl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd) + '  (' + sign(data.total_roi_pct) + formatPct(data.total_roi_pct) + ')';
        homePnl.className = colorClass(data.total_pnl_usd);

        document.getElementById('home-sgov-val').innerText = formatUSD(data.treasury_sgov?.allocated_usd || 60000);
        document.getElementById('home-margin-val').innerText = (data.margin?.margin_utilization_pct || 0) + '%';
        document.getElementById('home-margin-status').innerText = data.margin_status || 'OPTIMAL';
        
        // Performance Analytics
        if (data.performance_analytics) {
            document.getElementById('home-perf-days').innerText = data.performance_analytics.days_active + ' DÍAS';
            document.getElementById('home-perf-inception').innerText = 'Desde ' + data.performance_analytics.inception_date;
            
            const cagrEl = document.getElementById('home-perf-cagr');
            cagrEl.innerText = formatPct(data.performance_analytics.annualized_roi_pct);
            cagrEl.className = 'val ' + colorClass(data.performance_analytics.annualized_roi_pct);

            const pfEl = document.getElementById('home-perf-pf');
            pfEl.innerText = (data.performance_analytics.profit_factor || 0).toFixed(2);
            pfEl.className = 'val ' + (data.performance_analytics.profit_factor >= 1.5 ? 'text-green' : (data.performance_analytics.profit_factor >= 1.0 ? 'text-green' : 'text-red'));

            const mddEl = document.getElementById('home-perf-mdd');
            mddEl.innerText = formatPct(data.performance_analytics.max_drawdown_pct);
            mddEl.className = 'val ' + colorClass(data.performance_analytics.max_drawdown_pct);

            const monthlyEl = document.getElementById('home-perf-monthly');
            monthlyEl.innerText = sign(data.performance_analytics.projected_monthly_usd) + formatUSD(data.performance_analytics.projected_monthly_usd);
            monthlyEl.className = 'val ' + colorClass(data.performance_analytics.projected_monthly_usd);

            const thetaEl = document.getElementById('home-perf-theta');
            thetaEl.innerText = sign(data.performance_analytics.global_theta_usd_per_day) + formatUSD(data.performance_analytics.global_theta_usd_per_day) + '/d';
            thetaEl.className = 'val ' + colorClass(data.performance_analytics.global_theta_usd_per_day);
        }

        // Collateral Portfolio
        if (data.collateral_portfolio && data.collateral_portfolio.breakdown) {
            const breakdown = data.collateral_portfolio.breakdown;
            const sgovPct = breakdown.SGOV?.target_pct || 0;
            const gldPct = breakdown.GLD?.target_pct || 0;
            const tltPct = breakdown.TLT?.target_pct || 0;
            const marginPct = Math.max(0, 100 - (data.collateral_portfolio.total_collateral_pct || 0));

            const sgovBar = document.getElementById('bar-sgov');
            const gldBar = document.getElementById('bar-gld');
            const tltBar = document.getElementById('bar-tlt');
            const marginBar = document.getElementById('bar-margin');

            if(sgovBar) {
                sgovBar.style.width = sgovPct + '%';
                sgovBar.innerText = 'SGOV ' + sgovPct + '%';
                sgovBar.style.display = sgovPct > 0 ? 'flex' : 'none';
            }
            if(gldBar) {
                gldBar.style.width = gldPct + '%';
                gldBar.innerText = 'GLD ' + gldPct + '%';
                gldBar.style.display = gldPct > 0 ? 'flex' : 'none';
            }
            if(tltBar) {
                tltBar.style.width = tltPct + '%';
                tltBar.innerText = 'TLT ' + tltPct + '%';
                tltBar.style.display = tltPct > 0 ? 'flex' : 'none';
            }
            if(marginBar) {
                marginBar.style.width = marginPct + '%';
                marginBar.innerText = 'MARGIN ' + marginPct + '%';
                marginBar.style.display = marginPct > 0 ? 'flex' : 'none';
            }
        }

        if (data.strategies_ledger) {
            data.strategies_ledger.forEach(l => {
                const liveNav = (l.capital_allocated_usd || 0) + (l.net_pnl_usd || 0);
                const pnlTxt = sign(l.net_pnl_usd) + formatUSD(l.net_pnl_usd);
                const pnlClass = 'sub ' + colorClass(l.net_pnl_usd);
                
                if(l.id === 'wheel') {
                    document.getElementById('home-c1-nav').innerText = formatUSD(liveNav);
                    const el = document.getElementById('home-c1-pnl');
                    el.innerText = pnlTxt; el.className = pnlClass;
                }
                if(l.id === 'spreads') {
                    document.getElementById('home-c2-nav').innerText = formatUSD(liveNav);
                    const el = document.getElementById('home-c2-pnl');
                    el.innerText = pnlTxt; el.className = pnlClass;
                }
                if(l.id === 'alpha') {
                    document.getElementById('home-c3-nav').innerText = formatUSD(liveNav);
                    const el = document.getElementById('home-c3-pnl');
                    el.innerText = pnlTxt; el.className = pnlClass;
                }
                if(l.id === 'rsi_opportunistic') {
                    document.getElementById('home-c4-nav').innerText = formatUSD(liveNav);
                    const el = document.getElementById('home-c4-pnl');
                    el.innerText = pnlTxt; el.className = pnlClass;
                }
                if(l.id === 'daytrade') {
                    document.getElementById('home-c5-nav').innerText = formatUSD(liveNav);
                    const el = document.getElementById('home-c5-pnl');
                    el.innerText = pnlTxt; el.className = pnlClass;
                }
            });
        }
        
        // Render Health Pings
        if (data.health_pings) {
            const now = Date.now() / 1000;
            const updateHealth = (id, lastPing) => {
                const el = document.getElementById('health-' + id);
                if (!el) return;
                const diff = now - lastPing;
                if (lastPing === 0) {
                    el.innerHTML = '<span class="dot" style="background:gray"></span> WAITING';
                } else if (diff < 180) { // < 3 mins
                    el.innerHTML = '<span class="dot green"></span> ONLINE';
                    el.style.color = 'var(--accent-green)';
                } else if (diff < 600) { // < 10 mins
                    el.innerHTML = '<span class="dot" style="background:#F59E0B"></span> DELAYED';
                    el.style.color = '#F59E0B';
                } else {
                    el.innerHTML = '<span class="dot" style="background:var(--primary-red)"></span> OFFLINE';
                    el.style.color = 'var(--primary-red)';
                }
            };
            
            updateHealth('wheel', data.health_pings.wheel || 0);
            updateHealth('spreads', data.health_pings.spreads || 0);
            updateHealth('alpha', data.health_pings.alpha || 0);
            updateHealth('rsi', data.health_pings.rsi || 0);
            updateHealth('daytrade', data.health_pings.daytrade || 0);
        }
    } catch(e) { console.error('Error loadMaster', e); }
}

async function loadWheel() {
    try {
        const res = await fetch('/api/wheel/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('wheel-cap').innerText = formatUSD(data.initial_capital_usd);
        document.getElementById('wheel-shares').innerText = (data.etf_shares||0).toFixed(4);
        document.getElementById('wheel-prems').innerText = formatUSD(data.total_reinvested_usd);
        document.getElementById('wheel-cagr').innerText = sign(data.cagr_pct) + formatPct(data.cagr_pct);

        // 1. Posiciones Abiertas
        const tbodyPos = document.getElementById('wheel-positions');
        tbodyPos.innerHTML = '';
        if(data.wheel_positions && data.wheel_positions.length > 0) {
            data.wheel_positions.forEach(p => {
                tbodyPos.innerHTML += `<tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>${p.strategy_type || 'Cash-Secured Put'}</td>
                    <td>Strike $${p.strike}</td>
                    <td class="text-green">${formatUSD(p.premium_collected_usd || 0)}</td>
                    <td><span class="text-green">🟢 ${p.status || 'ACTIVA'}</span></td>
                </tr>`;
            });
        } else {
            tbodyPos.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">Sin posiciones abiertas. Esperando inicio de ciclo mensual.</td></tr>';
        }

        // 2. Historial de Ciclos
        const tbodyHist = document.getElementById('wheel-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.history && data.history.length > 0) {
                data.history.slice().reverse().forEach(h => {
                    tbodyHist.innerHTML += `<tr>
                        <td>${h.date || '-'}</td>
                        <td><strong>${h.event || 'CICLO MENSUAL'}</strong></td>
                        <td>${h.details || '-'}</td>
                        <td class="text-green">+${formatUSD(h.reinvested_usd || 0)}</td>
                        <td class="text-green">+${formatUSD(h.cumulative_pnl || 0)}</td>
                    </tr>`;
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">Historial listo para registrar el primer ciclo mensual.</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadWheel', e); }
}

async function loadSpreads() {
    try {
        const res = await fetch('/api/spreads/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('spreads-cap').innerText = formatUSD(20000 + (data.total_pnl_usd || 0));
        document.getElementById('spreads-wr').innerText = formatPct(data.stats?.win_rate || 0);
        
        let totalTheta = 0;
        // 1. Spreads Abiertos
        const tbodyPos = document.getElementById('spreads-positions');
        tbodyPos.innerHTML = '';
        if(data.open_spreads && data.open_spreads.length > 0) {
            data.open_spreads.forEach(s => {
                totalTheta += s.theta_daily_decay_usd || 0;
                const pnl = s.pnl_usd || 0;
                tbodyPos.innerHTML += `<tr>
                    <td><strong>${s.symbol}</strong></td>
                    <td>${s.type || 'BULL_PUT_SPREAD'}</td>
                    <td>Short Put $${s.short_strike} / Long Put $${s.long_strike}</td>
                    <td class="text-green">+${formatUSD(s.total_credit_collected_usd)}</td>
                    <td>${s.dte} días</td>
                    <td class="${colorClass(pnl)}">${sign(pnl)}${formatUSD(pnl)}</td>
                    <td><span class="text-green">🟢 ${s.status || 'ABIERTO'}</span></td>
                </tr>`;
            });
        } else {
            tbodyPos.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No hay credit spreads abiertos actualmente</td></tr>';
        }
        document.getElementById('spreads-theta').innerText = '+' + formatUSD(totalTheta) + '/d';
        const pnlEl = document.getElementById('spreads-pnl');
        pnlEl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.total_pnl_usd);

        // 2. Historial de Spreads Cerrados
        const tbodyHist = document.getElementById('spreads-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_spreads && data.closed_spreads.length > 0) {
                data.closed_spreads.slice().reverse().forEach(s => {
                    const net = s.final_pnl_usd || 0;
                    tbodyHist.innerHTML += `<tr>
                        <td>${s.entry_date || '-'} → ${s.exit_date || '-'}</td>
                        <td><strong>${s.symbol}</strong></td>
                        <td>${s.type || 'BULL_PUT_SPREAD'}</td>
                        <td>$${s.short_strike}/$${s.long_strike}</td>
                        <td>${s.exit_reason || 'TAKE_PROFIT_70%'}</td>
                        <td class="${colorClass(net)}"><strong>${sign(net)}${formatUSD(net)}</strong></td>
                    </tr>`;
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">Sin spreads cerrados aún (2 spreads en curso).</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadSpreads', e); }
}

async function loadAlpha() {
    try {
        const res = await fetch('/api/alpha/status');
        if(!res.ok) return;
        const data = await res.json();
        const allocCap = data.allocated_capital || 20000;
        const unrealizedPnl = data.total_unrealized_pnl_usd || 0;
        document.getElementById('alpha-cap').innerText = formatUSD(allocCap + unrealizedPnl);
        document.getElementById('alpha-leaps').innerText = formatUSD(unrealizedPnl);
        
        let putRisk = 0;
        if (data.open_positions && data.open_positions.length > 0) {
            putRisk = data.open_positions.reduce((acc, p) => acc + (p.short_put_current_buyback_cost || 0), 0);
        }
        document.getElementById('alpha-risk').innerText = formatUSD(putRisk);
        
        const pnlEl = document.getElementById('alpha-pnl');
        pnlEl.innerText = sign(unrealizedPnl) + formatUSD(unrealizedPnl);
        pnlEl.className = 'val ' + colorClass(unrealizedPnl);

        // 1. Posiciones Sintéticas Abiertas y Long Calls
        const tbodyPos = document.getElementById('alpha-positions');
        tbodyPos.innerHTML = '';
        
        let hasOpen = false;
        if(data.open_positions && data.open_positions.length > 0) {
            hasOpen = true;
            data.open_positions.forEach(p => {
                const statusBadge = p.decoupled ? '<span class="text-green">🟢 RISK-FREE CALL</span>' : '<span class="text-green">🟢 ACTIVO (120 DTE)</span>';
                const pnl = p.unrealized_pnl_usd || 0;
                tbodyPos.innerHTML += `<tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>Sintético (2x Put + 2x Call)</td>
                    <td>Put K$${p.short_put_strike} / Call K$${p.long_call_strike}</td>
                    <td class="${colorClass(pnl)}"><strong>${sign(pnl)}${formatUSD(pnl)}</strong></td>
                    <td class="text-red">$${p.short_put_current_buyback_cost || 0} USD</td>
                    <td>${statusBadge}</td>
                </tr>`;
            });
        }
        
        if(data.decoupled_calls && data.decoupled_calls.length > 0) {
            hasOpen = true;
            data.decoupled_calls.forEach(p => {
                tbodyPos.innerHTML += `<tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>Risk-Free Long Call</td>
                    <td>Call K$${p.long_call_strike}</td>
                    <td class="text-green"><strong>+${formatUSD(p.unrealized_pnl_usd || 0)}</strong></td>
                    <td class="text-green">$0.00 (Desacoplado)</td>
                    <td><span class="text-green">⭐ 100% RISK-FREE</span></td>
                </tr>`;
            });
        }
        
        if (!hasOpen) {
            tbodyPos.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">No hay posiciones sintéticas abiertas</td></tr>';
        }

        // 2. Historial de Alpha
        const tbodyHist = document.getElementById('alpha-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_positions && data.closed_positions.length > 0) {
                data.closed_positions.slice().reverse().forEach(p => {
                    const net = p.final_pnl_usd || 0;
                    tbodyHist.innerHTML += `<tr>
                        <td>${p.entry_date || '-'} → ${p.exit_date || '-'}</td>
                        <td><strong>${p.symbol}</strong></td>
                        <td>${p.strategy || 'Sintético LEAPS'}</td>
                        <td>${formatUSD(p.decouple_cost_paid_usd || 0)}</td>
                        <td class="${colorClass(net)}"><strong>${sign(net)}${formatUSD(net)}</strong></td>
                        <td><span class="text-green">CERRADO</span></td>
                    </tr>`;
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">Sin sintéticos cerrados aún (1 sintético QQQ en monitoreo).</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadAlpha', e); }
}

async function loadRsi() {
    try {
        const res = await fetch('/api/rsi-opportunistic/status');
        if(!res.ok) return;
        const data = await res.json();
        const allocCap = data.allocated_capital || 15000;
        const totalPnl = data.total_pnl_usd || 0;
        document.getElementById('rsi-cap').innerText = formatUSD(allocCap + totalPnl);
        
        const spyRsi = data.last_rsi_scanned?.SPY ?? 30.0;
        document.getElementById('rsi-val').innerText = Number(spyRsi).toFixed(1);
        
        const totalOpps = (data.open_trades?.length || 0) + (data.closed_trades?.length || 0);
        document.getElementById('rsi-opps').innerText = totalOpps;
        
        const pnlEl = document.getElementById('rsi-pnl');
        pnlEl.innerText = sign(totalPnl) + formatUSD(totalPnl);
        pnlEl.className = 'val ' + colorClass(totalPnl);

        // 1. Operaciones 1DTE Abiertas
        const tbodyPos = document.getElementById('rsi-positions');
        tbodyPos.innerHTML = '';
        if(data.open_trades && data.open_trades.length > 0) {
            data.open_trades.forEach(p => {
                tbodyPos.innerHTML += `<tr>
                    <td><strong>${p.symbol}</strong></td>
                    <td>Short Put 1DTE (${p.contracts}x)</td>
                    <td><span style="color:var(--primary-red);font-weight:bold;">${p.entry_rsi} (Pánico)</span></td>
                    <td>Strike $${p.put_strike}</td>
                    <td class="text-green">+${formatUSD(p.premium_collected_usd)}</td>
                    <td>${p.dte} día</td>
                    <td><span class="text-green">🟢 ABIERTA</span></td>
                </tr>`;
            });
        } else {
            tbodyPos.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">Sin operaciones abiertas. Escaneando mercado para caídas con RSI &lt; 30.</td></tr>';
        }

        // 2. Historial de Operaciones 1DTE Cerradas
        const tbodyHist = document.getElementById('rsi-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_trades && data.closed_trades.length > 0) {
                data.closed_trades.slice().reverse().forEach(p => {
                    const net = p.pnl_usd || 0;
                    tbodyHist.innerHTML += `<tr>
                        <td>${p.entry_date || '-'} → ${p.exit_date || '-'}</td>
                        <td><strong>${p.symbol}</strong></td>
                        <td>Entrada: ${p.entry_rsi} → Salida: ${p.exit_rsi || '-'}</td>
                        <td>Strike $${p.put_strike}</td>
                        <td class="text-green">+${formatUSD(p.premium_collected_usd || 0)}</td>
                        <td class="${colorClass(net)}"><strong>+${formatUSD(net)}</strong></td>
                        <td><span class="text-green">✅ CERRADA (TP 90%)</span></td>
                    </tr>`;
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No hay operaciones 1DTE cerradas registradas</td></tr>';
            }
        }
    } catch(e) { console.error('Error loadRsi', e); }
}

async function loadDaytrade() {
    try {
        const res = await fetch('/api/daytrade/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('dt-cap').innerText = formatUSD(10000 + (data.total_pnl_usd || 0));
        
        let wr = data.stats?.win_rate || 0;
        document.getElementById('dt-wr').innerText = formatPct(wr);
        
        document.getElementById('dt-mode').innerText = data.config?.execution_mode || 'PAPER';
        const pnlEl = document.getElementById('dt-pnl');
        pnlEl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.total_pnl_usd);

        // 1. Posiciones Intradía Abiertas
        const tbodyOpen = document.getElementById('dt-open-positions');
        tbodyOpen.innerHTML = '';
        if(data.open_positions && data.open_positions.length > 0) {
            data.open_positions.forEach(p => {
                const pnl = p.pnl_usd || 0;
                tbodyOpen.innerHTML += `<tr>
                    <td><strong>${p.option_ticker}</strong></td>
                    <td>${p.contracts || 1} contratos</td>
                    <td>${formatUSD(p.total_cost_usd)}</td>
                    <td>$${p.entry_premium || 0}</td>
                    <td class="${colorClass(pnl)}"><strong>${sign(pnl)}${formatUSD(pnl)}</strong></td>
                    <td><span class="text-green">🟢 EN VIVO</span></td>
                </tr>`;
            });
        } else {
            tbodyOpen.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">Sin posiciones abiertas en este momento. Escaneando señales intradiarias cada 60s.</td></tr>';
        }

        // 2. Historial de Operaciones Intradía Cerradas
        const tbodyHist = document.getElementById('dt-history');
        tbodyHist.innerHTML = '';
        if(data.closed_trades && data.closed_trades.length > 0) {
            data.closed_trades.slice().reverse().forEach(p => {
                const net = p.final_pnl_usd || 0;
                const roi = p.roi_pct != null ? formatPct(p.roi_pct) : (p.total_cost_usd > 0 ? formatPct((net / p.total_cost_usd) * 100) : '0.0%');
                const dur = p.duration_minutes ? `${p.duration_minutes}m` : '-';
                tbodyHist.innerHTML += `<tr>
                    <td>${p.timestamp || p.entry_time || '-'}</td>
                    <td><strong>${p.option_ticker}</strong></td>
                    <td>${formatUSD(p.entry_premium || 0)}</td>
                    <td>${formatUSD(p.exit_premium || 0)}</td>
                    <td>${dur}</td>
                    <td class="${colorClass(net)}"><strong>${sign(net)}${formatUSD(net)}</strong></td>
                    <td class="${colorClass(net)}">${roi}</td>
                    <td><span class="text-green">✅ GANADORA</span></td>
                </tr>`;
            });
        } else {
            tbodyHist.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">No hay historial de operaciones cerradas</td></tr>';
        }
    } catch(e) { console.error('Error loadDaytrade', e); }
}

// API Actions
async function runWheelCycle() {
    fetch('/api/wheel/run-cycle', { method:'POST' }).then(() => refreshAllData());
}
async function runSpreadsScan() {
    fetch('/api/spreads/scan', { method:'POST' }).then(() => refreshAllData());
}
async function runAlphaDecouple() {
    fetch('/api/alpha/decouple', { method:'POST' }).then(() => refreshAllData());
}
async function runDaytradeScan() {
    fetch('/api/daytrade/scan', { method:'POST' }).then(() => refreshAllData());
}
async function togglePaperLive() {
    const mode = document.getElementById('dt-mode').innerText === 'PAPER' ? 'LIVE_BROKER' : 'PAPER_TRADING';
    fetch('/api/daytrade/mode', {
        method:'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: mode, broker: 'INTERACTIVE_BROKERS'})
    }).then(() => refreshAllData());
}
