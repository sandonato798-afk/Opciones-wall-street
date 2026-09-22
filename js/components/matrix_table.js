// js/components/matrix_table.js - Renderizador de Matrices Desglosadas de 4 Columnas
// Utilizado en Capa 2 (Alpha Sintéticos LEAPS) y Capa 5 (Bull Market PMCC)

function renderAlphaMatrixTable(p, isOpen = true) {
    const symbol = p.symbol || p.ticker || 'QQQ';
    const isDecoupled = p.decoupled || p.status === 'RISK_FREE_LONG_CALL' || p.status === 'FREE_RUNNER_LONG_CALL';
    const dteVal = p.dte !== undefined ? p.dte : 120;
    const entryDate = p.entry_date || p.issued_date || p.timestamp || '-';
    
    // Vencimiento
    let expDateStr = p.expiration_date;
    if (!expDateStr && entryDate && entryDate !== '-') {
        try {
            const d = new Date(entryDate.replace(' ', 'T'));
            if (!isNaN(d.getTime())) {
                d.setDate(d.getDate() + dteVal);
                expDateStr = d.toISOString().split('T')[0];
            }
        } catch(e) { expDateStr = null; }
    }
    const vctoStr = expDateStr ? `<strong>${expDateStr}</strong> <span style="font-size:11px;opacity:0.75;">(${dteVal} DTE)</span>` : `${dteVal} DTE`;
    
    // Contratos
    const shortContracts = p.short_put_contracts || p.contracts || 1;
    const longContracts = p.long_call_contracts || p.contracts || 1;
    
    // Precios Underlying
    const entryUnderlying = p.underlying_price_at_entry || p.entry_underlying_price || p.underlying_price || 0;
    const currentUnderlying = p.current_underlying_price || p.underlying_price || entryUnderlying;
    const exitUnderlying = p.exit_underlying_price || p.exit_price || currentUnderlying;
    
    // --- 1. POSICION SHORT (PUT) ---
    const shortTicker = symbol;
    const shortOption = 'PUT (Short)';
    const shortStrike = p.short_put_strike !== undefined ? `$${p.short_put_strike}` : '-';
    const shortVcto = vctoStr;
    const shortContractsStr = `${shortContracts}x (${shortContracts * 100} acc)`;
    
    const shortEntryTime = entryDate;
    const shortEntryUnderlyingStr = entryUnderlying > 0 ? formatUSD(entryUnderlying) : '-';
    const shortPremCollected = p.short_put_premium_collected !== undefined ? p.short_put_premium_collected : 0;
    const shortPremPerShare = shortContracts > 0 ? (shortPremCollected / (shortContracts * 100)) : 0;
    const shortPremStr = `+${formatUSD(shortPremPerShare)} / sh`;
    const shortNetIncomeStr = `+${formatUSD(shortPremCollected)}`;
    
    let shortExitTimeStr = '-';
    let shortExitUnderlyingStr = '-';
    let shortExitPremStr = '-';
    let shortNetCostExitStr = '-';
    let shortPnl = 0;
    let shortDuration = '-';
    
    if (isDecoupled) {
        shortExitTimeStr = p.decouple_date ? `<strong>${p.decouple_date}</strong> <span class="badge-long">Put Recomprado</span>` : 'Recomprado';
        shortExitUnderlyingStr = formatUSD(currentUnderlying);
        const decoupleCost = p.decouple_cost_paid_usd !== undefined ? p.decouple_cost_paid_usd : 0;
        const decouplePremShare = shortContracts > 0 ? (decoupleCost / (shortContracts * 100)) : 0;
        shortExitPremStr = `${formatUSD(decouplePremShare)} / sh`;
        shortNetCostExitStr = formatUSD(decoupleCost);
        shortPnl = shortPremCollected - decoupleCost;
        shortDuration = formatDurationStr(entryDate, p.decouple_date, false, dteVal);
    } else if (isOpen) {
        shortExitTimeStr = '<span class="text-green">🟢 EN CURSO (Abierto)</span>';
        shortExitUnderlyingStr = formatUSD(currentUnderlying);
        const buybackCost = p.short_put_current_buyback_cost !== undefined ? p.short_put_current_buyback_cost : 0;
        const buybackShare = shortContracts > 0 ? (buybackCost / (shortContracts * 100)) : 0;
        shortExitPremStr = `${formatUSD(buybackShare)} / sh <span style="font-size:10px;opacity:0.8;">(Buyback)</span>`;
        shortNetCostExitStr = formatUSD(buybackCost);
        shortPnl = shortPremCollected - buybackCost;
        shortDuration = formatDurationStr(entryDate, null, true, dteVal);
    } else {
        shortExitTimeStr = p.exit_date || p.exit_time || expDateStr || '-';
        shortExitUnderlyingStr = formatUSD(exitUnderlying);
        const exitCost = p.short_put_exit_cost !== undefined ? p.short_put_exit_cost : 0;
        shortExitPremStr = formatUSD(exitCost / (shortContracts * 100));
        shortNetCostExitStr = formatUSD(exitCost);
        shortPnl = shortPremCollected - exitCost;
        shortDuration = formatDurationStr(entryDate, shortExitTimeStr, false, dteVal);
    }
    
    // --- 2. POSICION LONG (CALL) ---
    const longTicker = symbol;
    const longOption = isDecoupled ? 'CALL (Risk-Free)' : 'CALL (Long)';
    const longStrike = p.long_call_strike !== undefined ? `$${p.long_call_strike}` : '-';
    const longVcto = vctoStr;
    const longContractsStr = `${longContracts}x (${longContracts * 100} acc)`;
    
    const longEntryTime = entryDate;
    const longEntryUnderlyingStr = entryUnderlying > 0 ? formatUSD(entryUnderlying) : '-';
    const longPremPaid = p.long_call_premium_paid !== undefined ? p.long_call_premium_paid : 0;
    const longPremPerShare = longContracts > 0 ? (longPremPaid / (longContracts * 100)) : 0;
    const longPremStr = `-${formatUSD(longPremPerShare)} / sh`;
    const longNetCostStr = `-${formatUSD(longPremPaid)}`;
    
    let longExitTimeStr = '-';
    let longExitUnderlyingStr = '-';
    let longExitPremStr = '-';
    let longNetCostExitStr = '-';
    let longPnl = 0;
    let longDuration = '-';
    
    if (isOpen) {
        longExitTimeStr = '<span class="text-green">🟢 EN CURSO (Corriendo)</span>';
        longExitUnderlyingStr = `${formatUSD(currentUnderlying)} <span style="font-size:10px;opacity:0.8;">(Actual)</span>`;
        const callValTot = p.unrealized_pnl_usd !== undefined ? p.unrealized_pnl_usd : 0;
        const callValPerShare = longContracts > 0 ? (callValTot / (longContracts * 100)) : 0;
        longExitPremStr = `${formatUSD(callValPerShare)} / sh <span style="font-size:10px;opacity:0.8;">(Val. Flotante)</span>`;
        longNetCostExitStr = `<span class="text-green">+${formatUSD(callValTot)} (Val. Actual)</span>`;
        longPnl = callValTot - longPremPaid;
        longDuration = formatDurationStr(entryDate, null, true, dteVal);
    } else {
        longExitTimeStr = p.exit_date || p.exit_time || '-';
        longExitUnderlyingStr = formatUSD(exitUnderlying);
        const saleRev = p.long_call_sale_revenue !== undefined ? p.long_call_sale_revenue : (p.exit_cost_usd || 0);
        longExitPremStr = formatUSD(saleRev / (longContracts * 100));
        longNetCostExitStr = `+${formatUSD(saleRev)}`;
        longPnl = saleRev - longPremPaid;
        longDuration = formatDurationStr(entryDate, longExitTimeStr, false, dteVal);
    }
    
    // --- 3. COMBINADO ---
    const combPremNet = shortPremPerShare - longPremPerShare;
    const combNetIncome = shortPremCollected - longPremPaid;
    
    let combStatusStr = '';
    let combExitPx = isOpen ? currentUnderlying : exitUnderlying;
    let combExitPremStr = '';
    let combNetCostExitStr = '';
    let combPnl = 0;
    let combDuration = formatDurationStr(entryDate, isOpen ? null : (p.exit_date || p.exit_time), isOpen, dteVal);
    
    if (isOpen) {
        if (isDecoupled) {
            combStatusStr = '<span class="badge-long">🟢 LONG CALL ABIERTA (Put Desacoplada)</span>';
            const callValTot = p.unrealized_pnl_usd !== undefined ? p.unrealized_pnl_usd : 0;
            const decoupleCost = p.decouple_cost_paid_usd !== undefined ? p.decouple_cost_paid_usd : 0;
            const netFlotante = callValTot - decoupleCost;
            combExitPremStr = `+${formatUSD((callValTot - decoupleCost) / (longContracts * 100))} / sh <span style="font-size:10px;opacity:0.8;">(Neto Flotante)</span>`;
            combNetCostExitStr = `<span class="text-green"><strong>+${formatUSD(netFlotante)}</strong></span> <span style="font-size:10px;opacity:0.8;">(Val. Call - Recompra Put)</span>`;
            combPnl = netFlotante;
        } else {
            combStatusStr = '<span class="badge-short">🟢 SINTÉTICO ACTIVO (Short Put + Long Call)</span>';
            const callValTot = p.unrealized_pnl_usd !== undefined ? p.unrealized_pnl_usd : 0;
            const putBuyback = p.short_put_current_buyback_cost || 0;
            const netFlotante = callValTot - putBuyback;
            combExitPremStr = formatUSD(netFlotante / (longContracts * 100));
            combNetCostExitStr = formatUSD(netFlotante);
            combPnl = netFlotante;
        }
    } else {
        combStatusStr = p.exit_date || p.exit_time ? `Cerrado el ${p.exit_date || p.exit_time}` : 'Cerrado';
        combPnl = p.final_pnl_usd !== undefined ? p.final_pnl_usd : (shortPnl + longPnl);
        combExitPremStr = formatUSD(combPnl / (longContracts * 100));
        combNetCostExitStr = formatUSD(combPnl);
    }

    return `
    <div class="card alpha-card-block" style="margin-bottom:25px;border:1px solid var(--card-border);background:rgba(15,23,42,0.6);border-radius:8px;padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:10px;">
            <div style="font-size:14px;font-weight:bold;color:var(--text-white);">
                <strong>${symbol}</strong> — SINTÉTICO ZERO-COST LEAPS (ID: #${p.id || 'ALPHA'})
            </div>
            <div>
                ${isDecoupled ? '<span class="badge-long">🟢 PUT DESACOPLADO (100% RISK-FREE)</span>' : (isOpen ? '<span class="badge-short">🟡 SINTÉTICO COMPLETO</span>' : '<span style="color:var(--text-muted)">⚪ CERRADO</span>')}
            </div>
        </div>
        <div class="table-responsive">
            <table class="data-table alpha-matrix-table">
                <thead>
                    <tr>
                        <th style="width:28%;color:var(--ice-blue);">MÉTRICA AUDITADA</th>
                        <th style="width:24%;color:var(--accent-blue);background:rgba(0,210,255,0.08);border-left:1px solid rgba(0,210,255,0.2);">POSICIÓN SHORT</th>
                        <th style="width:24%;color:var(--accent-green);background:rgba(0,230,118,0.08);border-left:1px solid rgba(0,230,118,0.2);">POSICIÓN LONG</th>
                        <th style="width:24%;color:#F59E0B;background:rgba(245,158,11,0.08);border-left:1px solid rgba(245,158,11,0.2);">COMBINADO</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 1. ESPECIFICACIÓN -->
                    <tr class="section-divider"><td colspan="4">1. ESPECIFICACIÓN Y CONTRATOS</td></tr>
                    <tr>
                        <td><strong>ticker</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${shortTicker}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${longTicker}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>opcion</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><span class="badge-short">${shortOption}</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><span class="badge-long">${longOption}</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>strike</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortStrike}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longStrike}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>vencimiento</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortVcto}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longVcto}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>cantidad de contratos</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${shortContractsStr}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${longContractsStr}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>

                    <!-- 2. APERTURA -->
                    <tr class="section-divider"><td colspan="4">2. CONDICIONES DE APERTURA</td></tr>
                    <tr>
                        <td><strong>fecha y hora de apertura de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortEntryTime}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longEntryTime}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>precio del underlying a la apertura</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortEntryUnderlyingStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longEntryUnderlyingStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">-</td>
                    </tr>
                    <tr>
                        <td><strong>prima en la apertura</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortPremStr} <span style="font-size:10px;color:var(--accent-blue);">(Recibida)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longPremStr} <span style="font-size:10px;color:var(--primary-red);">(Pagada)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${formatUSD(combPremNet)}</strong> <span style="font-size:10.5px;opacity:0.8;">(en apertura: prima recibida - prima pagada)</span></td>
                    </tr>
                    <tr>
                        <td><strong>neto entrada</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--accent-green);"><strong>${shortNetIncomeStr}</strong> <span style="font-size:10px;">(Cobrado)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--primary-red);"><strong>${longNetCostStr}</strong> <span style="font-size:10px;">(Pagado)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--accent-green);"><strong>${formatUSD(combNetIncome)}</strong> <span style="font-size:10.5px;opacity:0.8;">(monto neto apertura: neto cobrado - neto pagado)</span></td>
                    </tr>

                    <!-- 3. CIERRE / ESTATUS -->
                    <tr class="section-divider"><td colspan="4">3. CIERRE Y ESTATUS OPERATIVO</td></tr>
                    <tr>
                        <td><strong>fecha y hora de cierre de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortExitTimeStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longExitTimeStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${combStatusStr} <br/><span style="font-size:10px;opacity:0.75;">(fecha cierre total o estatus actual)</span></td>
                    </tr>
                    <tr>
                        <td><strong>precio del underlying al cierre</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortExitUnderlyingStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longExitUnderlyingStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${formatUSD(combExitPx)}</strong> <br/><span style="font-size:10px;opacity:0.75;">(al cierre de toda la operación o precio actual)</span></td>
                    </tr>
                    <tr>
                        <td><strong>prima al cerrar / valor actual</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortExitPremStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longExitPremStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${combExitPremStr}</strong> <br/><span style="font-size:10px;opacity:0.75;">(cierre: neto de primas o neto primas + valor actual long)</span></td>
                    </tr>
                    <tr>
                        <td><strong>neto para cerrar / valor actual</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortNetCostExitStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longNetCostExitStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${combNetCostExitStr} <br/><span style="font-size:10px;opacity:0.75;">(cierre: monto neto cierre o monto al cierre + valor actual long)</span></td>
                    </tr>

                    <!-- 4. BALANCE Y TIEMPO -->
                    <tr class="section-divider"><td colspan="4">4. BALANCE FINAL Y TIEMPO DE OPERACIÓN</td></tr>
                    <tr style="background:rgba(255,255,255,0.03);font-size:13px;">
                        <td><strong>neto total de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="${colorClass(shortPnl)}"><strong>${sign(shortPnl)}${formatUSD(shortPnl)}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="${colorClass(longPnl)}"><strong>${sign(longPnl)}${formatUSD(longPnl)}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="${colorClass(combPnl)}"><strong style="font-size:15px;">${sign(combPnl)}${formatUSD(combPnl)}</strong> <br/><span style="font-size:10px;opacity:0.75;">(neto total de la operación combinada)</span></td>
                    </tr>
                    <tr>
                        <td><strong>tiempo neto de la operacion</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortDuration}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longDuration}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${combDuration}</strong> <br/><span style="font-size:10px;opacity:0.75;">(tiempo desde apertura hasta cierre del último)</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`;
}

function renderBullMarketMatrixTable(p, isOpen = true) {
    const symbol = p.symbol || 'SPY';
    const entryDate = p.entry_date || '-';
    const entryUnderlying = p.underlying_price_at_entry || 0;
    const currentUnderlying = p.current_underlying_price || entryUnderlying;
    const exitUnderlying = p.exit_underlying_price || currentUnderlying;
    
    // Contratos
    const longContracts = p.long_call_contracts || p.contracts || 1;
    const shortContracts = p.short_call_contracts || p.contracts || 1;
    
    // --- 1. PATA LONG (CALL ITM Δ 0.80) ---
    const longStrike = p.long_call_strike !== undefined ? `$${p.long_call_strike}` : '-';
    const longDte = p.long_call_initial_dte || 75;
    const longExp = p.long_call_expiration || '-';
    const longDelta = p.long_call_delta_entry ? `Δ ${p.long_call_delta_entry}` : 'Δ ~0.80';
    const longContractsStr = `${longContracts}x (${longContracts * 100} acc sintéticas)`;
    
    const longPremPaid = p.long_call_premium_paid || 0;
    const longPremShare = longContracts > 0 ? (longPremPaid / (longContracts * 100)) : 0;
    const longCurrentVal = p.long_call_current_value_usd || longPremPaid;
    const longUnrealized = p.long_call_unrealized_pnl_usd !== undefined ? p.long_call_unrealized_pnl_usd : (longCurrentVal - longPremPaid);
    const longDuration = formatDurationStr(entryDate, isOpen ? null : p.exit_date, isOpen, longDte);
    
    // --- 2. PATA SHORT (CALL SEMANAL Δ 0.20) ---
    const shortStrike = p.short_call_strike !== undefined ? `$${p.short_call_strike}` : '-';
    const shortDte = p.short_call_dte !== undefined ? p.short_call_dte : 7;
    const shortExp = p.short_call_expiration || '-';
    const shortDelta = p.short_call_delta_entry ? `Δ ${p.short_call_delta_entry}` : 'Δ ~0.20';
    const shortContractsStr = `${shortContracts}x (${shortContracts * 100} acc cubiertas)`;
    
    const shortPremCollected = p.short_call_premium_collected || 0;
    const shortPremShare = shortContracts > 0 ? (shortPremCollected / (shortContracts * 100)) : 0;
    const shortBuybackCost = p.short_call_current_buyback_cost || 0;
    const shortCurrentGain = shortPremCollected - shortBuybackCost;
    const thetaAccum = p.accumulated_theta_income_usd || 0;
    const rollsCount = p.rolls_completed_count || 0;
    const shortTotalGain = thetaAccum + (isOpen ? shortCurrentGain : 0);
    
    // --- 3. COMBINADO (SPREAD PMCC) ---
    const netDebit = p.net_debit_paid_usd !== undefined ? p.net_debit_paid_usd : (longPremPaid - shortPremCollected);
    const netDebitShare = longContracts > 0 ? (netDebit / (longContracts * 100)) : 0;
    const breakEven = p.break_even_price || (p.long_call_strike + netDebit / 100.0);
    const combTotalPnl = p.total_unrealized_pnl_usd !== undefined ? p.total_unrealized_pnl_usd : (longUnrealized + shortTotalGain);
    
    // Rows
    let longExitTimeStr = isOpen ? '<span class="text-green">🟢 ACTIVA (En curso)</span>' : (p.exit_date || '-');
    let shortExitTimeStr = isOpen ? `<span class="badge-short">🔄 ROLLEO SEMANAL #${rollsCount}</span>` : (p.exit_date || '-');
    let combStatusStr = isOpen ? `<span class="badge-long">🟢 PMCC ACTIVO (Semana #${rollsCount + 1})</span>` : '<span style="color:var(--text-muted)">⚪ CERRADO</span>';
    
    let longExitPremStr = isOpen ? `+${formatUSD(longCurrentVal / (longContracts * 100))} / sh <span style="font-size:10px;opacity:0.8;">(Val. Flotante)</span>` : formatUSD(longCurrentVal / (longContracts * 100));
    let shortExitPremStr = isOpen ? `-${formatUSD(shortBuybackCost / (shortContracts * 100))} / sh <span style="font-size:10px;opacity:0.8;">(Recompra Ciclo)</span>` : formatUSD(shortBuybackCost / (shortContracts * 100));
    let combExitPremStr = isOpen ? `Break-Even: <strong>$${breakEven.toFixed(2)}</strong>` : '-';
    
    let longNetCostExitStr = isOpen ? `<span class="text-green">+${formatUSD(longCurrentVal)}</span> <span style="font-size:10px;opacity:0.8;">(Valor Liquidación)</span>` : formatUSD(longCurrentVal);
    let shortNetCostExitStr = isOpen ? `<span class="text-red">-${formatUSD(shortBuybackCost)}</span> <span style="font-size:10px;opacity:0.8;">(Recompra Actual)</span>` : formatUSD(shortBuybackCost);
    let combNetCostExitStr = isOpen ? `<span class="text-green"><strong>+${formatUSD(thetaAccum)}</strong></span> <span style="font-size:10px;opacity:0.8;">(Theta Rolleos Acumulados)</span>` : '-';

    return `
    <div class="card alpha-card-block" style="margin-bottom:25px;border:1px solid var(--card-border);background:rgba(15,23,42,0.6);border-radius:8px;padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:10px;">
            <div style="font-size:14px;font-weight:bold;color:var(--text-white);">
                <strong>${symbol}</strong> — POOR MAN’S COVERED CALL (ID: #${p.id || 'PMCC'})
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
                <span class="badge-long">🎯 DELTA LONG: ${longDelta}</span>
                <span class="badge-short">⚡ DELTA SHORT: ${shortDelta}</span>
                ${isOpen ? '<span class="badge-long">🟢 ACTIVO Y ROLLEANDO</span>' : '<span style="color:var(--text-muted)">⚪ CERRADO</span>'}
            </div>
        </div>
        <div class="table-responsive">
            <table class="data-table alpha-matrix-table">
                <thead>
                    <tr>
                        <th style="width:28%;color:var(--ice-blue);">MÉTRICA AUDITADA</th>
                        <th style="width:24%;color:var(--accent-green);background:rgba(0,230,118,0.08);border-left:1px solid rgba(0,230,118,0.2);">PATA LONG (CALL ITM Δ 0.80)</th>
                        <th style="width:24%;color:var(--accent-blue);background:rgba(0,210,255,0.08);border-left:1px solid rgba(0,210,255,0.2);">PATA SHORT (CALL SEMANAL Δ 0.20)</th>
                        <th style="width:24%;color:#F59E0B;background:rgba(245,158,11,0.08);border-left:1px solid rgba(245,158,11,0.2);">COMBINADO (SPREAD PMCC)</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 1. ESPECIFICACIÓN -->
                    <tr class="section-divider"><td colspan="4">1. ESPECIFICACIÓN Y CONTRATOS</td></tr>
                    <tr>
                        <td><strong>ticker</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${symbol}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${symbol}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);"><strong>${symbol} (PMCC)</strong></td>
                    </tr>
                    <tr>
                        <td><strong>opcion</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><span class="badge-long">CALL ITM (Colateral Sintético)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><span class="badge-short">CALL OTM (Extracción Semanal)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><span class="badge-long">DIAGONAL SPREAD ALCISTA</span></td>
                    </tr>
                    <tr>
                        <td><strong>strike</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longStrike} <span style="font-size:11px;opacity:0.8;">(${longDelta})</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortStrike} <span style="font-size:11px;opacity:0.8;">(${shortDelta})</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">K-Long: ${longStrike} / K-Short: ${shortStrike}</td>
                    </tr>
                    <tr>
                        <td><strong>vencimiento</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${longExp}</strong> <span style="font-size:11px;opacity:0.75;">(${longDte} DTE)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${shortExp}</strong> <span style="font-size:11px;opacity:0.75;">(${shortDte} DTE)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">Diagonal (${shortDte}d vs ${longDte}d)</td>
                    </tr>
                    <tr>
                        <td><strong>cantidad de contratos</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${longContractsStr}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${shortContractsStr}</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--text-muted);">${longContracts} spread(s) PMCC</td>
                    </tr>

                    <!-- 2. APERTURA -->
                    <tr class="section-divider"><td colspan="4">2. CONDICIONES DE APERTURA</td></tr>
                    <tr>
                        <td><strong>fecha y hora de apertura de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${entryDate}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${entryDate} <span style="font-size:10px;opacity:0.75;">(Ciclo #${rollsCount + 1})</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${entryDate}</td>
                    </tr>
                    <tr>
                        <td><strong>precio del underlying a la apertura</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(entryUnderlying)}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(entryUnderlying)}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(entryUnderlying)}</td>
                    </tr>
                    <tr>
                        <td><strong>prima en la apertura</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(longPremShare)} / sh <span style="font-size:10px;color:var(--primary-red);">(Pagada)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(shortPremShare)} / sh <span style="font-size:10px;color:var(--accent-blue);">(Recibida Ciclo)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${formatUSD(netDebitShare)} / sh</strong> <span style="font-size:10.5px;opacity:0.8;">(Débito neto pagado por acción)</span></td>
                    </tr>
                    <tr>
                        <td><strong>neto entrada</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--primary-red);"><strong>-${formatUSD(longPremPaid)}</strong> <span style="font-size:10px;">(Costo Colateral Long)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--accent-green);"><strong>+${formatUSD(shortPremCollected)}</strong> <span style="font-size:10px;">(Crédito Inicial Cobrado)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);color:var(--ice-blue);"><strong>-${formatUSD(netDebit)}</strong> <span style="font-size:10.5px;opacity:0.8;">(Inversión Neta Inicial PMCC)</span></td>
                    </tr>

                    <!-- 3. CIERRE / ESTATUS -->
                    <tr class="section-divider"><td colspan="4">3. CIERRE Y ESTATUS OPERATIVO</td></tr>
                    <tr>
                        <td><strong>fecha y hora de cierre de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longExitTimeStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortExitTimeStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${combStatusStr}</td>
                    </tr>
                    <tr>
                        <td><strong>precio del underlying al cierre</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(currentUnderlying)} <span style="font-size:10px;opacity:0.75;">(Spot)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${formatUSD(currentUnderlying)} <span style="font-size:10px;opacity:0.75;">(Spot)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${formatUSD(currentUnderlying)}</strong> <span style="font-size:10px;opacity:0.75;">(Spot)</span></td>
                    </tr>
                    <tr>
                        <td><strong>prima al cerrar / valor actual</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longExitPremStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortExitPremStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${combExitPremStr}</td>
                    </tr>
                    <tr>
                        <td><strong>neto para cerrar / valor actual</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longNetCostExitStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${shortNetCostExitStr}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${combNetCostExitStr}</td>
                    </tr>

                    <!-- 4. BALANCE Y TIEMPO -->
                    <tr class="section-divider"><td colspan="4">4. BALANCE FINAL Y TIEMPO DE OPERACIÓN</td></tr>
                    <tr style="background:rgba(255,255,255,0.03);font-size:13px;">
                        <td><strong>neto total de la operación</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="${colorClass(longUnrealized)}"><strong>${sign(longUnrealized)}${formatUSD(longUnrealized)}</strong> <br/><span style="font-size:10px;opacity:0.75;">(Apreciación Long Sintética)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="text-green"><strong>+${formatUSD(shortTotalGain)}</strong> <br/><span style="font-size:10px;opacity:0.75;">(Theta Rolleos + Ciclo Actual)</span></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);" class="${colorClass(combTotalPnl)}"><strong style="font-size:15px;">${sign(combTotalPnl)}${formatUSD(combTotalPnl)}</strong> <br/><span style="font-size:10px;opacity:0.75;">(Neto Total Acumulado PMCC)</span></td>
                    </tr>
                    <tr>
                        <td><strong>tiempo neto de la operacion</strong></td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">${longDuration}</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);">Ciclo #${rollsCount + 1} (${shortDte} DTE restantes)</td>
                        <td style="border-left:1px solid rgba(255,255,255,0.05);"><strong>${longDuration}</strong> <br/><span style="font-size:10px;opacity:0.75;">(${rollsCount} rolleo(s) completados)</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`;
}
