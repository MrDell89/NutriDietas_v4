# -*- coding: utf-8 -*-
"""Tests de utilidades.py: normalización, fracciones y escalado de porciones."""

import pytest

from nutridietas.nucleo import utilidades as U


# ── normalizar ──────────────────────────────────────────────────────────────
def test_normalizar_none_devuelve_vacio():
    assert U.normalizar(None) == ""


def test_normalizar_minusculas_y_sin_acentos():
    assert U.normalizar("Sárdiná") == "sardina"
    assert U.normalizar("  PÓLLO  ") == "pollo"


def test_normalizar_acepta_no_str():
    assert U.normalizar(123) == "123"


# ── cantidad_a_texto ────────────────────────────────────────────────────────
@pytest.mark.parametrize("valor, esperado", [
    (None, ""),
    (2, "2"),
    (4.0, "4"),
    (0.5, "1/2"),
    (0.25, "1/4"),
    (0.75, "3/4"),
    (1.5, "1 1/2"),
    (1.25, "1 1/4"),
])
def test_cantidad_a_texto(valor, esperado):
    assert U.cantidad_a_texto(valor) == esperado


# ── escalar_cantidad ────────────────────────────────────────────────────────
def test_escalar_none_devuelve_none():
    assert U.escalar_cantidad(None, 1.3, "gramos") is None


def test_escalar_gramos_redondea_a_multiplo_de_5():
    # 180 * 1.3 = 234 -> múltiplo de 5 más cercano = 235
    assert U.escalar_cantidad(180, 1.3, "gramos") == 235


def test_escalar_gramos_minimo_5():
    # cantidades muy pequeñas nunca bajan de 5
    assert U.escalar_cantidad(100, 0.01, "g") == 5


@pytest.mark.parametrize("unidad", ["gramos", "gr", "g", "ml", "mililitros"])
def test_escalar_unidades_de_peso_volumen(unidad):
    assert U.escalar_cantidad(200, 1.0, unidad) == 200


def test_escalar_piezas_redondea_a_cuartos():
    # 1 pieza * 1.3 = 1.3 -> a 1/4 más cercano = 1.25
    assert U.escalar_cantidad(1, 1.3, "pieza") == 1.25


# ── coincide_no_deseado ─────────────────────────────────────────────────────
def test_coincide_devuelve_palabra_original():
    assert U.coincide_no_deseado("Pollo con crema", ["Crema"]) == "Crema"


def test_coincide_sin_match_devuelve_none():
    assert U.coincide_no_deseado("Bistec de res", ["pollo"]) is None


def test_coincide_ignora_acentos_y_mayusculas():
    assert U.coincide_no_deseado("Sopa de FRIJÓL", ["frijol"]) == "frijol"


def test_coincide_ignora_no_deseados_vacios():
    assert U.coincide_no_deseado("Pollo", ["", "  "]) is None
