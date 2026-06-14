# -*- coding: utf-8 -*-
"""
generadores.py
==============
Fachada única para generar una dieta en distintos formatos (Word o PDF).

Evita que cada parte del programa (GUI, CLI) tenga que importar los dos
módulos y repetir la rama  "pdf si … si no docx"  y el cálculo de la
extensión del archivo. Ambos generadores comparten la misma firma
    generar(plan, ruta_salida=None) -> ruta
por lo que aquí solo se elige cuál usar según el formato pedido.
"""

import generador_docx
import generador_pdf
import planes

FORMATOS = ("docx", "pdf")


def extension(formato):
    """Devuelve la extensión de archivo correspondiente al formato."""
    return ".pdf" if formato == "pdf" else ".docx"


def generar(plan, formato="docx", ruta_salida=None):
    """Genera la dieta de `plan` en el formato indicado. Devuelve la ruta."""
    if formato == "pdf":
        return generador_pdf.generar(plan, ruta_salida=ruta_salida)
    return generador_docx.generar(plan, ruta_salida=ruta_salida)


def generar_desde_celdas_manual(paciente, celdas_manual, numero_plan,
                                notas=None, ruta_salida=None, formato="docx"):
    """
    Construye el plan desde las celdas del editor y lo genera en el formato
    indicado. Centraliza lo que antes hacían por separado la GUI (para Word)
    y generador_pdf.generar_desde_celdas_manuales (para PDF).
    """
    plan = planes.plan_desde_celdas_manual(paciente, celdas_manual,
                                           numero_plan, notas=notas)
    return generar(plan, formato=formato, ruta_salida=ruta_salida)
