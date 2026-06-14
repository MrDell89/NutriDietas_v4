# -*- coding: utf-8 -*-
"""
dieta_grupal.py
===============
Genera dietas EN GRUPO para varios pacientes a la vez.

Idea central (lo que pediste):
  - Se eligen los MISMOS platillos para todos los pacientes del grupo, de modo
    que cocinen/coman lo mismo.
  - Solo cambian las PORCIONES: cada paciente tiene su propio factor_porcion,
    así que el mismo platillo se imprime con cantidades distintas en su Word.
  - Un platillo solo se usa si es apto para TODOS (no contiene alimentos que
    le desagraden a NINGUNO de los pacientes seleccionados).

Funciones:
  - comparar_gustos(): reporte de compatibilidad del grupo (qué pueden comer
    todos, qué choca y con quién).
  - construir_grupo(): devuelve un dict {paciente: PlanSemanal} con el mismo
    menú y porciones individualizadas.
"""

from nutridietas import config
from nutridietas.nucleo import utilidades as U
from nutridietas.nucleo.modelos import PlanSemanal, CeldaDieta
from nutridietas.nucleo.catalogo import Catalogo


# --------------------------------------------------------------------------- #
def comparar_gustos(pacientes, catalogo: Catalogo):
    """
    Analiza la compatibilidad del grupo. Devuelve un diccionario con:
      - 'comunes': {tiempo: [platillos aptos para todos]}
      - 'conflictos': lista de (platillo, [pacientes que no lo pueden comer, palabra])
      - 'no_deseados_union': set con todos los alimentos no deseados del grupo
    """
    listas_nd = [p.no_deseados for p in pacientes]

    comunes = {}
    for col in config.COLUMNAS:
        t = col["tiempo"]
        if t not in comunes:
            comunes[t] = catalogo.aptos_para_todos(t, listas_nd)

    conflictos = []
    for p in catalogo.platillos:
        choca_con = []
        for pac in pacientes:
            palabra = p.es_aceptable(pac.no_deseados)
            if palabra:
                choca_con.append((pac.nombre, palabra))
        if choca_con:
            conflictos.append((p, choca_con))

    union = set()
    for nd in listas_nd:
        for x in nd:
            union.add(x)

    return {
        "comunes": comunes,
        "conflictos": conflictos,
        "no_deseados_union": union,
    }


# --------------------------------------------------------------------------- #
def construir_grupo(pacientes, catalogo: Catalogo, numero_plan=1,
                    incluir_colacion2=False, notas=None):
    """
    Devuelve una lista de pares [(paciente, PlanSemanal), ...]. Todos comparten
    el mismo menú; las porciones se ajustan con el factor_porcion de cada
    paciente.
    """
    listas_nd = [p.no_deseados for p in pacientes]

    # platillos aptos para TODOS, por tiempo
    aptos = {}
    for col in config.COLUMNAS:
        t = col["tiempo"]
        if t not in aptos:
            aptos[t] = catalogo.aptos_para_todos(t, listas_nd)

    # 1) Elegimos UN menú comun (mismo platillo por dia/columna para el grupo)
    contador = {t: 0 for t in aptos}
    menu = {}  # menu[dia] = lista de platillos (o None) por columna
    for dia in config.DIAS:
        fila = []
        for col in config.COLUMNAS:
            t = col["tiempo"]
            if col["titulo"] == "Colación 2" and not incluir_colacion2:
                fila.append(None)
                continue
            lista = aptos.get(t, [])
            if not lista:
                fila.append(None)
                continue
            idx = contador[t] % len(lista)
            fila.append(lista[idx])
            contador[t] += 1
        menu[dia] = fila

    # 2) Para cada paciente, mismo menú pero con SU factor de porcion
    resultado = []
    for pac in pacientes:
        plan = PlanSemanal(
            paciente=pac,
            numero_plan=(pac.num_planes + 1) if numero_plan is None else numero_plan,
            notas_superiores=(notas or []) + [
                "Dieta en grupo — mismo menú, porciones individualizadas."
            ],
        )
        for dia in config.DIAS:
            celdas = []
            for platillo in menu[dia]:
                if platillo is None:
                    celdas.append(None)
                else:
                    celdas.append(CeldaDieta(platillo=platillo,
                                             factor=pac.factor_porcion))
            plan.celdas[dia] = celdas
        resultado.append((pac, plan))

    return resultado
