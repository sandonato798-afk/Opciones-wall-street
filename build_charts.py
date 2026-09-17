import matplotlib.pyplot as plt
import numpy as np
import os

# Create charts output directory
os.makedirs("pdf_assets", exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

# ---------------------------------------------------------
# CHART 1: Portfolio 5-Layer Allocation (Donut Chart)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=300)
labels = [
    '1. The Wheel (35% - $35k)',
    '2. Credit Spreads (20% - $20k)',
    '3. Alpha Trade (20% - $20k)',
    '4. Oportunista 1DTE (15% - $15k)',
    '5. Day Trading (10% - $10k)'
]
sizes = [35, 20, 20, 15, 10]
colors = ['#272C32', '#567283', '#ED3D32', '#FBBF24', '#10B981']
explode = (0.03, 0.03, 0.05, 0.03, 0.03)

wedges, texts, autotexts = ax.pie(
    sizes, explode=explode, labels=labels, autopct='%1.0f%%',
    startangle=140, colors=colors, pctdistance=0.75,
    textprops=dict(color="#1E293B", weight="bold", fontsize=9)
)

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(10)

centre_circle = plt.Circle((0,0), 0.52, fc='white')
fig.gca().add_artist(centre_circle)

ax.set_title("Matriz de Asignación de Margen ($100,000 USD)", fontsize=12, fontweight='bold', pad=15, color='#1D2226')
plt.tight_layout()
plt.savefig("pdf_assets/chart_allocation.png", bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# CHART 2: Reinvestment Flow Breakdown (Bar Chart)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
categories = ['SGOV (Tesorería 5.2%)', 'SPY/QQQ (Acciones)', 'Alpha Trade (Calls Limpios)']
percentages = [50, 30, 20]
monthly_usd = [1000, 600, 400]
bar_colors = ['#567283', '#10B981', '#ED3D32']

bars = ax.barh(categories, percentages, color=bar_colors, height=0.55, edgecolor='#1E293B', linewidth=0.5)

for bar, pct, usd in zip(bars, percentages, monthly_usd):
    ax.text(pct + 1.5, bar.get_y() + bar.get_height()/2, f"{pct}% (${usd} USD/mes)", 
            va='center', ha='left', fontweight='bold', fontsize=9.5, color='#1D2226')

ax.set_xlim(0, 65)
ax.set_xlabel("Porcentaje de Primas Netas Re-invertidas (%)", fontsize=10, fontweight='bold', color='#1D2226')
ax.set_title("Motor de Reinversión Híbrida (50% / 30% / 20%)", fontsize=12, fontweight='bold', pad=12, color='#1D2226')
ax.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig("pdf_assets/chart_reinvestment.png", bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# CHART 3: 3-Year Equity Projection (Line Chart)
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.0), dpi=300)
months = np.arange(0, 37)

# Curves
nav_sgov = 100000 * (1 + 0.312/12) ** months
nav_spy = 100000 * (1 + 0.368/12) ** months
nav_alpha = 100000 * (1 + 0.445/12) ** months
nav_hibrido = 100000 * (1 + 0.384/12) ** months

ax.plot(months, nav_sgov, label='100% SGOV Tesorería (ROI +31.2%/yr)', color='#567283', linewidth=2, linestyle='--')
ax.plot(months, nav_spy, label='100% Acumulación SPY/QQQ (ROI +36.8%/yr)', color='#10B981', linewidth=2, linestyle='-.')
ax.plot(months, nav_alpha, label='100% Alpha Trade Calls (ROI +44.5%/yr)', color='#9333EA', linewidth=2, linestyle=':')
ax.plot(months, nav_hibrido, label='HÍBRIDO OPTIMIZADO (ROI +38.4%/yr - Max Sharpe)', color='#ED3D32', linewidth=3.2)

ax.set_title("Proyección de Crecimiento del Capital a 36 Meses ($100k Inicial)", fontsize=12, fontweight='bold', pad=12, color='#1D2226')
ax.set_xlabel("Meses de Operación", fontsize=10, fontweight='bold', color='#1D2226')
ax.set_ylabel("NAV Total del Portafolio (USD)", fontsize=10, fontweight='bold', color='#1D2226')
ax.yaxis.set_major_formatter('${x:,.0f}')
ax.set_xticks([0, 6, 12, 18, 24, 30, 36])
ax.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='white', framealpha=0.9)
ax.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig("pdf_assets/chart_equity_growth.png", bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# CHART 4: Black Swan Crash Simulation (Area / Line Chart)
# ---------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 4.5), sharex=True, dpi=300, gridspec_kw={'height_ratios': [2, 1]})

days = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
spy_price = np.array([550, 528, 498, 484, 495, 510, 525, 538, 545, 548, 552]) # -12% crash then recovery
margin_util = np.array([10.5, 18.2, 35.4, 48.2, 42.0, 31.5, 22.0, 16.5, 13.0, 11.5, 10.8]) # Margin %
iv_index = np.array([14, 28, 45, 42, 35, 28, 22, 18, 16, 15, 14]) # IV %

# Plot SPY vs Margin Util
ax1.plot(days, spy_price, color='#ED3D32', linewidth=2.5, marker='o', label='Precio SPY (Crash -12%)')
ax1.set_ylabel("Precio SPY ($)", color='#ED3D32', fontweight='bold', fontsize=9.5)
ax1.tick_params(axis='y', labelcolor='#ED3D32')
ax1.set_title("Respuesta del Sistema durante un Cisne Negro (Flash Crash -12%)", fontsize=11, fontweight='bold', color='#1D2226')
ax1.grid(True, linestyle='--', alpha=0.4)

ax1_twin = ax1.twinx()
ax1_twin.plot(days, margin_util, color='#567283', linewidth=2.2, linestyle='--', marker='s', label='Utilización de Margen (%)')
ax1_twin.axhline(95, color='red', linestyle=':', label='Límite Margin Call (95%)')
ax1_twin.axhline(65, color='orange', linestyle=':', label='Techo Máx Operativo (65%)')
ax1_twin.set_ylabel("Utilización Margen (%)", color='#567283', fontweight='bold', fontsize=9.5)
ax1_twin.tick_params(axis='y', labelcolor='#567283')
ax1_twin.set_ylim(0, 105)

# Bottom subplot: Volatility (IV Spike) triggering Capa 4
ax2.bar(days, iv_index, color='#FBBF24', alpha=0.75, width=0.5, edgecolor='#1E293B', label='Índice IV Volatilidad Implícita')
ax2.axhline(30, color='red', linestyle='--', label='Gatillo RSI<30 / IV Spike')
ax2.set_ylabel("IV (%)", fontweight='bold', fontsize=9.5, color='#1D2226')
ax2.set_xlabel("Días del Evento de Cisne Negro", fontweight='bold', fontsize=9.5, color='#1D2226')
ax2.grid(True, linestyle='--', alpha=0.4)
ax2.legend(loc='upper right', fontsize=8, frameon=True)

plt.tight_layout()
plt.savefig("pdf_assets/chart_black_swan.png", bbox_inches='tight')
plt.close()

print("All 4 charts successfully generated in pdf_assets/")
