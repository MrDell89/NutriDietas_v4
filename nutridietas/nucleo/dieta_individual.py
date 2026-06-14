# -*- coding: utf-8 -*-
"""
dieta_individual.py
===================
Construye un PlanSemanal para UN paciente.

Por cada día y cada tiempo de comida elige un platillo del catalogo que el
paciente SI pueda comer (es decir, que no contenga ninguno de sus alimentos
no deseados). Va rotando entre los platillos disponibles para dar variedad.
"""

from nutridietas import config
from nutridietas.nucleo.modelos import PlanSemanal, CeldaDieta
from nutridietas.nucleo.catalogo import Catalogo
from nutridietas.nucleo import reglas_dieta


def construir(paciente, catalogo: Catalogo, numero_plan=None,
              incluir_colacion2=False, comida_libre_domingo=False,
              notas=None):
    """
    Devuelve un PlanSemanal listo para enviarse al generador de Word.
    """
    if numero_plan is None:
        numero_plan = paciente.num_planes + 1

    plan = PlanSemanal(
        paciente=paciente,
        numero_plan=numero_plan,
        notas_superiores=notas or [],
    )

    # Pre-calculamos los platillos aptos por cada tiempo de comida.
    aptos = {}
    for col in config.COLUMNAS:
        t = col["tiempo"]
        if t not in aptos:
            aptos[t] = catalogo.aptos_para(
                t, paciente.restricciones_alimentarias()
            )

    # indices rotatorios por tiempo
    contador = {t: 0 for t in aptos}
    patrones_tres = {"desayuno": {}, "cena": {}}

    for d, dia in enumerate(config.DIAS):
        celdas_dia = []
        proteinas_usadas = set()
        for ci, col in enumerate(config.COLUMNAS):
            t = col["tiempo"]
            titulo_col = col["titulo"]

            # Colación 2 vacia por defecto (como en el formato original)
            if titulo_col == "Colación 2" and not incluir_colacion2:
                celdas_dia.append(None)
                continue

            # Comida libre el domingo (opcional)
            if (comida_libre_domingo and dia == "Domingo"
                    and titulo_col == "Comida"):
                celdas_dia.append(CeldaDieta(texto_especial="Comida libre"))
                continue

            lista = aptos.get(t, [])
            if not lista:
                celdas_dia.append(None)
                continue

            if t in patrones_tres:
                platillo = reglas_dieta.escoger_patron_tres(
                    lista, dia, patrones_tres[t], proteinas_usadas
                )
            else:
                platillo, contador[t] = reglas_dieta.escoger_sin_repetir_proteina(
                    lista, contador[t], proteinas_usadas
                )

            if platillo is None:
                celdas_dia.append(None)
                continue

            proteinas_usadas.update(reglas_dieta.proteinas_de_platillo(platillo))

            celdas_dia.append(
                CeldaDieta(platillo=platillo, factor=paciente.factor_porcion)
            )

        plan.celdas[dia] = celdas_dia

    return plan


def reporte_excluidos(paciente, catalogo: Catalogo):
    """
    Devuelve una lista de (platillo, palabra_que_choca) con los platillos que
    se EXCLUYERON por contener alimentos no deseados del paciente. Util para
    mostrarle al nutriologo por qué no aparecieron ciertos platillos.
    """
    excluidos = []
    for p in catalogo.platillos:
        choca = p.es_aceptable(paciente.restricciones_alimentarias())
        if choca:
            excluidos.append((p, choca))
    return excluidos
