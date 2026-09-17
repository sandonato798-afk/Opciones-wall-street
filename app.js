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
    return '$' + (num || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
}
function formatPct(num) {
    return (num || 0).toFixed(2) + '%';
}
function colorClass(num) {
    return num >= 0 ? 'text-green' : 'text-red';
}
function sign(num) {
    return num >= 0 ? '+' : '';
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
                if(l.id === 'wheel') document.getElementById('home-c1-nav').innerText = formatUSD(l.capital_allocated_usd);
                if(l.id === 'spreads') document.getElementById('home-c2-nav').innerText = formatUSD(l.capital_allocated_usd);
                if(l.id === 'alpha') document.getElementById('home-c3-nav').innerText = formatUSD(l.capital_allocated_usd);
                if(l.id === 'rsi') document.getElementById('home-c4-nav').innerText = formatUSD(l.capital_allocated_usd);
                if(l.id === 'daytrade') document.getElementById('home-c5-nav').innerText = formatUSD(l.capital_allocated_usd);
            });
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

        const tbody = document.getElementById('wheel-positions');
        tbody.innerHTML = '';
        if(data.wheel_positions) {
            data.wheel_positions.forEach(p => {
                tbody.innerHTML += `<tr>
                    <td>${p.symbol}</td>
                    <td>${p.strategy_type}</td>
                    <td>${formatUSD(p.strike)}</td>
                    <td class="text-green">${formatUSD(p.premium_collected_usd)}</td>
                    <td>${p.status}</td>
                </tr>`;
            });
        }
    } catch(e) { console.error('Error loadWheel', e); }
}

async function loadSpreads() {
    try {
        const res = await fetch('/api/spreads/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('spreads-cap').innerText = formatUSD(data.capital);
        document.getElementById('spreads-wr').innerText = formatPct(data.stats?.win_rate || 0);
        
        let totalTheta = 0;
        const tbody = document.getElementById('spreads-positions');
        tbody.innerHTML = '';
        if(data.open_spreads) {
            data.open_spreads.forEach(s => {
                totalTheta += s.theta_daily_decay_usd || 0;
                tbody.innerHTML += `<tr>
                    <td>${s.symbol}</td>
                    <td>${s.type}</td>
                    <td>${s.short_strike}/${s.long_strike}</td>
                    <td class="text-green">${formatUSD(s.total_credit_collected_usd)}</td>
                    <td>${s.dte}</td>
                    <td>ACTIVE</td>
                </tr>`;
            });
        }
        document.getElementById('spreads-theta').innerText = '+' + formatUSD(totalTheta) + '/d';
        const pnlEl = document.getElementById('spreads-pnl');
        pnlEl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.total_pnl_usd);
    } catch(e) { console.error('Error loadSpreads', e); }
}

async function loadAlpha() {
    try {
        const res = await fetch('/api/alpha/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('alpha-cap').innerText = formatUSD(data.capital);
        document.getElementById('alpha-leaps').innerText = formatUSD(data.leaps_value_usd);
        document.getElementById('alpha-risk').innerText = formatUSD(data.short_put_risk_usd);
        const pnlEl = document.getElementById('alpha-pnl');
        pnlEl.innerText = sign(data.net_pnl_usd) + formatUSD(data.net_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.net_pnl_usd);

        const tbody = document.getElementById('alpha-positions');
        tbody.innerHTML = '';
        if(data.positions) {
            data.positions.forEach(p => {
                tbody.innerHTML += `<tr>
                    <td>${p.symbol}</td>
                    <td>${p.type}</td>
                    <td>${formatUSD(p.strike)}</td>
                    <td>${formatUSD(p.current_value)}</td>
                    <td>${p.status}</td>
                </tr>`;
            });
        }
    } catch(e) { console.error('Error loadAlpha', e); }
}

async function loadRsi() {
    try {
        const res = await fetch('/api/rsi-opportunistic/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('rsi-cap').innerText = formatUSD(data.capital);
        document.getElementById('rsi-val').innerText = (data.current_rsi || 0).toFixed(2);
        document.getElementById('rsi-opps').innerText = data.opportunities_found || 0;
        const pnlEl = document.getElementById('rsi-pnl');
        pnlEl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.total_pnl_usd);

        const tbody = document.getElementById('rsi-positions');
        tbody.innerHTML = '';
        if(data.active_positions) {
            data.active_positions.forEach(p => {
                tbody.innerHTML += `<tr>
                    <td>${p.symbol}</td>
                    <td>${p.signal}</td>
                    <td>${p.entry_rsi}</td>
                    <td class="text-green">${formatUSD(p.premium)}</td>
                    <td>${p.status}</td>
                </tr>`;
            });
        }
    } catch(e) { console.error('Error loadRsi', e); }
}

async function loadDaytrade() {
    try {
        const res = await fetch('/api/daytrade/status');
        if(!res.ok) return;
        const data = await res.json();
        document.getElementById('dt-cap').innerText = formatUSD(data.capital);
        document.getElementById('dt-wr').innerText = formatPct(data.stats?.win_rate || 0);
        document.getElementById('dt-mode').innerText = data.config?.execution_mode || 'PAPER';
        const pnlEl = document.getElementById('dt-pnl');
        pnlEl.innerText = sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd);
        pnlEl.className = 'val ' + colorClass(data.total_pnl_usd);

        const tbody = document.getElementById('dt-positions');
        tbody.innerHTML = '';
        if(data.open_positions) {
            data.open_positions.forEach(p => {
                tbody.innerHTML += `<tr>
                    <td>${p.option_ticker}</td>
                    <td>${formatUSD(p.total_cost_usd)}</td>
                    <td>-</td>
                    <td class="${colorClass(p.pnl_usd)}">${sign(p.pnl_usd)}${formatUSD(Math.abs(p.pnl_usd))}</td>
                    <td>OPEN</td>
                </tr>`;
            });
        }
        if(data.closed_trades) {
            data.closed_trades.forEach(p => {
                const net = p.final_pnl_usd || 0;
                tbody.innerHTML += `<tr>
                    <td>${p.option_ticker}</td>
                    <td>${formatUSD(p.total_cost_usd)}</td>
                    <td>${formatUSD(p.exit_premium * 100 * (p.contracts||1))}</td>
                    <td class="${colorClass(net)}">${sign(net)}${formatUSD(Math.abs(net))}</td>
                    <td>CLOSED</td>
                </tr>`;
            });
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
