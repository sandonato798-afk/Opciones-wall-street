import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_proposal_docx(output_path):
    doc = docx.Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styles & Colors
    PRIMARY_COLOR = RGBColor(15, 32, 67)    # Navy Blue #0F2043
    SECONDARY_COLOR = RGBColor(0, 150, 136) # Teal #009688
    TEXT_COLOR = RGBColor(40, 40, 40)
    LIGHT_BG = "F4F6F9"

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("SISTEMA DE TRADING DE OPCIONES D+ARQ")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Propuesta Institucional de Arquitectura Multiclima (5 Capas + Portfolio Margin)")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(14)
    run_sub.font.italic = True
    run_sub.font.color.rgb = SECONDARY_COLOR

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run("Capital Base: $1.000.000 USD | Entorno: IBKR Portfolio Margin | Despliegue: Docker Ubuntu VM")
    r_meta.font.name = 'Arial'
    r_meta.font.size = Pt(10)
    r_meta.font.color.rgb = RGBColor(120, 120, 120)

    doc.add_paragraph() # Spacer

    # Helper function for section headings
    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = PRIMARY_COLOR
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = SECONDARY_COLOR
        return h

    def add_body(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = 'Arial'
            rb.font.size = Pt(11)
            rb.font.bold = True
            rb.font.color.rgb = PRIMARY_COLOR
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(11)
        r.font.color.rgb = TEXT_COLOR
        return p

    # --- SECTION 1 ---
    add_heading_1("1. Resumen Ejecutivo y Filosofía del Sistema")
    add_body("El Sistema de Opciones D+ARQ está diseñado para gestionar un portafolio institucional de $1.000.000 USD maximizando el retorno ajustado por riesgo (Sharpe Ratio) mediante un enfoque de Diversificación por Régimen de Mercado (Multi-Regime Trading).")
    add_body("El 100% del capital líquido se asigna a un Pool Unificado de Colateral Intocable (Treasuries + Renta Variable + Oro) que respalda las operaciones bajo Portfolio Margin de IBKR, permitiendo que 5 capas de opciones operen simultáneamente sobre el margen sin descapitalizar la cuenta.")

    # --- SECTION 2 ---
    add_heading_1("2. Estructura del Portafolio de Colateral (100% NAV)")
    add_body("El colateral base es intocable: no se venden ni operan opciones en contra de estas tenencias. Todos los dividendos generados se reinvierten automáticamente de forma sistemática.")

    # Table for Collateral
    table = doc.add_table(rows=5, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["Activo / Instrumento", "% NAV", "Asignación ($)", "Descripción y Criterio"]
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "0F2043")
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.name = 'Arial'
        p.runs[0].font.size = Pt(10)

    collateral_data = [
        ("US Treasury Notes (Directos)", "60%", "$600,000", "6 bonos escalonados a 10% c/u (12/2027 a 12/2032). Precio < Par (<100), Yield ~5.0% APY."),
        ("VOO (Vanguard S&P 500 ETF)", "20%", "$200,000", "Exposición núcleo al S&P 500 sin opciones en contra."),
        ("QQQ (Invesco Nasdaq 100 ETF)", "15%", "$150,000", "Exposición al sector tecnológico MegaCap."),
        ("GLD (SPDR Gold Shares)", "5%", "$50,000", "Cobertura contra inflación y devaluación del USD.")
    ]

    for row_idx, data in enumerate(collateral_data, start=1):
        row_cells = table.rows[row_idx].cells
        for col_idx, text in enumerate(data):
            row_cells[col_idx].text = text
            p = row_cells[col_idx].paragraphs[0]
            p.runs[0].font.name = 'Arial'
            p.runs[0].font.size = Pt(9.5)
            if row_idx % 2 == 0:
                set_cell_background(row_cells[col_idx], LIGHT_BG)

    doc.add_paragraph() # Spacer

    # --- SECTION 3 ---
    add_heading_1("3. Especificación Pormenorizada de las 5 Capas de Trading")

    # Layer 1
    add_heading_2("Capa 1: La Rueda & Reinversión Compuesta (Motor de Flujo Base)")
    add_body("Mercado Lateral, Consolidación o Alcista Moderado.", "Régimen de Mercado: ")
    add_body("Venta de Cash-Secured Puts a 30-45 DTE en SPY, QQQ e IWM con Delta Δ 0.20 (~3.5% OTM).", "Estrategia: ")
    add_body("Cierre anticipado al capturar el 80% de la prima. Si se asignan acciones, se venden Covered Calls a 14 DTE Δ 0.30.", "Gestión de Salida: ")
    add_body("El 100% de las primas netas se reinvierten automáticamente en comprar más unidades de VOO/QQQ.", "Reinversión: ")

    # Layer 2
    add_heading_2("Capa 2: Alpha Trade (Sintéticos LEAPS + Desacople Automático)")
    add_body("Tendencia Alcista Macro de Mediano/Largo Plazo (S&P 500 / QQQ > SMA-200).", "Régimen de Mercado: ")
    add_body("Combo atómico BAG (2 Short Puts OTM + 2 Long Calls ITM) a 60-180 DTE a costo cero.", "Estrategia: ")
    add_body("Al acumular utilidades de La Rueda, el bot recompra las 2 Short Puts mediante orden BUY LIMIT. Las 2 Long Calls quedan 100% Risk-Free corriendo gratis con potencial alcista ilimitado.", "Mecanismo de Desacople: ")

    # Layer 3
    add_heading_2("Capa 3: RSI Oportunista (Caza-Rebotes en Pánico / VIX High)")
    add_body("Pánico Intradía / Disparo de Volatilidad Implícita (Intraday RSI < 25 y Precio < Cierre Previo).", "Régimen de Mercado: ")
    add_body("Venta de Short Puts muy OTM a 0-1 DTE sobre SPY, QQQ, DIA para capturar primas infladas por el VIX.", "Estrategia: ")
    add_body("Take Profit al 95% o RSI > 70. Time Stop de cierre obligatorio a las 15:55 EST.", "Gestión de Salida: ")

    # Layer 4
    add_heading_2("Capa 4: Daytrading Momentum (Impulso Intradía)")
    add_body("Ruptura de Rango de Apertura (ORB 15 min) en horario de alto volumen (10:00 - 14:00 EST).", "Régimen de Mercado: ")
    add_body("Operaciones de opciones a 1 DTE con Take Profit al 50%.", "Estrategia: ")
    add_body("Si la posición está en pérdida a las 15:55 EST, se ejecuta un Roll Out defensivo a 30 DTE para evitar la asignación inmediata.", "Roll Defensivo: ")

    # Layer 5
    add_heading_2("Capa 5: Bull Market PMCC (Poor Man’s Covered Call)")
    add_body("Tendencia Alcista Confirmada en gráfico diario (EMA-20 > EMA-50).", "Régimen de Mercado: ")
    add_body("Long Call ITM (60-90 DTE, Delta Δ 0.75-0.80) + Short Call OTM semanal (7-14 DTE, Delta Δ 0.20).", "Estrategia: ")
    add_body("Auto-roleo semanal de la Short Call al capturar el 80% de beneficio o a <= 2 DTE.", "Extracción de Theta: ")

    # --- SECTION 4 ---
    add_heading_1("4. Reglas Transversales de Riesgo y Cúpula de Margen")
    add_body("Las 5 capas combinadas NUNCA pueden consumir más del 40% del liquidez disponible en IBKR (InitMarginReq). Se mantiene un 60% de colchón libre de liquidez para absorber crashes sin liquidación.", "Cúpula de Margen (Max Utilization): ")
    add_body("Si el S&P 500 cae más de un -3.0% intradía o el Drawdown del portafolio supera el -2.0% diario, se congelan todas las órdenes de entrada. El sistema entra en modo 'Solo Gestión Defensiva'.", "Circuit Breaker Intradía: ")
    add_body("Prohibidas las órdenes a mercado (MKT) en opciones. Todas las órdenes salen a precio LIMIT a precio medio (Mid ± 1 tick) con timeout de 15 segundos y cancelación automática.", "Ejecución Estricta LIMIT: ")
    add_body("El broker IBKR es la fuente única de verdad (ib.positions() e ib.portfolio()). El libro mayor local utiliza escritura atómica (.tmp -> replace) y reconciliación limpia.", "Reconciliación Atómica: ")

    # --- SECTION 5 ---
    add_heading_1("5. Plan de Despliegue en VM Ubuntu (Docker + Docker Compose)")
    add_body("Contenedor gnzsnz/ib-gateway:latest con display virtual (Xvfb) y reinicio diario automático a las 06:00 EST.", "IBKR Gateway Headless: ")
    add_body("Contenedor Python 3.11-slim aislado, ejecutando el nuevo núcleo core/ (BrokerManager, ContractManager, OrderExecutionEngine, RiskGuardian, InstitutionalLedger).", "Bot DARQ Trading: ")
    add_body("Credenciales almacenadas en archivo .env fuera de Git/Dropbox. Puerto 4002 accesible únicamente dentro de la red interna de Docker (127.0.0.1:4002). Dashboard accesible mediante puerto 10000.", "Seguridad & Red: ")

    # Save document
    doc.save(output_path)
    print(f"Documento creado exitosamente en: {output_path}")

if __name__ == "__main__":
    out_dir = r"C:\Users\HP\Dropbox\D+ARQ\2_FINANZAS_Y_CRIPTO\FINANZAS Y CRIPTO\01_SISTEMAS_TRADING\Sistema de opciones"
    file_path = os.path.join(out_dir, "Propuesta_Arquitectura_Trading_DARQ.docx")
    create_proposal_docx(file_path)
