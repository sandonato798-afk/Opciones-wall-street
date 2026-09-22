// js/tabs/tab_master.js - Lógica de la solapa PORTFOLIO OVERVIEW, métricas globales y salud

async function loadMaster() {
    try {
        const res = await fetch('/api/master/summary');
        if(!res.ok) return;
        const data = await res.json();
        
        // Header
        setTxt('global-nav', formatUSD(data.consolidated_nav_usd));
        setTxt('global-roi', sign(data.total_roi_pct) + formatPct(data.total_roi_pct));
        setClass('global-roi', colorClass(data.total_roi_pct));
        
        // Home tab
        setTxt('home-master-nav', formatUSD(data.consolidated_nav_usd));
        setTxt('home-master-initial', formatUSD(data.initial_master_capital_usd));
        setTxt('home-master-pnl', sign(data.total_pnl_usd) + formatUSD(data.total_pnl_usd) + '  (' + sign(data.total_roi_pct) + formatPct(data.total_roi_pct) + ')');
        setClass('home-master-pnl', colorClass(data.total_pnl_usd));

        const freeMargin = data.margin?.free_margin_usd !== undefined ? formatUSD(data.margin.free_margin_usd) : '$85,000.00';
        const utilPct = data.margin?.margin_utilization_pct || 0;
        setTxt('home-margin-val', utilPct + '%');
        setTxt('home-margin-status', `${freeMargin} LIBRE (POOL 100%)`);
        
        if (data.reinvestment_matrix_50_30_20) {
            const pending = data.reinvestment_matrix_50_30_20.pending_usd || 0;
            setTxt('home-reinvest-val', pending > 0 ? `${formatUSD(pending)} Pend.` : '100% AL DÍA');
            setTxt('home-reinvest-sub', '40% Tesoro · 20% Corp · 20% SPY · 15% QQQ · 5% GLD');
        }
        
        // Performance Analytics
        if (data.performance_analytics) {
            setTxt('home-perf-days', (data.performance_analytics.days_active || 0) + ' DÍAS');
            setTxt('home-perf-inception', 'Desde ' + (data.performance_analytics.inception_date || '-'));
            
            setTxt('home-perf-cagr', formatPct(data.performance_analytics.annualized_roi_pct));
            setClass('home-perf-cagr', 'val ' + colorClass(data.performance_analytics.annualized_roi_pct));

            const pfVal = (data.performance_analytics.profit_factor === 'N/A' || data.performance_analytics.profit_factor === undefined) ? 'N/A' : Number(data.performance_analytics.profit_factor).toFixed(2);
            setTxt('home-perf-pf', pfVal);
            setClass('home-perf-pf', 'val text-green');

            setTxt('home-perf-mdd', formatPct(data.performance_analytics.max_drawdown_pct));
            setClass('home-perf-mdd', 'val ' + colorClass(data.performance_analytics.max_drawdown_pct));

            setTxt('home-perf-monthly', sign(data.performance_analytics.projected_monthly_usd) + formatUSD(data.performance_analytics.projected_monthly_usd));
            setClass('home-perf-monthly', 'val ' + colorClass(data.performance_analytics.projected_monthly_usd));

            setTxt('home-perf-theta', sign(data.performance_analytics.global_theta_usd_per_day) + formatUSD(data.performance_analytics.global_theta_usd_per_day) + '/d');
            setClass('home-perf-theta', 'val ' + colorClass(data.performance_analytics.global_theta_usd_per_day));
        }

        // Collateral Portfolio Bars & Stats
        if (data.collateral_portfolio && data.collateral_portfolio.breakdown) {
            const breakdown = data.collateral_portfolio.breakdown;
            const treasuryPct = breakdown.TREASURY?.target_pct || 40;
            const corpPct = breakdown.CORP_AAA?.target_pct || 20;
            const spyPct = breakdown.SPY?.target_pct || 20;
            const qqqPct = breakdown.QQQ?.target_pct || 15;
            const gldPct = breakdown.GLD?.target_pct || 5;

            const barTreasury = document.getElementById('bar-treasury');
            const barCorp = document.getElementById('bar-corp');
            const barSpy = document.getElementById('bar-spy');
            const barQqq = document.getElementById('bar-qqq');
            const barGld = document.getElementById('bar-gld');

            if(barTreasury) { barTreasury.style.width = treasuryPct + '%'; barTreasury.innerText = 'TESORO ' + treasuryPct + '%'; }
            if(barCorp) { barCorp.style.width = corpPct + '%'; barCorp.innerText = 'CORP AAA ' + corpPct + '%'; }
            if(barSpy) { barSpy.style.width = spyPct + '%'; barSpy.innerText = 'SPY ' + spyPct + '%'; }
            if(barQqq) { barQqq.style.width = qqqPct + '%'; barQqq.innerText = 'QQQ ' + qqqPct + '%'; }
            if(barGld) { barGld.style.width = gldPct + '%'; barGld.innerText = 'GLD ' + gldPct + '%'; }

            setTxt('home-yield-val', '+' + formatUSD(data.collateral_portfolio.total_annual_yield_usd || 4350) + '/año');
        }

        // Collateral Detailed Table
        const tbodyCol = document.getElementById('home-collateral-table');
        if (tbodyCol && data.collateral_portfolio && data.collateral_portfolio.breakdown) {
            tbodyCol.innerHTML = '';
            const breakdown = data.collateral_portfolio.breakdown;
            Object.values(breakdown).forEach(item => {
                const yieldTxt = item.annual_yield_usd > 0 ? `+${formatUSD(item.annual_yield_usd)}/año (${(item.annual_yield_usd / (item.actual_usd || 1) * 100).toFixed(1)}%)` : 'Apreciación + Opciones';
                tbodyCol.innerHTML += `<tr>
                    <td><strong>${item.symbol}</strong> <span style="font-size:11px;opacity:0.75;">(${item.tickers ? item.tickers.join(', ') : item.symbol})</span></td>
                    <td>${item.description || '-'}</td>
                    <td><span style="color:var(--accent-blue);font-weight:bold;">${item.target_pct}%</span></td>
                    <td>${formatUSD(item.actual_usd)}</td>
                    <td>${item.margin_req_pct}%</td>
                    <td class="text-green"><strong>${formatUSD(item.collateral_unlocked_usd)}</strong></td>
                    <td class="text-green">${yieldTxt}</td>
                </tr>`;
            });
            tbodyCol.innerHTML += `<tr style="background:rgba(255,255,255,0.05);font-weight:bold;">
                <td>TOTAL COLATERAL</td>
                <td>100% NAV Colateralizado</td>
                <td><span style="color:var(--accent-blue);">100%</span></td>
                <td>${formatUSD(data.collateral_portfolio.total_collateral_usd)}</td>
                <td>~6.5% Prom.</td>
                <td class="text-green">${formatUSD(data.collateral_portfolio.total_unlocked_buying_power_usd)}</td>
                <td class="text-green">+${formatUSD(data.collateral_portfolio.total_annual_yield_usd)}/año</td>
            </tr>`;
        }

        if (data.strategies_ledger) {
            data.strategies_ledger.forEach(l => {
                const liveNav = (l.capital_allocated_usd || 0) + (l.net_pnl_usd || 0);
                const pnlTxt = sign(l.net_pnl_usd) + formatUSD(l.net_pnl_usd);
                const pnlClass = 'sub ' + colorClass(l.net_pnl_usd);
                
                if(l.id === 'wheel') {
                    setTxt('home-c1-nav', formatUSD(liveNav));
                    setTxt('home-c1-pnl', pnlTxt);
                    setClass('home-c1-pnl', pnlClass);
                }
                if(l.id === 'alpha') {
                    setTxt('home-c3-nav', formatUSD(liveNav));
                    setTxt('home-c3-pnl', pnlTxt);
                    setClass('home-c3-pnl', pnlClass);
                }
                if(l.id === 'rsi_opportunistic') {
                    setTxt('home-c4-nav', formatUSD(liveNav));
                    setTxt('home-c4-pnl', pnlTxt);
                    setClass('home-c4-pnl', pnlClass);
                }
                if(l.id === 'daytrade') {
                    setTxt('home-c5-nav', formatUSD(liveNav));
                    setTxt('home-c5-pnl', pnlTxt);
                    setClass('home-c5-pnl', pnlClass);
                }
                if(l.id === 'bullmarket') {
                    setTxt('home-c6-nav', formatUSD(liveNav));
                    setTxt('home-c6-pnl', pnlTxt);
                    setClass('home-c6-pnl', pnlClass);
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
            updateHealth('alpha', data.health_pings.alpha || 0);
            updateHealth('rsi', data.health_pings.rsi || 0);
            updateHealth('daytrade', data.health_pings.daytrade || 0);
            updateHealth('bullmarket', data.health_pings.bullmarket || 0);
        }
    } catch(e) { console.error('Error loadMaster', e); }
}
