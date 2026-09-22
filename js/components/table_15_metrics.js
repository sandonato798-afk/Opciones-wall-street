// js/components/table_15_metrics.js - Renderizador universal de la fila de 15 métricas auditadas
// Utilizado en La Rueda, RSI Oportunista y Daytrading

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
    
    // 4. Vencimiento: Fecha exacta (YYYY-MM-DD)
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
    
    // 5. Cantidad de Contratos
    const contractsNum = p.contracts || p.long_call_contracts || p.short_put_contracts || 1;
    const contracts = isDecoupled ? `${contractsNum}x Long Call` : `${contractsNum}x`;
    
    // 6. Fecha y Hora de Apertura: entryTime
    
    // 7. Precio Underlying Apertura
    const entryUnderlying = p.underlying_price_at_entry || p.entry_underlying_price || p.underlying_price || p.etf_price || p.entry_price || 0;
    const entryUnderlyingStr = entryUnderlying > 0 ? formatUSD(entryUnderlying) : '-';
    
    // 8. Prima Recibida Apertura & 9. Neto Cobrado Entrada
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
    
    // 10. Fecha y Hora de Cierre
    let exitTimeStr = '-';
    if (isOpen) {
        if (isDecoupled && p.decouple_date) {
            exitTimeStr = `<span class="text-green">🟢 EN CURSO</span><br/><span style="font-size:10px;opacity:0.8;">Desacople Put: ${p.decouple_date}</span>`;
        } else {
            exitTimeStr = '<span class="text-green">🟢 EN CURSO</span>';
        }
    } else {
        exitTimeStr = p.exit_time || p.exit_date || p.decouple_date || (p.timestamp && p.timestamp !== entryTime ? p.timestamp : '-');
        if (exitTimeStr === '-' && expDateStr) {
            exitTimeStr = expDateStr; // Cierre por expiración natural
        }
    }
    
    // 11. Precio Underlying Cierre
    let exitUnderlying = 0;
    if (isOpen) {
        exitUnderlying = p.current_underlying_price || p.underlying_price || p.etf_price || 0;
    } else {
        exitUnderlying = p.exit_underlying_price || p.exit_price || p.underlying_price || p.etf_price || 0;
    }
    const exitUnderlyingStr = exitUnderlying > 0 ? formatUSD(exitUnderlying) : '-';
    
    // 12. Prima Pagada al Cerrar
    let exitPremiumStr = '-';
    if (isOpen) {
        if (p.unrealized_pnl_usd !== undefined && contractsNum > 0) {
            const callValPerShare = p.unrealized_pnl_usd / (contractsNum * 100);
            exitPremiumStr = `${formatUSD(callValPerShare)} / sh`;
        } else if (p.short_put_current_buyback_cost !== undefined && contractsNum > 0) {
            exitPremiumStr = formatUSD(p.short_put_current_buyback_cost / (contractsNum * 100));
        } else {
            const curPrem = p.current_premium !== undefined ? p.current_premium : (p.curr_prem_per_share || 0);
            exitPremiumStr = curPrem > 0 ? formatUSD(curPrem) : '$0.00';
        }
    } else {
        if (p.exit_premium !== undefined) {
            exitPremiumStr = formatUSD(p.exit_premium);
        } else if (p.exit_cost_usd !== undefined && contractsNum > 0) {
            exitPremiumStr = formatUSD(p.exit_cost_usd / (contractsNum * 100));
        } else if (p.exit_reason === 'EXPIRED_OTM_WORTHLESS') {
            exitPremiumStr = '$0.00';
        } else if (p.pnl_usd !== undefined && netIncomeEntry > 0 && contractsNum > 0) {
            const cost = Math.max(0, netIncomeEntry - p.pnl_usd);
            exitPremiumStr = formatUSD(cost / (contractsNum * 100));
        } else {
            exitPremiumStr = '$0.00';
        }
    }
    
    // 13. Neto Pagado para Cerrar
    let netCostExitStr = '-';
    if (isOpen) {
        if (p.short_put_current_buyback_cost !== undefined) {
            netCostExitStr = p.short_put_current_buyback_cost > 0 ? `${formatUSD(p.short_put_current_buyback_cost)} (Buyback Put)` : '$0.00 (Libre Riesgo)';
        } else {
            const curPrem = p.current_premium !== undefined ? p.current_premium : (p.curr_prem_per_share || 0);
            const buybackTot = curPrem * 100 * contractsNum;
            netCostExitStr = buybackTot > 0 ? `${formatUSD(buybackTot)}` : '$0.00';
        }
    } else {
        if (p.exit_cost_usd !== undefined) {
            netCostExitStr = formatUSD(p.exit_cost_usd);
        } else if (p.decouple_cost_paid_usd !== undefined) {
            netCostExitStr = formatUSD(p.decouple_cost_paid_usd);
        } else if (p.exit_reason === 'EXPIRED_OTM_WORTHLESS') {
            netCostExitStr = '$0.00';
        } else if (p.pnl_usd !== undefined && netIncomeEntry > 0) {
            const cost = Math.max(0, netIncomeEntry - p.pnl_usd);
            netCostExitStr = formatUSD(cost);
        } else {
            netCostExitStr = '$0.00';
        }
    }
    
    // 14. Neto Total de la Operación
    let netPnl = 0;
    if (p.final_pnl_usd !== undefined) netPnl = p.final_pnl_usd;
    else if (p.unrealized_pnl_usd !== undefined) netPnl = p.unrealized_pnl_usd;
    else if (p.pnl_usd !== undefined) netPnl = p.pnl_usd;
    else if (p.realized_pnl_usd !== undefined) netPnl = p.realized_pnl_usd;
    else if (!isOpen && p.premium_collected_usd) netPnl = p.premium_collected_usd;
    
    const pnlNote = isDecoupled ? ' (100% Risk-Free)' : '';
    
    // 15. Tiempo Neto de la Operación
    const netDuration = formatDurationStr(entryTime, p.exit_time || p.exit_date || p.decouple_date, isOpen, dteVal);
    
    return `<tr>
        <td><strong>${ticker}</strong></td>
        <td><span style="color:var(--accent-blue);font-weight:600;">${optionType}</span></td>
        <td>${strike}</td>
        <td>${dteStr}</td>
        <td><strong>${contracts}</strong></td>
        <td>${entryTime}</td>
        <td>${entryUnderlyingStr}</td>
        <td>${entryPremiumStr}</td>
        <td class="text-green">${netIncomeEntryStr}</td>
        <td>${exitTimeStr}</td>
        <td>${exitUnderlyingStr}</td>
        <td>${exitPremiumStr}</td>
        <td>${netCostExitStr}</td>
        <td class="${colorClass(netPnl)}"><strong>${sign(netPnl)}${formatUSD(netPnl)}${pnlNote}</strong></td>
        <td>${netDuration}</td>
    </tr>`;
}
