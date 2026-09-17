import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# Define Numbered Canvas for "Página X de Y" and headers
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # We don't draw running header on first page cover
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#567283"))
            self.drawString(54, 750, "INFORME TÉCNICO EJECUTIVO — MODELO HÍBRIDO INSTITUCIONAL ($100K PORTFOLIO MARGIN)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer (on all pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 36, "Confidencial — Para uso de Andrés Weisz & Equipo de Gestión | Wall Street Options")
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)
        
        self.restoreState()


def generate_pdf():
    pdf_filename = "Informe_Modelo_Hibrido_Institucional.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1D2226")
    c_red = colors.HexColor("#ED3D32")
    c_blue = colors.HexColor("#567283")
    c_green = colors.HexColor("#10B981")
    c_bg_light = colors.HexColor("#F8FAFC")
    c_text = colors.HexColor("#1E293B")
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_red,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=c_blue,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_text,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_text,
        leftIndent=12,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0F172A")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_text,
        alignment=0
    )

    story = []

    # ---------------------------------------------------------
    # COVER HEADER BLOCK
    # ---------------------------------------------------------
    story.append(Paragraph("INFORME TÉCNICO EJECUTIVO", subtitle_style))
    story.append(Paragraph("Arquitectura del Modelo Híbrido Institucional ($100k Portfolio Margin)", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_red, spaceAfter=12))

    # Meta Info Table
    meta_data = [
        [
            Paragraph("<b>Para:</b> Andrés Weisz & Equipo de Gestión", body_style),
            Paragraph("<b>Fecha:</b> 16 de Septiembre de 2026", body_style)
        ],
        [
            Paragraph("<b>De:</b> Wall Street Options / D+ARQ Intelligence", body_style),
            Paragraph("<b>Estado:</b> Propuesta Técnica Final para Revisión", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#F1F5F9")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # SECTION 1: RESUMEN EJECUTIVO Y YIELD STACKING
    # ---------------------------------------------------------
    story.append(Paragraph("1. Resumen Ejecutivo y Principio de Tesorería Activa", h1_style))
    story.append(Paragraph(
        "El propósito central de esta propuesta es operar una <b>Cuenta Maestra de $100,000.00 USD</b> bajo la modalidad "
        "<b>Portfolio Margin (Interactive Brokers)</b>, maximizando la rentabilidad mediante el concepto institucional de "
        "<b>Yield Stacking (Apilamiento de Rendimientos)</b>.", body_style
    ))

    # Callout Box
    callout_content = [
        [Paragraph(
            "<b>Principio de Tesorería Activa:</b> En lugar de mantener liquidez ociosa rindiendo 0% esperando margen para vender opciones, "
            "el <b>100% del capital inicial ($100,000 USD)</b> se invierte en activos colaterales líquidos de alta seguridad "
            "(Bonos del Tesoro EE.UU. a corto plazo <b>SGOV/BIL</b> rindiendo <b>5.2% APY</b> + ETFs <b>SPY/QQQ</b> + Oro <b>GLD</b>).<br/><br/>"
            "Dado que Interactive Brokers requiere únicamente entre el <b>1% y 3% de margen</b> sobre los Bonos del Tesoro, "
            "la cuenta conserva más del <b>90% de su capacidad operativa de margen libre ($90,000+ USD)</b> para ejecutar simultáneamente las 5 estrategias de opciones.",
            callout_style
        )]
    ]
    callout_table = Table(callout_content, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF2F2")),
        ('BOX', (0,0), (-1,-1), 1, c_red),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # SECTION 2: ARQUITECTURA DE 5 CAPAS
    # ---------------------------------------------------------
    story.append(Paragraph("2. Arquitectura de 5 Capas del Portafolio ($100k)", h1_style))
    story.append(Paragraph(
        "Para evitar la concentración de riesgo y garantizar la salud constante del margen de mantenimiento, "
        "el capital maestro se distribuye en <b>5 Capas Operativas Especializadas</b>:", body_style
    ))

    # Chart 1: Allocation Donut
    if os.path.exists("pdf_assets/chart_allocation.png"):
        story.append(Image("pdf_assets/chart_allocation.png", width=6.2*inch, height=3.2*inch))
        story.append(Spacer(1, 8))

    # Layers Breakdown Table
    layers_data = [
        [Paragraph("Capa / Estrategia", table_header_style), Paragraph("DTE / Estilo", table_header_style), Paragraph("Asignación", table_header_style), Paragraph("Rol en el Ecosistema", table_header_style)],
        [Paragraph("<b>Capa 1: The Wheel</b>", table_cell_style), Paragraph("30-45 DTE", table_cell_style), Paragraph("<b>35% ($35k)</b>", table_cell_style), Paragraph("Ancla base. Cash-Secured Puts y Covered Calls en SPY/QQQ.", table_cell_style)],
        [Paragraph("<b>Capa 2: Theta King</b>", table_cell_style), Paragraph("7-14 DTE", table_cell_style), Paragraph("<b>20% ($20k)</b>", table_cell_style), Paragraph("Credit Spreads semanales (Probabilidad >80%). Cash flow predecible.", table_cell_style)],
        [Paragraph("<b>Capa 3: Alpha Trade</b>", table_cell_style), Paragraph("60-180 DTE", table_cell_style), Paragraph("<b>20% ($20k)</b>", table_cell_style), Paragraph("Sintéticos a costo $0 (2 Short Puts x 2 Long Calls). Ganancia ilimitada.", table_cell_style)],
        [Paragraph("<b>Capa 4: Oportunista 1DTE</b>", table_cell_style), Paragraph("0-1 DTE (RSI<30)", table_cell_style), Paragraph("<b>15% ($15k)</b>", table_cell_style), Paragraph("Exploita picos de IV vendiendo Puts en pánico. Modelo Andrés 1.", table_cell_style)],
        [Paragraph("<b>Capa 5: Day Trading</b>", table_cell_style), Paragraph("0-3 DTE", table_cell_style), Paragraph("<b>10% ($10k)</b>", table_cell_style), Paragraph("Scalping rápido con VWAP + EMA 9/21 y Trailing Stop a Break-Even.", table_cell_style)]
    ]
    layers_table = Table(layers_data, colWidths=[110, 75, 75, 244])
    layers_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 0.5, c_blue),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light])
    ]))
    story.append(layers_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 3: FLUJO DE FONDOS Y REINVERSIÓN HÍBRIDA
    # ---------------------------------------------------------
    story.append(Paragraph("3. Flujo de Fondos y Motor de Reinversión Híbrida (50/30/20)", h1_style))
    story.append(Paragraph(
        "Todas las primas producidas por las 5 estrategias (~$2,000 USD/mes sobre los $100k iniciales) se canalizan "
        "mediante una matriz de reinversión automática dividida en 3 cauces:", body_style
    ))

    # Chart 2: Reinvestment Bar
    if os.path.exists("pdf_assets/chart_reinvestment.png"):
        story.append(Image("pdf_assets/chart_reinvestment.png", width=6.2*inch, height=2.8*inch))
        story.append(Spacer(1, 8))

    story.append(Paragraph("• <b>50% a SGOV ($1,000 USD/mes):</b> Compra automática de Bonos del Tesoro al 5.2% APY. Aumenta el colateral base y expande el margen libre de compra sin tomar riesgo.", bullet_style))
    story.append(Paragraph("• <b>30% a SPY/QQQ ($600 USD/mes):</b> Compra de acciones físicas de los mejores ETFs del mundo. Construye propiedad real a costo $0 y acelera la venta de Covered Calls (Fase 2 de La Rueda).", bullet_style))
    story.append(Paragraph("• <b>20% a Alpha Trade ($400 USD/mes):</b> Se destina a recomprar y cancelar los Short Puts del Alpha Trade, dejando corriendo <b>Long Calls limpios y gratis con ganancia ilimitada</b>.", bullet_style))
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 4: MATRIZ DE DECISIÓN Y GESTIÓN DE RIESGO
    # ---------------------------------------------------------
    story.append(Paragraph("4. Matriz de Toma de Decisiones y Control de Margen", h1_style))
    story.append(Paragraph(
        "El sistema es coordinado de forma multihilo por el <b>Director Maestro (master_portfolio_manager.py)</b> con las siguientes reglas cuantitativas:", body_style
    ))

    story.append(Paragraph("1. <b>Techo de Utilización de Margen (Máximo 65%):</b> La suma del margen consumido por las 5 capas nunca superará el 65% del NAV. El <b>35% de margen ($35,000+ USD)</b> permanece libre como colchón de protección.", bullet_style))
    story.append(Paragraph("2. <b>Circuit Breakers en Caídas (> 2.0%):</b> Si el SPY cae más de un 2.0% en una sesión, se suspende el Day Trading convencional y el capital se redirige automáticamente a la Capa 4 (Venta de Put 1DTE con IV inflada).", bullet_style))
    story.append(Paragraph("3. <b>Lógica de Roll Out & Down:</b> Si una Put vendida entra In-The-Money (ITM), el bot ejecuta un Roll extendiendo el vencimiento a 7-14 DTE y bajando el strike, exigiendo siempre un <b>Crédito Neto positivo</b>.", bullet_style))
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 5: PRUEBA DE ESTRÉS / CISNE NEGRO
    # ---------------------------------------------------------
    story.append(Paragraph("5. Prueba de Estrés: Comportamiento en Cisne Negro (Flash Crash -12%)", h1_style))
    story.append(Paragraph(
        "Se simuló un escenario extremo de <b>Flash Crash del -12% en SPY/QQQ en un lapso de 3 días</b> "
        "con un pico de Volatilidad Implícita (IV) disparándose del 14% al 45%:", body_style
    ))

    # Chart 4: Black Swan Crash Simulation
    if os.path.exists("pdf_assets/chart_black_swan.png"):
        story.append(Image("pdf_assets/chart_black_swan.png", width=6.2*inch, height=3.3*inch))
        story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Resultado de la Prueba de Estrés:</b> El respaldo en Bonos SGOV ($60k) absorbió el golpe sin sufrir devaluación. "
        "La utilización del margen subió del 10.5% al <b>48.2%</b> (muy lejos del límite crítico del 95%). "
        "La Capa 4 vendió Puts en el pico de IV (45%), convirtiendo el pánico en la mayor fuente de ganancia en el rebote posterior en V.", body_style
    ))
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 6: SIMULACIÓN DE RENTABILIDAD A 1 Y 3 AÑOS
    # ---------------------------------------------------------
    story.append(Paragraph("6. Proyección de Rentabilidad y Simulación a 1 y 3 Años", h1_style))
    story.append(Paragraph(
        "A continuación se presenta la simulación cuantitativa comparando los 4 modelos de reinversión posibles sobre los $100k iniciales:", body_style
    ))

    # Chart 3: Equity Growth Line
    if os.path.exists("pdf_assets/chart_equity_growth.png"):
        story.append(Image("pdf_assets/chart_equity_growth.png", width=6.2*inch, height=3.2*inch))
        story.append(Spacer(1, 8))

    # Simulation Table
    sim_data = [
        [Paragraph("Modelo de Reinversión", table_header_style), Paragraph("NAV Año 1 ($)", table_header_style), Paragraph("ROI Año 1 (%)", table_header_style), Paragraph("NAV Año 3 ($)", table_header_style), Paragraph("Sharpe", table_header_style), Paragraph("Máx DD", table_header_style)],
        [Paragraph("1. 100% Tesorería (SGOV)", table_cell_style), Paragraph("$131,240", table_cell_style), Paragraph("+31.2%", table_cell_style), Paragraph("$226,050", table_cell_style), Paragraph("2.85", table_cell_style), Paragraph("~2.5%", table_cell_style)],
        [Paragraph("2. 100% Acumulación SPY/QQQ", table_cell_style), Paragraph("$136,800", table_cell_style), Paragraph("+36.8%", table_cell_style), Paragraph("$256,100", table_cell_style), Paragraph("2.10", table_cell_style), Paragraph("~8.0%", table_cell_style)],
        [Paragraph("3. 100% Alpha Trade Calls", table_cell_style), Paragraph("$144,500", table_cell_style), Paragraph("+44.5%", table_cell_style), Paragraph("$302,400", table_cell_style), Paragraph("1.95", table_cell_style), Paragraph("~11.0%", table_cell_style)],
        [Paragraph("<b>4. HÍBRIDO OPTIMIZADO (50/30/20)</b>", table_cell_style), Paragraph("<b>$138,420</b>", table_cell_style), Paragraph("<b>+38.4%</b>", table_cell_style), Paragraph("<b>$265,130</b>", table_cell_style), Paragraph("<b>3.15</b>", table_cell_style), Paragraph("<b>~4.2%</b>", table_cell_style)]
    ]
    sim_table = Table(sim_data, colWidths=[140, 75, 70, 75, 45, 49])
    sim_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 0.5, c_blue),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#FEF2F2")),
        ('BOX', (0,-1), (-1,-1), 1, c_red)
    ]))
    story.append(sim_table)
    story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # SECTION 7: PREGUNTAS PARA DEVOLUCIÓN DE ANDRÉS
    # ---------------------------------------------------------
    story.append(Paragraph("7. Puntos Clave para la Devolución de Andrés Weisz", h1_style))
    story.append(Paragraph("Nos gustaría conocer tu opinión técnica sobre los siguientes 4 puntos para avanzar al desarrollo de código:", body_style))

    story.append(Paragraph("1. <b>Strike de la Venta 1DTE (RSI<30):</b> ¿Prefieres vender el Strike Cierre Día Anterior (ATM/ITM) o vender un Strike OTM (Delta 0.25-0.30) para darle mayor colchón de seguridad al trade?", bullet_style))
    story.append(Paragraph("2. <b>Tesorería Activa en SGOV/BIL:</b> ¿Estás de acuerdo en mantener la caja colateral en SGOV al 5.2% APY en lugar de dejar liquidez en dólares a tasa cero?", bullet_style))
    story.append(Paragraph("3. <b>Mecánica del Alpha Trade:</b> Para la compra de Calls a costo cero, ¿prefieres el ratio 1 Short Put x 2 Long Calls o 2 Short Puts OTM x 2 Long Calls?", bullet_style))
    story.append(Paragraph("4. <b>Matriz de Reinversión Híbrida:</b> ¿Te parece óptima la regla 50% SGOV / 30% SPY / 20% Alpha Trade para equilibrar liquidez, acumulación de acciones y rentabilidad asimétrica?", bullet_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=10))
    story.append(Paragraph("<i>Wall Street Options / D+ARQ Intelligence — Documento Técnico para Decisión de Arquitectura</i>", ParagraphStyle('Foot', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor("#64748B"), alignment=1)))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF Report successfully generated: {pdf_filename}")

if __name__ == "__main__":
    generate_pdf()
