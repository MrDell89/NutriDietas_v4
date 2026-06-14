# -*- coding: utf-8 -*-
"""
generador_pdf.py
================
Genera un PDF idéntico al formato del Lic. Juan Pablo Espino, usando reportlab.
  - Página carta HORIZONTAL
  - Logo arriba a la derecha (encabezado)
  - Título centrado: "Xer Plan alimenticio: Nombre"
  - Tabla 6 columnas (Día + 5 tiempos) × 8 filas (cabecera + 7 días)
  - Cabecera y columna de días en verde #1AA27E
  - Nombres de platillos en verde oscuro #072F25, negrita
  - Ingredientes con viñeta •
  - Notas en cursiva
  - Firma al pie derecha
"""

import logging
import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, Image, HRFlowable)
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.utils import ImageReader

import config

log = logging.getLogger(__name__)

# ── Colores ──────────────────────────────────────────────────────────────── #
VERDE      = colors.HexColor(config.ui(config.COLOR_VERDE_ENCABEZADO))
VERDE_OSC  = colors.HexColor(config.ui(config.COLOR_VERDE_TITULO))
BLANCO     = colors.white
NEGRO      = colors.HexColor(config.ui(config.COLOR_TEXTO))
VERDE_NOTA = colors.HexColor(config.ui(config.COLOR_NOTA))

# ── Estilos de párrafo ────────────────────────────────────────────────────── #
_FONT = "Helvetica"   # reportlab siempre tiene Helvetica (≈ Century Gothic)
_FONT_B = "Helvetica-Bold"
_FONT_I = "Helvetica-Oblique"
_FONT_BI = "Helvetica-BoldOblique"

def _estilo(nombre, font=_FONT, size=8, color=NEGRO,
            align=TA_LEFT, leading=None, spaceBefore=0, spaceAfter=0):
    return ParagraphStyle(
        nombre,
        fontName=font,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or (size * 1.25),
        spaceBefore=spaceBefore,
        spaceAfter=spaceAfter,
        wordWrap='CJK',
    )

ST_TITULO     = _estilo("titulo",     font=_FONT_B, size=14, color=VERDE_OSC, align=TA_CENTER)
ST_TITULO_NRM = _estilo("titulo_nrm", font=_FONT,   size=14, color=VERDE_OSC, align=TA_CENTER)
ST_NOTA_SUP   = _estilo("nota_sup",   font=_FONT,   size=10, color=NEGRO)
ST_CABECERA   = _estilo("cabecera",   font=_FONT_B, size=9,  color=BLANCO,    align=TA_CENTER)
ST_DIA        = _estilo("dia",        font=_FONT_B, size=9,  color=BLANCO,    align=TA_CENTER)
ST_PLATILLO   = _estilo("platillo",   font=_FONT_B, size=8,  color=VERDE_OSC, align=TA_CENTER)
ST_ING        = _estilo("ing",        font=_FONT,   size=7,  color=NEGRO,     leading=9)
ST_NOTA_CELDA = _estilo("nota_celda", font=_FONT_I, size=7,  color=VERDE_NOTA, align=TA_CENTER)
ST_ESPECIAL   = _estilo("especial",   font=_FONT_B, size=10, color=VERDE_OSC,  align=TA_CENTER)
ST_FIRMA      = _estilo("firma",      font=_FONT_BI, size=9, color=VERDE_OSC,  align=TA_RIGHT)
ST_LIBRE      = _estilo("libre",      font=_FONT_B,  size=11, color=VERDE_OSC, align=TA_CENTER)


# ── Anchos de columna (puntos) ────────────────────────────────────────────── #
# Página carta landscape: 792 × 612 pts. Márgenes 0.4" = 28.8 pts c/u
# Ancho útil ≈ 792 - 57.6 = 734.4
COL_DIA  = 52
COL_DES  = 148
COL_COL1 = 92
COL_COM  = 148
COL_COL2 = 100
COL_CEN  = 148
COL_TOTAL = COL_DIA + COL_DES + COL_COL1 + COL_COM + COL_COL2 + COL_CEN  # 688


def _celda_contenido(celda_obj, factor=1.0):
    """
    Convierte un CeldaDieta en una lista de Paragraphs para la celda de la tabla.
    """
    if celda_obj is None:
        return [Paragraph("", ST_ING)]

    if celda_obj.texto_especial:
        return [
            Paragraph(celda_obj.texto_especial, ST_LIBRE),
            Paragraph(":)", ST_LIBRE),
        ]

    if celda_obj.platillo is None:
        return [Paragraph("", ST_ING)]

    p = celda_obj.platillo
    titulo = p.nombre + (" (Video)" if p.video else "")
    parrafos = [Paragraph(titulo, ST_PLATILLO)]

    for ing in p.ingredientes:
        txt = "• " + ing.render(factor)
        parrafos.append(Paragraph(txt, ST_ING))

    if p.nota:
        parrafos.append(Paragraph(p.nota, ST_NOTA_CELDA))

    return parrafos


def _contenido_desde_texto(titulo, ingredientes_txt, nota=None):
    """
    Construye una celda a partir de strings planos (para el editor manual).
    ingredientes_txt: lista de strings como "• Pollo (150 gr)"
    """
    parrafos = [Paragraph(titulo, ST_PLATILLO)]
    for ing in ingredientes_txt:
        parrafos.append(Paragraph("• " + ing if not ing.startswith("•") else ing, ST_ING))
    if nota:
        parrafos.append(Paragraph(nota, ST_NOTA_CELDA))
    return parrafos


def generar(plan, ruta_salida=None):
    """
    Genera el PDF de un PlanSemanal.
    Devuelve la ruta del archivo creado.
    """
    if ruta_salida is None:
        os.makedirs(config.CARPETA_SALIDAS, exist_ok=True)
        nombre = plan.nombre_archivo().replace(".docx", ".pdf")
        ruta_salida = os.path.join(config.CARPETA_SALIDAS, nombre)
    else:
        # si recibe ruta .docx la convierte a .pdf
        if ruta_salida.endswith(".docx"):
            ruta_salida = ruta_salida.replace(".docx", ".pdf")

    MARGEN = 0.4 * inch

    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=landscape(letter),
        leftMargin=MARGEN, rightMargin=MARGEN,
        topMargin=MARGEN + 0.3 * inch,   # espacio para encabezado
        bottomMargin=MARGEN,
    )

    story = []

    # ── Encabezado: logo a la derecha + título centrado ─────────────────── #
    encabezado_items = []

    # fila con logo a la derecha
    logo_cell = ""
    if os.path.exists(config.RUTA_LOGO):
        try:
            logo_cell = Image(config.RUTA_LOGO, width=1.3 * inch, height=0.85 * inch)
        except Exception:
            log.warning("No se pudo cargar el logo para el PDF: %s",
                        config.RUTA_LOGO, exc_info=True)
            logo_cell = ""

    # Título
    # "1er Plan alimenticio:  Nombre"  ← dos párrafos combinados en una celda
    ordinal_txt, _, nombre_pac = plan.titulo().partition(": ")
    celda_titulo = [
        Paragraph(f'<b>{ordinal_txt}:</b> {nombre_pac}', ST_TITULO),
    ]

    if logo_cell:
        hdr_data = [[celda_titulo, logo_cell]]
        hdr_col  = [COL_TOTAL - 1.4 * inch, 1.4 * inch]
        hdr_tbl  = Table(hdr_data, colWidths=hdr_col)
        hdr_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",  (1, 0), (1, 0),  "RIGHT"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        story.append(hdr_tbl)
    else:
        for p in celda_titulo:
            story.append(p)

    # ── Notas superiores ─────────────────────────────────────────────────── #
    for nota in plan.notas_superiores:
        story.append(Paragraph(nota, ST_NOTA_SUP))

    story.append(Spacer(1, 6))

    # ── Construcción de la tabla ─────────────────────────────────────────── #
    DIAS   = config.DIAS
    COLS   = config.COLUMNAS   # lista de dicts con "titulo" y "tiempo"

    # fila cabecera
    cab = [Paragraph("", ST_CABECERA)]
    for c in COLS:
        cab.append(Paragraph(c["titulo"], ST_CABECERA))

    rows = [cab]

    for dia in DIAS:
        fila = [Paragraph(dia, ST_DIA)]
        celdas_dia = plan.celdas.get(dia, [])
        for i in range(len(COLS)):
            celda_obj = celdas_dia[i] if i < len(celdas_dia) else None
            factor = plan.paciente.factor_porcion if plan.paciente else 1.0
            fila.append(_celda_contenido(celda_obj, factor))
        rows.append(fila)

    col_widths = [COL_DIA, COL_DES, COL_COL1, COL_COM, COL_COL2, COL_CEN]
    tabla = Table(rows, colWidths=col_widths, repeatRows=1)

    n_filas = len(rows)
    n_cols  = len(col_widths)

    # Estilo base
    estilo = [
        # bordes
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.black),
        # cabecera fondo verde
        ("BACKGROUND",  (0, 0), (-1, 0),  VERDE),
        # columna días fondo verde
        ("BACKGROUND",  (0, 1), (0, -1),  VERDE),
        # alineación vertical centrada
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("VALIGN",      (0, 0), (0, -1),  "MIDDLE"),
        ("VALIGN",      (0, 0), (-1, 0),  "MIDDLE"),
        # padding
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0),(-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
        # alternas leve color en filas de datos
        *[("ROWBACKGROUND", (1, r), (-1, r),
           colors.HexColor("#F0FAF6") if r % 2 == 0 else colors.white)
          for r in range(1, n_filas)],
    ]

    tabla.setStyle(TableStyle(estilo))
    story.append(tabla)

    # ── Firma ────────────────────────────────────────────────────────────── #
    story.append(Spacer(1, 6))
    story.append(Paragraph(config.FIRMA, ST_FIRMA))

    doc.build(story)
    return ruta_salida


def generar_desde_celdas_manuales(paciente, celdas_manual,
                                   numero_plan, notas=None,
                                   ruta_salida=None):
    """
    Versión para el editor visual de la GUI.

    celdas_manual: dict[dia] = list de 5 dicts:
        {"titulo": str, "ingredientes": [str], "nota": str|None, "video": bool}
    """
    from modelos import PlanSemanal, CeldaDieta, Platillo, Ingrediente

    plan = PlanSemanal(
        paciente=paciente,
        numero_plan=numero_plan,
        notas_superiores=notas or [],
        celdas={},
    )

    for dia in config.DIAS:
        fila = []
        celdas_dia = celdas_manual.get(dia, [{}] * 5)
        for ci, datos in enumerate(celdas_dia):
            if not datos or not datos.get("titulo"):
                fila.append(None)
                continue
            if datos.get("titulo", "").lower() == "comida libre":
                fila.append(CeldaDieta(texto_especial="Comida libre"))
                continue
            # construir platillo temporal desde los datos del editor
            ings = []
            for txt in datos.get("ingredientes", []):
                txt = txt.strip().lstrip("•").strip()
                if txt:
                    ings.append(Ingrediente(nombre=txt))
            pl = Platillo(
                id=f"manual_{dia}_{ci}",
                nombre=datos.get("titulo", ""),
                tiempo=config.COLUMNAS[ci]["tiempo"],
                ingredientes=ings,
                video=datos.get("video", False),
                nota=datos.get("nota"),
            )
            fila.append(CeldaDieta(platillo=pl,
                                   factor=paciente.factor_porcion))
        plan.celdas[dia] = fila

    return generar(plan, ruta_salida=ruta_salida)
