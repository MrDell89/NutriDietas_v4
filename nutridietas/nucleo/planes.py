# -*- coding: utf-8 -*-
"""
planes.py
=========
Construcción de un PlanSemanal a partir de las celdas del editor visual
(datos "manuales" capturados en la GUI).

Vive aparte de los generadores (docx/pdf) y de la GUI para tener UN solo
lugar que arme el plan desde celdas manuales, y para poder probarlo sin
depender de Tkinter ni de las librerías de salida.

Formato de entrada (celdas_manual):
    dict[dia] = lista de 5 dicts (uno por columna), cada uno:
        {"titulo": str, "ingredientes": [str], "nota": str|None, "video": bool}
    Un dict vacío (o sin "titulo") representa una celda vacía.
    Un "titulo" == "comida libre" produce una celda especial de comida libre.
"""

from nutridietas import config
from nutridietas.nucleo.modelos import PlanSemanal, CeldaDieta, Platillo, Ingrediente


def plan_desde_celdas_manual(paciente, celdas_manual, numero_plan, notas=None):
    """Devuelve un PlanSemanal armado desde las celdas del editor."""
    plan = PlanSemanal(
        paciente=paciente,
        numero_plan=numero_plan,
        notas_superiores=notas or [],
        celdas={},
    )

    for dia in config.DIAS:
        fila = []
        celdas_dia = celdas_manual.get(dia, [])
        for ci, _col in enumerate(config.COLUMNAS):
            datos = celdas_dia[ci] if ci < len(celdas_dia) else None

            if not datos or not datos.get("titulo"):
                fila.append(None)
                continue

            if datos.get("titulo", "").strip().lower() == "comida libre":
                fila.append(CeldaDieta(texto_especial="Comida libre"))
                continue

            # construir un platillo temporal desde el texto del editor
            ingredientes = []
            for txt in datos.get("ingredientes", []):
                txt = txt.strip().lstrip("•").strip()
                if txt:
                    ingredientes.append(Ingrediente(nombre=txt))

            platillo = Platillo(
                id=f"manual_{dia}_{ci}",
                nombre=datos.get("titulo", ""),
                tiempo=config.COLUMNAS[ci]["tiempo"],
                ingredientes=ingredientes,
                video=datos.get("video", False),
                nota=datos.get("nota"),
            )
            fila.append(CeldaDieta(platillo=platillo,
                                   factor=paciente.factor_porcion))

        plan.celdas[dia] = fila

    return plan
