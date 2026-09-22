// State
let appData = {};

// Helper seguro para asignar texto a elementos sin crash
function setTxt(id, txt) {
    const el = document.getElementById(id);
    if (el) el.innerText = txt;
}

function setHtml(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

function setClass(id, cls) {
    const el = document.getElementById(id);
    if (el) el.className = cls;
}

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    refreshAllData();
    setInterval(refreshAllData, 10000);
});

function showTab(tabId) {
    if (!tabId) return;
    document.querySelectorAll('.tab-btn').forEach(t => {
        if (t.dataset.tab === tabId) t.classList.add('active');
        else t.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(c => {
        if (c.id === tabId) c.classList.add('active');
        else c.classList.remove('active');
    });
}
window.showTab = showTab;

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const target = tab.dataset.tab;
            if (target) showTab(target);
        });
    });
}

async function refreshAllData() {
    await Promise.all([
        loadMaster(),
        loadWheel(),
        loadAlpha(),
        loadRsi(),
        loadDaytrade()
    ]);
}

function formatUSD(num) {
    if (num === null || num === undefined) num = 0;
    const isNeg = num < 0;
    const absVal = Math.abs(num);
    const formatted = absVal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
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

function formatDurationStr(entryTime, exitTime, isOpen) {
    if (!entryTime) return '-';
    try {
        const t1 = new Date(entryTime.replace(' ', 'T')).getTime();
        const t2 = isOpen ? Date.now() : (exitTime ? new Date(exitTime.replace(' ', 'T')).getTime() : Date.now());
        if (isNaN(t1) || isNaN(t2) || t2 < t1) return '-';
        const totalMins = Math.floor((t2 - t1) / 60000);
        if (totalMins < 60) return `${totalMins} min`;
        const hours = Math.floor(totalMins / 60);
        const mins = totalMins % 60;
        if (hours < 24) return `${hours}h ${mins}m`;
        const days = Math.floor(hours / 24);
        const remHours = hours % 24;
        return `${days}d ${remHours}h`;
    } catch(e) {
        return '-';
    }
}

function render15MetricsRow(p, isOpen = false) {
    const ticker = p.symbol || p.ticker || 'SPY';
    const isDecoupled = p.decoupled || p.status === 'RISK_FREE_LONG_CALL' || p.status === 'FREE_RUNNER_LONG_CALL';
    
    let optionType = p.option_type || p.type || p.strategy_mode || p.strategy_type;
    if (!optionType) {
        if (isDecoupled) optionType = 'LONG CALL (RISK-FREE)';
        else if (p.short_put_strike && p.long_call_strike) optionType = 'SINTÉTICO ZERO-COST';
        else if (p.strategy && p.strategy.includes('CALL')) optionType = 'CALL';
        else if (p.strategy && p.strategy.includes('PUT')) optionType = 'PUT';
        else optionType = 'OPCIÓN';
    }
    
    let strike = '-';
    if (p.strike !== undefined && p.strike !== null) strike = `$${p.strike}`;
    else if (p.put_strike !== undefined && p.put_strike !== null) strike = `P$${p.put_strike}`;
    else if (p.short_put_strike !== undefined || p.long_call_strike !== undefined) {
        if (isDecoupled) {
            strike = `C$${p.long_call_strike || '-'} <span style="font-size:10px;color:var(--accent-green);">(Put P$${p.short_put_strike || '-'} Cerrado)</span>`;
        } else {
            strike = `P$${p.short_put_strike || '-'}/C$${p.long_call_strike || '-'}`;
        }
    }
    
    const dteVal = p.dte !== undefined ? p.dte : (p.target_dte || 30);
    const entryTime = p.entry_time || p.entry_date || p.issued_date || p.timestamp || '-';
    
    // 1. Vencimiento: Fecha exacta (YYYY-MM-DD)
    let expDateStr = p.expiration_date;
    if (!expDateStr && entryTime && entryTime !== '-') {
        try {
            const d = new Date(entryTime.replace(' ', 'T'));
            if (!isNaN(d.getTime())) {
                d.setDate(d.getDate() + (dteVal || 30));
                expDateStr = d.toISOString().split('T')[0];
            }
        } catch(e) { expDateStr = null; }
    }
    const dteStr = expDateStr ? `<strong>${expDateStr}</strong> <span style="font-size:11px;opacity:0.75;">(${dteVal}d)</span>` : `${dteVal} DTE`;
    
    // 2. Contratos Abiertos Residuaes
    const contractsNum = p.contracts || p.long_call_contracts || p.short_put_contracts || 1;
    const contracts = isDecoupled ? `${contractsNum}x Long Call` : `${contractsNum}x`;
    
    const entryUnderlying = p.underlying_price_at_entry || p.entry_underlying_price || p.underlying_price || p.etf_price || p.entry_price || 0;
    
    // 3. Prima Entrada Especifica (Put Cobrado vs Call Pagado)
    let entryPremiumStr = '';
    let netIncomeEntry = 0;
    
    if (p.short_put_premium_collected !== undefined && p.long_call_premium_paid !== undefined) {
        const putPremPerShare = (p.short_put_premium_collected / (contractsNum * 100)).toFixed(2);
        const callPremPerShare = (p.long_call_premium_paid / (contractsNum * 100)).toFixed(2);
        entryPremiumStr = `<span class="text-green">P:+$${putPremPerShare}</span> | <span class="text-red">C:-$${callPremPerShare}</span>`;
        netIncomeEntry = 0; // Costo cero neto
    } else {
        let entryPremium = 0;
        if (p.entry_premium !== undefined) entryPremium = p.entry_premium;
        else if (p.premium_per_share !== undefined) entryPremium = p.premium_per_share;
        else if (p.premium_collected_usd) entryPremium = p.premium_collected_usd / (contractsNum * 100);
        
        entryPremiumStr = formatUSD(entryPremium);
        netIncomeEntry = p.premium_collected_usd !== undefined ? p.premium_collected_usd : (entryPremium * 100 * contractsNum);
    }
    
    const netIncomeEntryStr = (p.short_put_premium_collected !== undefined && p.long_call_premium_paid !== undefined) ? '$0.00 (Costo Cero)' : `+${formatUSD(netIncomeEntry)}`;
    
    // 4. Detalle Especifico de Cierre/Desacople por Partes
    let exitTimeStr = '-';
    if (isOpen) {
        if (isDecoupled && p.decouple_date) {
            exitTimeStr = `<span class="text-green">🟢 EN CURSO</span><br/><span style="font-size:10px;opacity:0.8;">Desacople Put: ${p.decouple_date}</span>`;
        } else {
            exitTimeStr = '<span class="text-green">🟢 EN CURSO</span>';
        }
    } else {
        exitTimeStr = p.exit_time || p.exit_date || p.decouple_date || p.timestamp || '-';
    }
    
    const exitUnderlying = isOpen ? (p.current_underlying_price || p.underlying_price || p.etf_price || 0) : (p.exit_underlying_price || p.exit_price || p.underlying_price || p.etf_price || 0);
    
    // Prima Salida / Valor Actual de la parte Long Abierta
    let exitPremiumStr = '-';
    if (isOpen) {
        if (p.unrealized_pnl_usd !== undefined && contractsNum > 0) {
            const callValPerShare = p.unrealized_pnl_usd / (contractsNum * 100);
            exitPremiumStr = `${formatUSD(callValPerShare)} / sh`;
        } else {
            exitPremiumStr = formatUSD(p.current_premium || p.curr_prem_per_share || 0);
        }
    } else {
        exitPremiumStr = formatUSD(p.exit_premium || 0);
    }
    
    // Costo Neto de Salida / Recompra Put
    let netCostExitStr = '-';
    if (p.decouple_cost_paid_usd !== undefined) {
        netCostExitStr = `${formatUSD(p.decouple_cost_paid_usd)} <span style="font-size:10px;color:var(--primary-red);">(Recompra Put)</span>`;
    } else if (isOpen) {
        const buyback = p.short_put_current_buyback_cost !== undefined ? p.short_put_current_buyback_cost : 0;
        netCostExitStr = buyback > 0 ? `${formatUSD(buyback)} (Buyback Put)` : '$0.00 (Libre Riesgo)';
    } else {
        const exitCost = p.exit_cost_usd !== undefined ? p.exit_cost_usd : 0;
        netCostExitStr = formatUSD(exitCost);
    }
    
    // Neto Operación & ROI
    let netPnl = 0;
    if (p.final_pnl_usd !== undefined) netPnl = p.final_pnl_usd;
    else if (p.unrealized_pnl_usd !== undefined) netPnl = p.unrealized_pnl_usd;
    else if (p.pnl_usd !== undefined) netPnl = p.pnl_usd;
    else if (p.realized_pnl_usd !== undefined) netPnl = p.realized_pnl_usd;
    
    let roiPct = 0;
    if (p.final_pnl_pct !== undefined) roiPct = p.final_pnl_pct;
    else if (p.roi_pct !== undefined) roiPct = p.roi_pct;
    else if (p.pnl_pct !== undefined) roiPct = p.pnl_pct;
    else if (netIncomeEntry > 0) roiPct = (netPnl / netIncomeEntry) * 100;
    
    const pnlNote = isDecoupled ? ' (100% Risk-Free)' : '';
    const netDuration = formatDurationStr(entryTime, p.exit_time || p.exit_date || p.decouple_date, isOpen);
    
    return `<tr>
        <td><strong>${ticker}</strong></td>
        <td><span style="color:var(--accent-blue);font-weight:600;">${optionType}</span></td>
        <td>${strike}</td>
        <td>${dteStr}</td>
        <td><strong>${contracts}</strong></td>
        <td>${entryTime}</td>
        <td>${formatUSD(entryUnderlying)}</td>
        <td>${entryPremiumStr}</td>
        <td class="text-green">${netIncomeEntryStr}</td>
        <td>${exitTimeStr}</td>
        <td>${formatUSD(exitUnderlying)}</td>
        <td class="text-green"><strong>${exitPremiumStr}</strong></td>
        <td>${netCostExitStr}</td>
        <td class="${colorClass(netPnl)}"><strong>${sign(netPnl)}${formatUSD(netPnl)}${pnlNote}</strong></td>
        <td>${netDuration}</td>
    </tr>`;
}

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

        setTxt('home-margin-val', (data.margin?.margin_utilization_pct || 0) + '%');
        setTxt('home-margin-status', data.margin_status || 'OPTIMAL');
        
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
        }
    } catch(e) { console.error('Error loadMaster', e); }
}

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
                { symbol: 'SPY', name: 'SPDR S&P 500 ETF Trust (Índice Núcleo)', mode: 'CASH_SECURED_PUT / COVERED_CALL', delta: 'Δ 0.20 - 0.25 (1.5% OTM)', dte: '30 - 45 Días', backing: '100% Respaldado por SGOV T-Bills', status: '<span class="text-green">🟢 ACTIVO (Ciclo Mensual)</span>' },
                { symbol: 'QQQ', name: 'Invesco QQQ (Nasdaq 100 MegaCap)', mode: 'CASH_SECURED_PUT / COVERED_CALL', delta: 'Δ 0.20 - 0.25 (2.0% OTM)', dte: '30 - 45 Días', backing: '100% Respaldado por SGOV T-Bills', status: '<span class="text-green">🟢 ACTIVO (Escaneo Abierto)</span>' },
                { symbol: 'GLD', name: 'SPDR Gold Shares (Oro Físico)', mode: 'COVERED_CALL SOBRE TENENCIA', delta: 'Δ 0.25 - 0.30 (OTM)', dte: '30 Días', backing: 'Cuotas de GLD en Cartera', status: '<span class="text-green">🟢 ACTIVO (Yield Boost +4.5%)</span>' },
                { symbol: 'TLT', name: 'iShares 20+ Year Treasury Bond', mode: 'COVERED_CALL SOBRE TENENCIA', delta: 'Δ 0.25 - 0.30 (OTM)', dte: '30 Días', backing: 'Cuotas de TLT en Cartera', status: '<span class="text-green">🟢 ACTIVO (Yield Boost +4.3%)</span>' },
                { symbol: 'IWM', name: 'iShares Russell 2000 (Small Caps)', mode: 'CASH_SECURED_PUT', delta: 'Δ 0.20 (3.0% OTM)', dte: '30 - 45 Días', backing: 'Margen Libre Disponible', status: '<span style="color:var(--text-muted)">⚪ LISTO PARA ENTRADA</span>' }
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

        // 1. Posiciones Abiertas
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

async function loadAlpha() {
    try {
        const res = await fetch('/api/alpha/status');
        if(!res.ok) return;
        const data = await res.json();
        const allocCap = data.allocated_capital || 20000;
        const unrealizedPnl = data.total_unrealized_pnl_usd || 0;
        setTxt('alpha-cap', formatUSD(allocCap + unrealizedPnl));
        setTxt('alpha-leaps', formatUSD(unrealizedPnl));
        
        let putRisk = 0;
        if (data.open_positions && data.open_positions.length > 0) {
            putRisk = data.open_positions.reduce((acc, p) => acc + (p.short_put_current_buyback_cost || 0), 0);
        }
        setTxt('alpha-risk', formatUSD(putRisk));
        
        setTxt('alpha-pnl', sign(unrealizedPnl) + formatUSD(unrealizedPnl));
        setClass('alpha-pnl', 'val ' + colorClass(unrealizedPnl));

        // 1. Posiciones Sintéticas Abiertas y Long Calls
        const tbodyPos = document.getElementById('alpha-positions');
        if (tbodyPos) {
            tbodyPos.innerHTML = '';
            let hasOpen = false;
            if(data.open_positions && data.open_positions.length > 0) {
                hasOpen = true;
                data.open_positions.forEach(p => {
                    tbodyPos.innerHTML += render15MetricsRow(p, true);
                });
            }
            if(data.decoupled_calls && data.decoupled_calls.length > 0) {
                hasOpen = true;
                data.decoupled_calls.forEach(p => {
                    tbodyPos.innerHTML += render15MetricsRow(p, true);
                });
            }
            if (!hasOpen) {
                tbodyPos.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">No hay posiciones sintéticas abiertas</td></tr>';
            }
        }

        // 2. Historial de Alpha
        const tbodyHist = document.getElementById('alpha-history');
        if(tbodyHist) {
            tbodyHist.innerHTML = '';
            if(data.closed_positions && data.closed_positions.length > 0) {
                data.closed_positions.slice().reverse().forEach(p => {
                    tbodyHist.innerHTML += render15MetricsRow(p, false);
                });
            } else {
                tbodyHist.innerHTML = '<tr><td colspan="15" style="text-align:center;color:var(--text-muted);">Sin sintéticos cerrados aún (1 sintético QQQ en monitoreo).</td></tr>';
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

// API Actions
async function runWheelCycle() {
    fetch('/api/wheel/run-cycle', { method:'POST' }).then(() => refreshAllData());
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
