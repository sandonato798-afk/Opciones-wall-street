import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
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

def create_audit_docx(output_path):
    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    PRIMARY_COLOR = RGBColor(180, 40, 40)   # Dark Red / Warning #B42828
    SECONDARY_COLOR = RGBColor(15, 32, 67) # Navy Blue #0F2043
    TEXT_COLOR = RGBColor(40, 40, 40)
    LIGHT_BG = "F8F9FA"

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("INFORME DE AUDITORÍA GLOBAL Y HOJA DE RUTA")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_COLOR

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Sistema de Trading de Opciones D+ARQ — Reconstrucción Institucional")
    run_sub.font.name = 'Arial'
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = SECONDARY_COLOR

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run("Auditoría de 3 Expertos | Estado: FASE 0 & FASE 1 EJECUTADAS | Documento Permanente de Consulta")
    r_meta.font.name = 'Arial'
    r_meta.font.size = Pt(9.5)
    r_meta.font.color.rgb = RGBColor(120, 120, 120)

    doc.add_paragraph() # Spacer

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = SECONDARY_COLOR
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = PRIMARY_COLOR
        return h

    def add_p(text, bold_prefix=""):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.name = 'Arial'
            rb.font.size = Pt(10.5)
            rb.font.bold = True
            rb.font.color.rgb = SECONDARY_COLOR
        r = p.add_run(text)
        r.font.name = 'Arial'
        r.font.size = Pt(10.5)
        r.font.color.rgb = TEXT_COLOR
        return p

    # Section 1
    add_h1("1. Veredicto del Equipo de Auditoría")
    add_p("El sistema anterior NO estaba listo para operar ni en cuenta real ni en Paper Trading. Las primas registradas eran estimaciones fijas Black-Scholes, los strikes no existían en las cadenas reales de IBKR y el broker tenía 0 posiciones registradas. Se ordenó la contención inmediata del bot y la reconstrucción desde el núcleo.")

    # Section 2
    add_h1("2. Diagnóstico de Hallazgos Críticos")
    add_h2("A. Motor de Ejecución")
    add_p("El bot guardaba el trade en el JSON local aunque la orden fallara. En simulación devolvía FILLED a $1.00 fijo.", "Fills Ficticios: ")
    add_p("Take-Profit, Stop-Loss, Rolls y Desacoples solo editaban el JSON. Las posiciones cortas quedaban abiertas en IBKR para siempre.", "Salidas no enviadas: ")
    add_p("Strikes no redondeados a cadenas reales y vencimientos sin validar con reqSecDefOptParams ni qualifyContracts.", "Contratos Inválidos: ")
    add_p("Uso de ordenes MKT en LEAPS de 25 lotes con riesgo de slippage masivo.", "Ordenes a Mercado: ")
    add_p("Cotizaciones con 15 min de retraso. Al recibir $0.00 de IBKR por falta de datos en vivo, calculaba pérdidas ficticias de -$74.000 USD.", "Precios $0.00 / NaN: ")
    add_p("Calculado como 50 + %cambio * 15 en lugar de velas históricas de 14 períodos.", "RSI Falso: ")

    add_h2("B. Hilos y Conexión Socket")
    add_p("Endpoints HTTP POST llamaban a ib_insync desde hilos secundarios del servidor web, causando escrituras concurrentes al socket y cierres silenciosos de asyncio.", "Concurrencia HTTP: ")
    add_p("Watchdog verificaba serverVersion() estático en lugar de realizar reqCurrentTime() real.", "Heartbeat Falso: ")

    add_h2("C. Estado y Datos Fantasma")
    add_p("Los $14.3M reinvertidos registrados salían de un bucle infinito en Alpha donde la señal daba True constantemente y 'desacoplaba' cada 1.5 min.", "Reinversión Fantasma: ")

    add_h2("D. Seguridad y Credenciales")
    add_p("Usuario y contraseña de IBKR expuestos en config.ini en Dropbox, token de GitHub en .github_token y servidor API sin autenticación en 0.0.0.0.", "Credenciales Expuestas: ")

    # Section 3
    add_h1("3. Plan de Reconstrucción Ejecutado (Fases 0, 1 y 2)")
    add_p("Bot detenido. Kill-Switch activado (TRADING_ENABLED: false). Todos los estados JSON fantasma reseteados a 0.", "Fase 0 (Contención): ")
    add_p("Creación del nuevo núcleo en core/ (clock.py, contracts.py, orders.py, ledger.py, risk.py, broker.py). Sin simulaciones ficticias.", "Fase 1 (Núcleo Institucional): ")
    add_p("Creación de config/strategies.yaml. Reconfiguración del Colateral 100% NAV (60% Treasuries directos 12/2027-12/2032, 20% VOO, 15% QQQ, 5% GLD).", "Fase 2 (Configuración Modular): ")

    doc.save(output_path)
    print(f"Informe de auditoria Word creado en: {output_path}")

if __name__ == "__main__":
    out_dir = r"C:\Users\HP\Dropbox\D+ARQ\2_FINANZAS_Y_CRIPTO\FINANZAS Y CRIPTO\01_SISTEMAS_TRADING\Sistema de opciones"
    file_path = os.path.join(out_dir, "Informe_Auditoria_y_Reconstruccion_DARQ.docx")
    create_audit_docx(file_path)
