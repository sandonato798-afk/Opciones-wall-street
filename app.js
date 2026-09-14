// Global State
let currentETFs = {};
let currentChain = null;
let currentLegs = [];
let payoffChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDayTradeStatus();
    loadETFCards();
    loadOptionChain('SPY', 30);
    initChart();
    loadPortfolio();

    // Event Listeners for Day Trading
    document.getElementById('btn-save-mode').addEventListener('click', saveModeAndBroker);
    document.getElementById('btn-run-scan').addEventListener('click', triggerDayTradeScan);

    // Event Listeners for Option Chain & Builder
    document.getElementById('btn-fetch-chain').addEventListener('click', () => {
        const symbol = document.getElementById('select-symbol').value;
        const dte = document.getElementById('select-dte').value;
        loadOptionChain(symbol, dte);
    });

    document.getElementById('btn-add-leg').addEventListener('click', () => {
        addLegRow();
    });

    document.getElementById('btn-calculate-payoff').addEventListener('click', () => {
        calculateAndRenderPayoff();
    });

    document.getElementById('btn-execute-paper').addEventListener('click', () => {
        executePaperTrade();
    });

    // Auto Refresh Day Trade Status every 10 seconds
    setInterval(loadDayTradeStatus, 10000);
});

// Navigation Tabs
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

// Day Trading Status & Mode Switcher
async function loadDayTradeStatus() {
    try {
        const res = await fetch('/api/daytrade/status');
        const data = await res.json();

        // Update Mode & Broker Indicators
        const isPaper = data.config.execution_mode === 'PAPER_TRADING';
        document.getElementById('live-mode-text').innerText = isPaper ? 'MODO: PAPER TRADING (SIMULACIÓN)' : `MODO: BROKER REAL (${data.config.broker_name})`;
        document.getElementById('broker-badge').innerText = `${data.config.broker_name} READY`;

        document.getElementById('select-mode').value = data.config.execution_mode;
        document.getElementById('select-broker').value = data.config.broker_name;

        // Update PnL
        const pnlEl = document.getElementById('dt-daily-pnl');
        pnlEl.innerText = (data.daily_pnl >= 0 ? '+' : '') + `$${data.daily_pnl.toFixed(2)} USD`;
        pnlEl.className = data.daily_pnl >= 0 ? 'text-green' : 'text-red';

        // Active Positions List
        const posContainer = document.getElementById('dt-active-positions');
        posContainer.innerHTML = '';

        if (data.open_positions.length === 0) {
            posContainer.innerHTML = '<p class="empty-msg">No hay posiciones intradiarias abiertas en este momento.</p>';
        } else {
            data.open_positions.forEach(pos => {
                const isProfit = pos.pnl_usd >= 0;
                const pnlClass = isProfit ? 'text-green' : 'text-red';

                posContainer.innerHTML += `
                    <div class="card" style="margin-bottom: 12px; border-left: 4px solid ${isProfit ? '#00FF87' : '#FF0844'}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <strong style="font-size: 16px; color:#00F2FE">${pos.option_ticker}</strong>
                                <div style="font-size: 12px; color:#9CA3AF">Entrada: $${pos.entry_premium.toFixed(2)} | Target TP: $${pos.target_profit_price.toFixed(2)} | Stop SL: $${pos.stop_loss_price.toFixed(2)}</div>
                            </div>
                            <div style="text-align:right">
                                <div class="${pnlClass}" style="font-size: 18px; font-weight:700;">
                                    ${pos.pnl_pct >= 0 ? '+' : ''}${pos.pnl_pct.toFixed(2)}% ($${pos.pnl_usd.toFixed(2)} USD)
                                </div>
                                <div style="font-size: 11px; color:#9CA3AF">${pos.contracts} Contrato(s)</div>
                            </div>
                        </div>
                    </div>
                `;
            });
        }

        // Closed History Table
        const historyBody = document.getElementById('dt-history-body');
        if (data.closed_trades.length > 0) {
            historyBody.innerHTML = '';
            data.closed_trades.forEach(t => {
                const isProf = t.final_pnl_usd >= 0;
                historyBody.innerHTML += `
                    <tr>
                        <td>${t.exit_time ? t.exit_time.split(' ')[1] : ''}</td>
                        <td style="color:#00F2FE">${t.option_ticker}</td>
                        <td>$${t.entry_premium.toFixed(2)}</td>
                        <td>$${t.exit_premium.toFixed(2)}</td>
                        <td><span class="info-pill">${t.exit_reason}</span></td>
                        <td style="color:${isProf ? '#00FF87' : '#FF0844'}; font-weight:700">
                            ${isProf ? '+' : ''}$${t.final_pnl_usd.toFixed(2)} USD
                        </td>
                    </tr>
                `;
            });
        }
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
    } catch (err) {
        console.error("Error ejecutando escaneo:", err);
    }
}

// TAB 1: Load ETF Cards
async function loadETFCards() {
    try {
        const res = await fetch('/api/etfs');
        currentETFs = await res.json();

        const container = document.getElementById('etf-cards-container');
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
    document.getElementById('select-symbol').value = symbol;
    document.querySelector('[data-tab="tab-chain"]').click();
    loadOptionChain(symbol, 30);
}

// TAB 2: Option Chain
async function loadOptionChain(symbol, dte) {
    try {
        const res = await fetch(`/api/option-chain?symbol=${symbol}&dte=${dte}`);
        currentChain = await res.json();

        document.getElementById('chain-etf-price').innerText = `$${currentChain.etf_price.toFixed(2)}`;
        document.getElementById('chain-iv').innerText = `${currentChain.implied_volatility_pct}%`;
        document.getElementById('chain-exp-date').innerText = currentChain.expiration_date;

        const tbody = document.getElementById('chain-table-body');
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

// TAB 3: Strategy Builder & Payoff Chart
function loadPreset(strategy) {
    const symbol = document.getElementById('select-symbol').value || 'SPY';
    const etfPrice = currentETFs[symbol] ? currentETFs[symbol].price : 560.0;
    
    currentLegs = [];
    const container = document.getElementById('legs-container');
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
    const symbol = document.getElementById('select-symbol').value || 'SPY';
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

        document.getElementById('metric-max-profit').innerText = payoff.max_profit === 'Ilimitado' ? 'Ilimitado' : `$${payoff.max_profit.toFixed(2)} USD`;
        document.getElementById('metric-max-loss').innerText = payoff.max_loss === 'Ilimitado' ? 'Ilimitado' : `$${payoff.max_loss.toFixed(2)} USD`;
        document.getElementById('metric-breakevens').innerText = payoff.breakevens.length > 0 ? payoff.breakevens.map(b => `$${b.toFixed(2)}`).join(', ') : 'N/A';

        renderChart(payoff.prices, payoff.payoffs);
    } catch (err) {
        console.error("Error calculando Payoff:", err);
    }
}

function initChart() {
    const ctx = document.getElementById('payoffChart').getContext('2d');
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
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9CA3AF' }
                }
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
    const symbol = document.getElementById('select-symbol').value || 'SPY';
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
            loadPortfolio();
            document.querySelector('[data-tab="tab-portfolio"]').click();
        }
    } catch (err) {
        console.error("Error abriendo posición:", err);
    }
}

// TAB 4: Load Portfolio
async function loadPortfolio() {
    try {
        const res = await fetch('/api/portfolio');
        const data = await res.json();

        document.getElementById('port-capital').innerText = `$${data.portfolio_capital.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
        document.getElementById('port-active-count').innerText = data.positions.length;

        let totalDelta = 0;
        let totalTheta = 0;

        const listContainer = document.getElementById('portfolio-positions-list');
        listContainer.innerHTML = '';

        if (data.positions.length === 0) {
            listContainer.innerHTML = '<p class="empty-msg">No hay posiciones de opciones abiertas.</p>';
            return;
        }

        data.positions.forEach(pos => {
            totalDelta += pos.greeks.delta;
            totalTheta += pos.greeks.theta;

            const posCard = document.createElement('div');
            posCard.className = 'card';
            posCard.style.marginBottom = '12px';
            posCard.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="font-size: 16px; color:#00F2FE">[${pos.symbol}] ${pos.strategy}</strong>
                        <div style="font-size: 12px; color:#9CA3AF">${pos.timestamp} | Entro ETF: $${pos.underlying_entry_price}</div>
                    </div>
                    <div style="text-align: right">
                        <div style="font-weight:700; font-size:16px; color:${pos.net_premium_usd >= 0 ? '#00FF87' : '#FF0844'}">
                            ${pos.type}: $${pos.net_premium_usd} USD
                        </div>
                        <div style="font-size: 11px; color:#9CA3AF">Delta: ${pos.greeks.delta} | Theta: ${pos.greeks.theta}</div>
                    </div>
                </div>
            `;
            listContainer.appendChild(posCard);
        });

        document.getElementById('port-delta').innerText = (totalDelta >= 0 ? '+' : '') + totalDelta.toFixed(2);
        document.getElementById('port-theta').innerText = (totalTheta >= 0 ? '+' : '') + `$${totalTheta.toFixed(2)} / día`;
    } catch (err) {
        console.error("Error cargando portafolio:", err);
    }
}
