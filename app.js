// Global State
let currentETFs = {};
let currentChain = null;
let currentLegs = [];
let payoffChart = null;
let distributionChart = null;
let latestWheelData = null;
let latestDayTradeData = null;
let profitMode = "AUTONOMOUS"; // "AUTONOMOUS" or "MANUAL"

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initDistributionChart();
    loadWheelStatus();
    loadDayTradeStatus();
    loadIssuedContracts();
    loadETFCards();
    loadOptionChain('SPY', 30);
    initChart();

    // Event Listeners for Wheel & Compounding
    const btnWheel = document.getElementById('btn-run-wheel-cycle');
    if (btnWheel) btnWheel.addEventListener('click', triggerWheelCycle);

    // Event Listeners for Day Trading
    const btnSaveMode = document.getElementById('btn-save-mode');
    if (btnSaveMode) btnSaveMode.addEventListener('click', saveModeAndBroker);

    const btnScan = document.getElementById('btn-run-scan');
    if (btnScan) btnScan.addEventListener('click', triggerDayTradeScan);

    // Event Listeners for Option Chain & Builder
    const btnFetchChain = document.getElementById('btn-fetch-chain');
    if (btnFetchChain) {
        btnFetchChain.addEventListener('click', () => {
            const symbol = document.getElementById('select-symbol').value;
            const dte = document.getElementById('select-dte').value;
            loadOptionChain(symbol, dte);
        });
    }

    const btnAddLeg = document.getElementById('btn-add-leg');
    if (btnAddLeg) btnAddLeg.addEventListener('click', addLegRow);

    const btnPayoff = document.getElementById('btn-calculate-payoff');
    if (btnPayoff) btnPayoff.addEventListener('click', calculateAndRenderPayoff);

    const btnExecutePaper = document.getElementById('btn-execute-paper');
    if (btnExecutePaper) btnExecutePaper.addEventListener('click', executePaperTrade);

    // Auto Refresh Status
    setInterval(() => {
        loadDayTradeStatus();
        loadWheelStatus();
        loadIssuedContracts();
    }, 10000);
});

// Sidebar Tabs Navigation
function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const target = tab.dataset.tab;
            const targetEl = document.getElementById(target);
            if (targetEl) targetEl.classList.add('active');
        });
    });
}

// Toggle Profit Reinvestment Mode (Autonomous vs Manual)
function toggleProfitMode() {
    const chk = document.getElementById('chk-profit-mode');
    const labelText = document.getElementById('toggle-label-text');
    const descAuto = document.getElementById('profit-mode-desc-auto');
    const descManual = document.getElementById('profit-mode-desc-manual');

    if (chk.checked) {
        profitMode = "MANUAL";
        if (labelText) labelText.innerText = "🎛️ Modo Manual";
        if (descAuto) descAuto.style.display = 'none';
        if (descManual) descManual.style.display = 'block';
    } else {
        profitMode = "AUTONOMOUS";
        if (labelText) labelText.innerText = "🤖 Modo Autónomo";
        if (descAuto) descAuto.style.display = 'block';
        if (descManual) descManual.style.display = 'none';
    }
}

async function executeManualProfitAction(action) {
    if (!latestDayTradeData) return;
    const availPnl = latestDayTradeData.total_pnl_usd || 0.0;

    if (availPnl <= 0) {
        alert("No hay ganancias acumuladas de Day Trading para asignar en este momento.");
        return;
    }

    if (action === 'TRANSFER_WHEEL') {
        try {
            const res = await fetch('/api/wheel/transfer-profit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount_usd: availPnl })
            });
            const result = await res.json();
            if (result.status === 'SUCCESS') {
                alert(`¡Exitoso! $${availPnl.toFixed(2)} USD transferidos a la Rueda. Compradas +${result.result.shares_bought} acciones ETF.`);
                loadWheelStatus();
            }
        } catch (err) {
            console.error("Error en transferencia manual:", err);
        }
    } else if (action === 'KEEP_DAYTRADE') {
        alert(`Ganancias de $${availPnl.toFixed(2)} USD retenidas en la base de Day Trading.`);
    } else if (action === 'HOLD_CASH') {
        alert(`Ganancias de $${availPnl.toFixed(2)} USD retenidas como Efectivo Libre en Caja.`);
    }
}

// Master Portfolio Sync
function syncMasterPortfolio() {
    if (!latestWheelData || !latestDayTradeData) return;

    const dtCapital = latestDayTradeData.capital || 100000.0;
    const dtTotalPnlUsd = latestDayTradeData.total_pnl_usd || 0.0;
    const dtTotalPnlPct = latestDayTradeData.total_pnl_pct || 0.0;

    let cashInTrades = 0.0;
    if (latestDayTradeData.open_positions && latestDayTradeData.open_positions.length > 0) {
        latestDayTradeData.open_positions.forEach(p => {
            const cost = p.total_cost_usd || ((p.entry_premium * 100 * p.contracts) + (p.open_fee_usd || 0));
            cashInTrades += cost;
        });
    }

    const freeCash = Math.max(0.0, dtCapital - cashInTrades);
    const shares = latestWheelData.etf_shares || 0.0;
    const etfPrice = latestWheelData.etf_price || 560.50;
    const sharesVal = shares * etfPrice;
    const totalNav = dtCapital + sharesVal;

    const masterNavEl = document.getElementById('master-nav');
    if (masterNavEl) masterNavEl.innerText = `$${totalNav.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

    const masterCashEl = document.getElementById('master-cash');
    if (masterCashEl) masterCashEl.innerText = `$${dtCapital.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

    const masterFreeCashEl = document.getElementById('master-free-cash');
    if (masterFreeCashEl) masterFreeCashEl.innerText = `$${freeCash.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

    const masterInTradesEl = document.getElementById('master-in-trades');
    if (masterInTradesEl) masterInTradesEl.innerText = `$${cashInTrades.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

    const masterOpenCountEl = document.getElementById('master-open-trades-count');
    if (masterOpenCountEl) masterOpenCountEl.innerText = `${latestDayTradeData.open_positions ? latestDayTradeData.open_positions.length : 0} operaciones abiertas`;

    const masterSharesValEl = document.getElementById('master-shares-val');
    if (masterSharesValEl) masterSharesValEl.innerText = `$${sharesVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

    const masterSharesCountEl = document.getElementById('master-shares-count');
    if (masterSharesCountEl) masterSharesCountEl.innerText = `${shares.toFixed(4)} acciones ${latestWheelData.etf_symbol || 'SPY'}`;

    const masterDtPnlEl = document.getElementById('master-dt-pnl');
    if (masterDtPnlEl) {
        masterDtPnlEl.innerText = (dtTotalPnlUsd >= 0 ? '+' : '') + `$${dtTotalPnlUsd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
        masterDtPnlEl.className = dtTotalPnlUsd >= 0 ? 'value text-green' : 'value text-red';
    }

    const masterDtPctEl = document.getElementById('master-dt-pct');
    if (masterDtPctEl) masterDtPctEl.innerText = (dtTotalPnlPct >= 0 ? '+' : '') + `${dtTotalPnlPct.toFixed(2)}% realizado`;

    const manualPnlText = document.getElementById('manual-profit-avail-text');
    if (manualPnlText) manualPnlText.innerText = (dtTotalPnlUsd >= 0 ? '+' : '') + `$${dtTotalPnlUsd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
}

// Load Active Issued Option Contracts & DTE Expiration Monitor
async function loadIssuedContracts() {
    try {
        const tbody = document.getElementById('issued-contracts-body');
        if (!tbody) return;

        let contractsList = [];

        // 1. Fetch Wheel Active Contracts
        if (latestWheelData && latestWheelData.wheel_positions) {
            latestWheelData.wheel_positions.forEach(pos => {
                contractsList.push({
                    ticker: pos.ticker,
                    strategy: pos.strategy_type === 'CASH_SECURED_PUT' ? 'Cash-Secured Put' : 'Covered Call',
                    symbol: pos.symbol,
                    strike: pos.strike,
                    contracts: pos.contracts || 1,
                    premium: pos.premium_collected_usd,
                    issued_date: pos.issued_date,
                    expiration_date: pos.expiration_date,
                    status: pos.status || 'ACTIVE',
                    source: 'WHEEL'
                });
            });
        }

        // 2. Fetch Day Trading Open Positions
        if (latestDayTradeData && latestDayTradeData.open_positions) {
            latestDayTradeData.open_positions.forEach(pos => {
                contractsList.push({
                    ticker: pos.option_ticker,
                    strategy: `Day Trade ${pos.option_type}`,
                    symbol: pos.symbol,
                    strike: pos.strike,
                    contracts: pos.contracts || 1,
                    premium: pos.entry_premium * 100 * pos.contracts,
                    issued_date: pos.entry_time,
                    expiration_date: 'Intradiario (Hoy)',
                    status: 'OPEN',
                    source: 'DAYTRADE'
                });
            });
        }

        if (contractsList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" style="color:var(--text-muted)">No hay contratos de opciones activos emitidos en este momento.</td></tr>`;
            return;
        }

        tbody.innerHTML = '';
        const today = new Date();

        contractsList.forEach(c => {
            let dteBadge = '';
            if (c.source === 'DAYTRADE' || c.expiration_date.includes('Intradiario')) {
                dteBadge = `<span class="badge badge-dte-today">⚡ 0 DTE - Vence Hoy</span>`;
            } else {
                const expDate = new Date(c.expiration_date);
                const diffTime = expDate - today;
                const diffDays = Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
                if (diffDays === 0) {
                    dteBadge = `<span class="badge badge-dte-today">⏰ Vence Hoy</span>`;
                } else {
                    dteBadge = `<span class="badge badge-dte">📅 ${diffDays} días restantes</span>`;
                }
            }

            tbody.innerHTML += `
                <tr>
                    <td style="color:#00F2FE; font-weight:700;">${c.ticker}</td>
                    <td><span class="badge badge-cyan">${c.strategy}</span></td>
                    <td style="font-weight:700;">${c.symbol} $${c.strike.toFixed(2)}</td>
                    <td><strong>${c.contracts}</strong></td>
                    <td style="color:#00FF87; font-weight:700;">$${c.premium.toFixed(2)} USD</td>
                    <td style="font-size:11px; color:#9CA3AF;">${c.issued_date ? c.issued_date.split(' ')[0] : '-'}</td>
                    <td style="font-weight:600;">${c.expiration_date}</td>
                    <td>${dteBadge}</td>
                    <td><span class="badge badge-live">${c.status}</span></td>
                </tr>
            `;
        });
    } catch (err) {
        console.error("Error cargando contratos emitidos:", err);
    }
}

// TAB WHEEL & COMPOUNDING STATUS
async function loadWheelStatus() {
    try {
        const res = await fetch('/api/wheel/status');
        const data = await res.json();
        latestWheelData = data;

        const initialCap = data.initial_capital_usd || 100000.0;
        const shares = data.etf_shares || 0.0;
        const etfPrice = data.etf_price || 560.50;
        const sharesVal = shares * etfPrice;
        const cashVal = data.cash_balance !== undefined ? data.cash_balance : initialCap;
        const navVal = data.portfolio_nav_usd || (sharesVal + cashVal);
        const totalReinvest = data.total_reinvested_usd || 0.0;

        const sharesPct = navVal > 0 ? ((sharesVal / navVal) * 100.0).toFixed(1) : "0.0";
        const cashPct = navVal > 0 ? ((cashVal / navVal) * 100.0).toFixed(1) : "100.0";

        const wInitCapEl = document.getElementById('wheel-initial-cap');
        if (wInitCapEl) wInitCapEl.innerText = `$${initialCap.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const wSharesEl = document.getElementById('wheel-shares');
        if (wSharesEl) wSharesEl.innerText = `${shares.toFixed(4)} acciones`;

        const wTotalReinvestEl = document.getElementById('wheel-total-reinvest');
        if (wTotalReinvestEl) wTotalReinvestEl.innerText = `+$${totalReinvest.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const wNavEl = document.getElementById('wheel-nav');
        if (wNavEl) wNavEl.innerText = `$${navVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const wCagrEl = document.getElementById('wheel-cagr');
        if (wCagrEl) wCagrEl.innerText = `+${data.cagr_pct >= 0 ? data.cagr_pct : 28.5}% anual`;

        const dSharesValEl = document.getElementById('dist-shares-val');
        if (dSharesValEl) dSharesValEl.innerText = `$${sharesVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const dSharesPctEl = document.getElementById('dist-shares-pct');
        if (dSharesPctEl) dSharesPctEl.innerText = `${sharesPct}%`;

        const dCashValEl = document.getElementById('dist-cash-val');
        if (dCashValEl) dCashValEl.innerText = `$${cashVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const dCashPctEl = document.getElementById('dist-cash-pct');
        if (dCashPctEl) dCashPctEl.innerText = `${cashPct}%`;

        const dReinvestValEl = document.getElementById('dist-reinvest-val');
        if (dReinvestValEl) dReinvestValEl.innerText = `+$${totalReinvest.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        renderDistributionChart(sharesVal, cashVal, data.etf_symbol || 'SPY');

        const tbody = document.getElementById('wheel-holdings-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td><strong>${data.etf_symbol || 'SPY'}</strong></td>
                    <td><span class="badge badge-cyan">Acciones Físicas</span></td>
                    <td style="color:#00F2FE; font-weight: 700;">${shares.toFixed(4)}</td>
                    <td>$${etfPrice.toFixed(2)} USD</td>
                    <td style="color:#00F2FE; font-weight: 700;">$${sharesVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
                    <td><strong>${sharesPct}%</strong></td>
                    <td><span class="badge badge-green">${shares >= 10 ? 'Covered Call Activa' : 'Acumulando Acciones'}</span></td>
                </tr>
                <tr>
                    <td><strong>USD Cash</strong></td>
                    <td><span class="badge badge-green">Garantía Líquida</span></td>
                    <td>-</td>
                    <td>$1.00 USD</td>
                    <td style="color:#00FF87; font-weight: 700;">$${cashVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
                    <td><strong>${cashPct}%</strong></td>
                    <td><span class="badge badge-cyan">Respaldando Cash-Secured Put</span></td>
                </tr>
                <tr style="background: rgba(255, 255, 255, 0.04); font-weight: bold;">
                    <td colspan="4" style="text-align: right; color: #9CA3AF;">PATRIMONIO TOTAL (NAV):</td>
                    <td style="color:#FFB300; font-size: 15px;">$${navVal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
                    <td style="color:#00FF87;">100.0%</td>
                    <td style="color:#FFB300;">Rueda Auto-Compounding</td>
                </tr>
            `;
        }

        syncMasterPortfolio();
    } catch (err) {
        console.error("Error cargando estado Rueda:", err);
    }
}

async function triggerWheelCycle() {
    try {
        const res = await fetch('/api/wheel/run-cycle', { method: 'POST' });
        const result = await res.json();
        alert(`¡Ciclo de Rueda ejecutado! Prima cobrada: $${result.cycle.premium_collected_usd} USD. Compradas +${result.cycle.shares_bought} acciones de ${result.cycle.symbol}`);
        loadWheelStatus();
        loadIssuedContracts();
    } catch (err) {
        console.error("Error ejecutando ciclo de rueda:", err);
    }
}

function initDistributionChart() {
    const canvas = document.getElementById('distributionChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    distributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Acciones ETFs (SPY)', 'Efectivo / Garantía CSP'],
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#00F2FE', '#00FF87'],
                borderColor: '#111827',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9CA3AF', boxWidth: 12, font: { size: 11 } }
                }
            },
            cutout: '70%'
        }
    });
}

function renderDistributionChart(sharesVal, cashVal, symbol) {
    if (!distributionChart) return;
    distributionChart.data.labels = [`Acciones ${symbol}`, 'Efectivo Garantía'];
    distributionChart.data.datasets[0].data = [sharesVal, cashVal];
    distributionChart.update();
}

// Day Trading Status & Mode Switcher
async function loadDayTradeStatus() {
    try {
        const res = await fetch('/api/daytrade/status');
        const data = await res.json();
        latestDayTradeData = data;

        const isPaper = data.config.execution_mode === 'PAPER_TRADING';
        const liveModeEl = document.getElementById('live-mode-text');
        if (liveModeEl) liveModeEl.innerText = isPaper ? 'PAPER TRADING' : `BROKER REAL (${data.config.broker_name})`;

        const brokerBadgeEl = document.getElementById('broker-badge');
        if (brokerBadgeEl) brokerBadgeEl.innerText = `${data.config.broker_name} READY`;

        const selMode = document.getElementById('select-mode');
        if (selMode) selMode.value = data.config.execution_mode;

        const selBroker = document.getElementById('select-broker');
        if (selBroker) selBroker.value = data.config.broker_name;

        const kpiCapEl = document.getElementById('kpi-initial-cap');
        if (kpiCapEl) kpiCapEl.innerText = `$${data.initial_capital_usd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
        
        const dailyPctEl = document.getElementById('kpi-daily-pct');
        if (dailyPctEl) {
            dailyPctEl.innerText = (data.daily_pnl_pct >= 0 ? '+' : '') + `${data.daily_pnl_pct.toFixed(2)}%`;
            dailyPctEl.className = data.daily_pnl_pct >= 0 ? 'value text-green' : 'value text-red';
        }

        const dailyUsdEl = document.getElementById('kpi-daily-usd');
        if (dailyUsdEl) dailyUsdEl.innerText = (data.daily_pnl_usd >= 0 ? '+' : '') + `$${data.daily_pnl_usd.toFixed(2)} USD`;

        const totalPctEl = document.getElementById('kpi-total-pct');
        if (totalPctEl) {
            totalPctEl.innerText = (data.total_pnl_pct >= 0 ? '+' : '') + `${data.total_pnl_pct.toFixed(2)}%`;
            totalPctEl.className = data.total_pnl_pct >= 0 ? 'value text-cyan' : 'value text-red';
        }

        const totalUsdEl = document.getElementById('kpi-total-usd');
        if (totalUsdEl) totalUsdEl.innerText = (data.total_pnl_usd >= 0 ? '+' : '') + `$${data.total_pnl_usd.toFixed(2)} USD`;

        const uptimeEl = document.getElementById('kpi-uptime');
        if (uptimeEl) uptimeEl.innerText = `${data.uptime_hours.toFixed(1)} hrs`;
        
        const winrateEl = document.getElementById('kpi-winrate');
        if (winrateEl) winrateEl.innerText = `${data.stats.win_rate.toFixed(1)}%`;

        const tradesCountEl = document.getElementById('kpi-trades-count');
        if (tradesCountEl) tradesCountEl.innerText = `${data.stats.total} trade(s) (${data.stats.wins}W / ${data.stats.losses}L)`;

        const commissionsEl = document.getElementById('kpi-commissions');
        if (commissionsEl) commissionsEl.innerText = `-$${data.total_commissions_paid.toFixed(2)} USD`;

        const dtCurrCapEl = document.getElementById('dt-current-capital');
        if (dtCurrCapEl) dtCurrCapEl.innerText = `$${data.capital.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

        const posContainer = document.getElementById('dt-active-positions');
        if (posContainer) {
            posContainer.innerHTML = '';
            if (data.open_positions.length === 0) {
                posContainer.innerHTML = '<p class="empty-msg" style="color:var(--text-muted)">No hay posiciones intradiarias abiertas en este momento. Escaneando durante horario de mercado...</p>';
            } else {
                data.open_positions.forEach(pos => {
                    const isProfit = pos.pnl_usd >= 0;
                    const pnlClass = isProfit ? 'text-green' : 'text-red';
                    const entryCostUsd = pos.total_cost_usd || ((pos.entry_premium * 100 * pos.contracts) + (pos.open_fee_usd || 0));
                    const currValUsd = (pos.current_premium * 100 * pos.contracts);

                    posContainer.innerHTML += `
                        <div class="card" style="margin-bottom: 12px; border-left: 4px solid ${isProfit ? '#00FF87' : '#FF0844'}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <strong style="font-size: 16px; color:#00F2FE">${pos.option_ticker}</strong>
                                    <span class="badge badge-cyan" style="margin-left: 8px;">${pos.contracts} Contrato(s)</span>
                                    <div style="font-size: 12px; color:#9CA3AF; margin-top: 4px;">
                                        Inversión: <strong>$${entryCostUsd.toFixed(2)} USD</strong> ($${pos.entry_premium.toFixed(2)}/acción) | 
                                        Valor Actual: <strong>$${currValUsd.toFixed(2)} USD</strong> ($${pos.current_premium.toFixed(2)}/acción) | 
                                        TP: $${pos.target_profit_price.toFixed(2)} | SL: $${pos.stop_loss_price.toFixed(2)}
                                    </div>
                                </div>
                                <div style="text-align:right">
                                    <div class="${pnlClass}" style="font-size: 18px; font-weight:700;">
                                        ${pos.pnl_pct >= 0 ? '+' : ''}${pos.pnl_pct.toFixed(2)}% (${pos.pnl_usd >= 0 ? '+' : ''}$${pos.pnl_usd.toFixed(2)} USD)
                                    </div>
                                    <div style="font-size: 11px; color:#9CA3AF">Comisión: -$${pos.open_fee_usd.toFixed(2)} USD</div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        }

        const historyBody = document.getElementById('dt-history-body');
        if (historyBody && data.closed_trades && data.closed_trades.length > 0) {
            historyBody.innerHTML = '';
            data.closed_trades.forEach(t => {
                const contracts = t.contracts || 1;
                const openFee = t.open_fee_usd || (contracts * 0.65);
                const closeFee = t.close_fee_usd || (contracts * 0.65);
                const totalFees = t.total_fees_usd || (openFee + closeFee);
                
                const entryCapitalUsd = t.total_cost_usd || ((t.entry_premium * 100 * contracts) + openFee);
                const exitCapitalUsd = (t.exit_premium * 100 * contracts) - closeFee;
                const netPnlUsd = t.final_pnl_usd !== undefined ? t.final_pnl_usd : (exitCapitalUsd - entryCapitalUsd);
                const netPnlPct = entryCapitalUsd > 0 ? ((netPnlUsd / entryCapitalUsd) * 100.0) : (t.final_pnl_pct || 0);

                const isProf = netPnlUsd >= 0;
                const reasonBadgeColor = t.exit_reason === 'TAKE_PROFIT' ? '#00FF87' : (t.exit_reason === 'STOP_LOSS' ? '#FF0844' : '#FFB300');
                const reasonLabel = t.exit_reason === 'TAKE_PROFIT' ? '🎯 Take Profit (+35%)' : (t.exit_reason === 'STOP_LOSS' ? '🛑 Stop Loss (-18%)' : '⏰ Cierre EOD');

                historyBody.innerHTML += `
                    <tr>
                        <td>
                            <div style="font-weight:600;">${t.exit_time ? t.exit_time.split(' ')[1] : '-'}</div>
                            <div style="font-size:10px; color:#9CA3AF;">${t.entry_time ? 'Entrada: ' + t.entry_time.split(' ')[1] : ''}</div>
                        </td>
                        <td>
                            <div style="color:#00F2FE; font-weight:700;">${t.option_ticker}</div>
                            <div style="font-size:11px; color:#9CA3AF;">${contracts} Contrato(s)</div>
                        </td>
                        <td style="font-weight:700; color:#FFFFFF;">$${entryCapitalUsd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
                        <td style="font-weight:700; color:${isProf ? '#00FF87' : '#FF0844'};">$${exitCapitalUsd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD</td>
                        <td style="color:#FF0844;">-$${totalFees.toFixed(2)} USD</td>
                        <td><span class="badge" style="background: rgba(255,255,255,0.06); color:${reasonBadgeColor}; border: 1px solid ${reasonBadgeColor}33;">${reasonLabel}</span></td>
                        <td style="color:${isProf ? '#00FF87' : '#FF0844'}; font-weight:700; font-size: 14px;">
                            ${isProf ? '+' : ''}$${netPnlUsd.toLocaleString('en-US', {minimumFractionDigits: 2})} USD
                            <div style="font-size: 11px;">(${isProf ? '+' : ''}${netPnlPct.toFixed(2)}%)</div>
                        </td>
                    </tr>
                `;
            });
        }

        syncMasterPortfolio();
    } catch (err) {
        console.error("Error cargando estado Day Trading:", err);
    }
}

async function saveModeAndBroker() {
    const mode = document.getElementById('select-mode').value;
    const broker = document.getElementById('select-broker').value;

    try {
        const res = await fetch('/api/daytrade/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, broker })
        });
        const result = await res.json();
        if (result.status === 'SUCCESS') {
            alert(`Configuración actualizada a: ${mode} con broker ${broker}`);
            loadDayTradeStatus();
        }
    } catch (err) {
        console.error("Error guardando modo:", err);
    }
}

async function triggerDayTradeScan() {
    try {
        const res = await fetch('/api/daytrade/scan', { method: 'POST' });
        const result = await res.json();
        alert("Escaneo intradiario de opciones ejecutado exitosamente.");
        loadDayTradeStatus();
        loadIssuedContracts();
    } catch (err) {
        console.error("Error ejecutando escaneo:", err);
    }
}

// ETF CARDS
async function loadETFCards() {
    try {
        const res = await fetch('/api/etfs');
        currentETFs = await res.json();

        const container = document.getElementById('etf-cards-container');
        if (!container) return;
        container.innerHTML = '';

        Object.values(currentETFs).forEach(etf => {
            const isPos = etf.change_pct >= 0;
            const changeClass = isPos ? 'pos' : 'neg';
            const changeSign = isPos ? '+' : '';

            const cardHtml = `
                <div class="etf-card" onclick="selectETFFromCard('${etf.symbol}')">
                    <div class="etf-header">
                        <span class="etf-symbol">${etf.symbol}</span>
                        <span class="etf-change ${changeClass}">${changeSign}${etf.change_pct}%</span>
                    </div>
                    <div class="etf-price">$${etf.price.toFixed(2)} USD</div>
                    <div class="etf-name">${etf.name}</div>

                    <div class="iv-bar-container">
                        <div class="iv-header">
                            <span>IV Rank (Volatilidad):</span>
                            <strong>${etf.iv_rank}%</strong>
                        </div>
                        <div class="iv-progress">
                            <div class="iv-fill" style="width: ${etf.iv_rank}%"></div>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML += cardHtml;
        });
    } catch (err) {
        console.error("Error cargando ETFs:", err);
    }
}

function selectETFFromCard(symbol) {
    const selSym = document.getElementById('select-symbol');
    if (selSym) selSym.value = symbol;
    const tabChainBtn = document.querySelector('[data-tab="tab-chain"]');
    if (tabChainBtn) tabChainBtn.click();
    loadOptionChain(symbol, 30);
}

// OPTION CHAIN
async function loadOptionChain(symbol, dte) {
    try {
        const res = await fetch(`/api/option-chain?symbol=${symbol}&dte=${dte}`);
        currentChain = await res.json();

        const pEl = document.getElementById('chain-etf-price');
        if (pEl) pEl.innerText = `$${currentChain.etf_price.toFixed(2)}`;

        const ivEl = document.getElementById('chain-iv');
        if (ivEl) ivEl.innerText = `${currentChain.implied_volatility_pct}%`;

        const expEl = document.getElementById('chain-exp-date');
        if (expEl) expEl.innerText = currentChain.expiration_date;

        const tbody = document.getElementById('chain-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        currentChain.chain.forEach(row => {
            const c = row.call;
            const p = row.put;

            const tr = document.createElement('tr');
            if (row.moneyness === 'ATM') {
                tr.classList.add('itm-row');
            }

            tr.innerHTML = `
                <td style="color: #00F2FE">${c.delta}</td>
                <td style="color: #9CA3AF">${c.theta}</td>
                <td>$${c.bid.toFixed(2)}</td>
                <td>$${c.ask.toFixed(2)}</td>
                <td style="font-weight:700">$${c.last_price.toFixed(2)}</td>
                <td class="strike-cell">$${row.strike.toFixed(2)}</td>
                <td style="font-weight:700">$${p.last_price.toFixed(2)}</td>
                <td>$${p.bid.toFixed(2)}</td>
                <td>$${p.ask.toFixed(2)}</td>
                <td style="color: #9CA3AF">${p.theta}</td>
                <td style="color: #FF0844">${p.delta}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error cargando Option Chain:", err);
    }
}

// STRATEGY BUILDER
function loadPreset(strategy) {
    const symbolEl = document.getElementById('select-symbol');
    const symbol = symbolEl ? symbolEl.value : 'SPY';
    const etfPrice = currentETFs[symbol] ? currentETFs[symbol].price : 560.0;
    
    currentLegs = [];
    const container = document.getElementById('legs-container');
    if (!container) return;
    container.innerHTML = '';

    if (strategy === 'covered_call') {
        const strike = Math.round(etfPrice / 5) * 5 + 5;
        addLeg('SELL', 'CALL', strike, 4.50, 1);
    } else if (strategy === 'cash_put') {
        const strike = Math.round(etfPrice / 5) * 5 - 5;
        addLeg('SELL', 'PUT', strike, 3.80, 1);
    } else if (strategy === 'bull_put_spread') {
        const shortStrike = Math.round(etfPrice / 5) * 5 - 5;
        const longStrike = shortStrike - 5;
        addLeg('SELL', 'PUT', shortStrike, 3.50, 1);
        addLeg('BUY', 'PUT', longStrike, 1.20, 1);
    } else if (strategy === 'iron_condor') {
        const putShort = Math.round(etfPrice / 5) * 5 - 10;
        const putLong = putShort - 5;
        const callShort = Math.round(etfPrice / 5) * 5 + 10;
        const callLong = callShort + 5;

        addLeg('SELL', 'PUT', putShort, 2.80, 1);
        addLeg('BUY', 'PUT', putLong, 0.90, 1);
        addLeg('SELL', 'CALL', callShort, 2.50, 1);
        addLeg('BUY', 'CALL', callLong, 0.80, 1);
    }

    calculateAndRenderPayoff();
}

function addLeg(action = 'SELL', type = 'PUT', strike = 550, premium = 3.50, qty = 1) {
    const container = document.getElementById('legs-container');
    if (!container) return;
    const legId = Date.now() + Math.random();

    const legDiv = document.createElement('div');
    legDiv.className = 'leg-row';
    legDiv.id = `leg-${legId}`;

    legDiv.innerHTML = `
        <select class="leg-action" style="flex: 1.2">
            <option value="SELL" ${action === 'SELL' ? 'selected' : ''}>SELL (Vender)</option>
            <option value="BUY" ${action === 'BUY' ? 'selected' : ''}>BUY (Comprar)</option>
        </select>
        <select class="leg-type" style="flex: 1">
            <option value="PUT" ${type === 'PUT' ? 'selected' : ''}>PUT</option>
            <option value="CALL" ${type === 'CALL' ? 'selected' : ''}>CALL</option>
        </select>
        <input type="number" class="leg-strike" value="${strike}" placeholder="Strike K" style="flex: 1">
        <input type="number" step="0.1" class="leg-premium" value="${premium}" placeholder="Prima $" style="flex: 1">
        <button class="btn-remove-leg" onclick="removeLeg('leg-${legId}')">✖</button>
    `;

    container.appendChild(legDiv);
}

function addLegRow() {
    const symbolEl = document.getElementById('select-symbol');
    const symbol = symbolEl ? symbolEl.value : 'SPY';
    const etfPrice = currentETFs[symbol] ? currentETFs[symbol].price : 560.0;
    addLeg('SELL', 'PUT', Math.round(etfPrice / 5) * 5, 3.00, 1);
}

function removeLeg(legId) {
    const el = document.getElementById(legId);
    if (el) el.remove();
}

function getLegsFromUI() {
    const rows = document.querySelectorAll('.leg-row');
    const legs = [];
    rows.forEach(row => {
        legs.push({
            action: row.querySelector('.leg-action').value,
            type: row.querySelector('.leg-type').value,
            strike: parseFloat(row.querySelector('.leg-strike').value) || 500,
            premium: parseFloat(row.querySelector('.leg-premium').value) || 1.0,
            qty: 1
        });
    });
    return legs;
}

async function calculateAndRenderPayoff() {
    const legs = getLegsFromUI();
    if (legs.length === 0) return;

    try {
        const res = await fetch('/api/payoff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ legs })
        });
        const payoff = await res.json();

        const maxProfEl = document.getElementById('metric-max-profit');
        if (maxProfEl) maxProfEl.innerText = payoff.max_profit === 'Ilimitado' ? 'Ilimitado' : `$${payoff.max_profit.toFixed(2)} USD`;

        const maxLossEl = document.getElementById('metric-max-loss');
        if (maxLossEl) maxLossEl.innerText = payoff.max_loss === 'Ilimitado' ? 'Ilimitado' : `$${payoff.max_loss.toFixed(2)} USD`;

        const bkEvEl = document.getElementById('metric-breakevens');
        if (bkEvEl) bkEvEl.innerText = payoff.breakevens.length > 0 ? payoff.breakevens.map(b => `$${b.toFixed(2)}`).join(', ') : 'N/A';

        renderChart(payoff.prices, payoff.payoffs);
    } catch (err) {
        console.error("Error calculando Payoff:", err);
    }
}

function initChart() {
    const canvas = document.getElementById('payoffChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    payoffChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'P&L al Vencimiento (USD)',
                data: [],
                borderColor: '#00F2FE',
                backgroundColor: 'rgba(0, 242, 254, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9CA3AF' } },
                y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9CA3AF' } }
            }
        }
    });
}

function renderChart(prices, payoffs) {
    if (!payoffChart) return;
    payoffChart.data.labels = prices.map(p => `$${p.toFixed(1)}`);
    payoffChart.data.datasets[0].data = payoffs;
    payoffChart.update();
}

async function executePaperTrade() {
    const symbolEl = document.getElementById('select-symbol');
    const symbol = symbolEl ? symbolEl.value : 'SPY';
    const legs = getLegsFromUI();
    if (legs.length === 0) {
        alert("Agrega al menos una leg a la estrategia.");
        return;
    }

    try {
        const res = await fetch('/api/trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol,
                strategy: "Estrategia Simulado Opciones",
                legs
            })
        });
        const result = await res.json();
        if (result.status === "SUCCESS") {
            alert(`¡Posición simulada abierta exitosamente en ${symbol}!`);
            loadIssuedContracts();
        }
    } catch (err) {
        console.error("Error abriendo posición:", err);
    }
}
