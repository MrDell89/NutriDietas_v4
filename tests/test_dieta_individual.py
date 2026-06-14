# -*- coding: utf-8 -*-
"""Tests de dieta_individual.py: armado del plan semanal individual."""

import config
import dieta_individual as di
from catalogo import Catalogo
from modelos import Platillo, Paciente, Ingrediente


def _catalogo():
    """Catálogo en memoria con varios platillos por tiempo."""
    c = Catalogo(ruta="__inexistente__.json")  # arranca vacío
    c.platillos = [
        Platillo("d1", "Avena", "desayuno", [Ingrediente("Leche", 200, "ml")]),
        Platillo("d2", "Fruta", "desayuno", []),
        Platillo("c1", "Nuez", "colacion", []),
        Platillo("c2", "Yogur", "colacion", []),
        Platillo("m1", "Pollo", "comida", []),
        Platillo("m2", "Pescado", "comida", []),
        Platillo("n1", "Ensalada", "cena", []),
    ]
    return c


def test_plan_tiene_7_dias_y_5_columnas():
    plan = di.construir(Paciente("Ana"), _catalogo(), numero_plan=1)
    assert set(plan.celdas) == set(config.DIAS)
    for dia in config.DIAS:
        assert len(plan.celdas[dia]) == len(config.COLUMNAS)


def test_colacion2_vacia_por_defecto():
    plan = di.construir(Paciente("Ana"), _catalogo(), numero_plan=1,
                        incluir_colacion2=False)
    # índice 3 = "Colación 2"
    assert all(plan.celdas[dia][3] is None for dia in config.DIAS)


def test_colacion2_se_llena_si_se_pide():
    plan = di.construir(Paciente("Ana"), _catalogo(), numero_plan=1,
                        incluir_colacion2=True)
    assert plan.celdas["Lunes"][3] is not None


def test_rotacion_da_variedad_entre_dias():
    plan = di.construir(Paciente("Ana"), _catalogo(), numero_plan=1)
    # columna 0 = desayuno: Lunes y Martes deben alternar entre Avena/Fruta
    lunes = plan.celdas["Lunes"][0].platillo.nombre
    martes = plan.celdas["Martes"][0].platillo.nombre
    assert {lunes, martes} == {"Avena", "Fruta"}


def test_comida_libre_domingo():
    plan = di.construir(Paciente("Ana"), _catalogo(), numero_plan=1,
                        comida_libre_domingo=True)
    celda = plan.celdas["Domingo"][2]  # índice 2 = "Comida"
    assert celda.texto_especial == "Comida libre"


def test_excluye_platillos_no_deseados():
    pac = Paciente("Ana", no_deseados=["leche"])
    plan = di.construir(pac, _catalogo(), numero_plan=1)
    # la Avena (lleva leche) no debe aparecer en ningún desayuno
    desayunos = {plan.celdas[d][0].platillo.nombre for d in config.DIAS}
    assert "Avena" not in desayunos
    assert desayunos == {"Fruta"}


def test_factor_porcion_se_propaga_a_celdas():
    pac = Paciente("Ana", factor_porcion=1.5)
    plan = di.construir(pac, _catalogo(), numero_plan=1)
    assert plan.celdas["Lunes"][0].factor == 1.5


def test_numero_plan_por_defecto_es_siguiente():
    pac = Paciente("Ana", num_planes=4)
    plan = di.construir(pac, _catalogo())  # numero_plan=None
    assert plan.numero_plan == 5


def test_reporte_excluidos_lista_platillo_y_palabra():
    pac = Paciente("Ana", no_deseados=["leche"])
    excluidos = di.reporte_excluidos(pac, _catalogo())
    assert ("Avena", "leche") in [(p.nombre, palabra) for p, palabra in excluidos]


def test_sin_platillos_aptos_celda_es_none():
    pac = Paciente("Ana", no_deseados=["leche", "fruta"])
    plan = di.construir(pac, _catalogo(), numero_plan=1)
    # no quedan desayunos aptos → todas las celdas de desayuno vacías
    assert all(plan.celdas[d][0] is None for d in config.DIAS)
