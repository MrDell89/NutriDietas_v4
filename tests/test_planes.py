# -*- coding: utf-8 -*-
"""Tests de planes.py: construcción del plan desde celdas del editor."""

import config
import planes
from modelos import Paciente


def _celdas_una(dia, ci, datos):
    """Arma un celdas_manual con un solo dato en (dia, ci) y el resto vacío."""
    cm = {d: [{} for _ in config.COLUMNAS] for d in config.DIAS}
    cm[dia][ci] = datos
    return cm


def test_celda_vacia_da_none():
    cm = {d: [{} for _ in config.COLUMNAS] for d in config.DIAS}
    plan = planes.plan_desde_celdas_manual(Paciente("Ana"), cm, 1)
    assert all(c is None for dia in config.DIAS for c in plan.celdas[dia])


def test_celda_normal_construye_platillo():
    cm = _celdas_una("Lunes", 0, {
        "titulo": "Avena",
        "ingredientes": ["• Hojuelas (40 gramos)", "Leche (200 ml)", "  "],
        "nota": "Sin azúcar",
        "video": True,
    })
    plan = planes.plan_desde_celdas_manual(Paciente("Ana"), cm, 1)
    celda = plan.celdas["Lunes"][0]
    assert celda.platillo.nombre == "Avena"
    assert celda.platillo.video is True
    assert celda.platillo.nota == "Sin azúcar"
    # bullets quitados y líneas vacías descartadas
    assert [i.nombre for i in celda.platillo.ingredientes] == \
           ["Hojuelas (40 gramos)", "Leche (200 ml)"]
    # tiempo tomado de la columna 0 (desayuno)
    assert celda.platillo.tiempo == config.COLUMNAS[0]["tiempo"]


def test_comida_libre():
    cm = _celdas_una("Domingo", 2, {"titulo": "Comida libre"})
    plan = planes.plan_desde_celdas_manual(Paciente("Ana"), cm, 1)
    assert plan.celdas["Domingo"][2].texto_especial == "Comida libre"


def test_factor_porcion_se_propaga():
    cm = _celdas_una("Lunes", 0, {"titulo": "Avena", "ingredientes": []})
    plan = planes.plan_desde_celdas_manual(Paciente("Ana", factor_porcion=1.5), cm, 1)
    assert plan.celdas["Lunes"][0].factor == 1.5


def test_dias_o_columnas_faltantes_no_rompen():
    # solo se pasa info parcial; el resto debe quedar como None
    cm = {"Lunes": [{"titulo": "Avena"}]}  # faltan días y columnas
    plan = planes.plan_desde_celdas_manual(Paciente("Ana"), cm, 1)
    assert set(plan.celdas) == set(config.DIAS)
    assert len(plan.celdas["Lunes"]) == len(config.COLUMNAS)
    assert plan.celdas["Lunes"][0].platillo.nombre == "Avena"
    assert plan.celdas["Lunes"][1] is None
