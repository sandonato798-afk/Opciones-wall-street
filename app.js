// app.js - Orquestador Principal del Dashboard
// Inicializa la navegación por solapas y el ciclo global de actualización periódica

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
        loadDaytrade(),
        loadBullMarket()
    ]);
}
