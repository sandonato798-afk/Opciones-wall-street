// js/formatters.js - Utilidades universales de formateo y manipulacion de DOM

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

function formatDurationStr(entryTime, exitTime, isOpen, fallbackDte = null) {
    if (!entryTime || entryTime === '-') return fallbackDte ? `${fallbackDte}d` : '-';
    try {
        const t1 = new Date(entryTime.replace(' ', 'T')).getTime();
        let t2 = isOpen ? Date.now() : (exitTime && exitTime !== '-' ? new Date(exitTime.replace(' ', 'T')).getTime() : null);
        if (!isOpen && (!t2 || t2 === t1)) {
            if (fallbackDte) return `${fallbackDte}d (Ciclo)`;
        }
        if (!t2) t2 = Date.now();
        if (isNaN(t1) || isNaN(t2) || t2 < t1) return fallbackDte ? `${fallbackDte}d` : '-';
        const totalMins = Math.floor((t2 - t1) / 60000);
        if (totalMins < 60) return `${totalMins} min`;
        const hours = Math.floor(totalMins / 60);
        const mins = totalMins % 60;
        if (hours < 24) return `${hours}h ${mins}m`;
        const days = Math.floor(hours / 24);
        const remHours = hours % 24;
        return `${days}d ${remHours}h`;
    } catch(e) {
        return fallbackDte ? `${fallbackDte}d` : '-';
    }
}
