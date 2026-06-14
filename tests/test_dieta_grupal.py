# -*- coding: utf-8 -*-
"""Tests de dieta_grupal.py: mismo menú para el grupo, porciones distintas."""

from nutridietas import config
from nutridietas.nucleo import dieta_grupal as dg
from nutridietas.nucleo.catalogo import Catalogo
from nutridietas.nucleo.modelos import Platillo, Paciente, Ingrediente


def _catalogo():
    c = Catalogo(ruta="__inexistente__.json")
    c.platillos = [
        Platillo("d1", "Avena", "desayuno", [Ingrediente("Leche", 200, "ml")]),
        Platillo("d2", "Fruta", "desayuno", []),
        Platillo("c1", "Nuez", "colacion", []),
        Platillo("m1", "Pollo", "comida", []),
        Platillo("n1", "Ensalada", "cena", []),
    ]
    return c


def test_comparar_gustos_union_de_no_deseados():
    g = [Paciente("Ana", no_deseados=["leche"]),
         Paciente("Beto", no_deseados=["nuez"])]
    rep = dg.comparar_gustos(g, _catalogo())
    assert rep["no_deseados_union"] == {"leche", "nuez"}


def test_comparar_gustos_comunes_excluye_lo_que_choca_con_alguien():
    g = [Paciente("Ana", no_deseados=["leche"]), Paciente("Beto")]
    rep = dg.comparar_gustos(g, _catalogo())
    desayunos = {p.nombre for p in rep["comunes"]["desayuno"]}
    assert "Avena" not in desayunos  # choca con Ana
    assert "Fruta" in desayunos


def test_comparar_gustos_reporta_conflicto_con_quien():
    g = [Paciente("Ana", no_deseados=["leche"]), Paciente("Beto")]
    rep = dg.comparar_gustos(g, _catalogo())
    conflictos = {p.nombre: choca for p, choca in rep["conflictos"]}
    assert "Avena" in conflictos
    assert ("Ana", "leche") in conflictos["Avena"]


def test_construir_grupo_mismo_menu_distinta_porcion():
    g = [Paciente("Ana", factor_porcion=1.0),
         Paciente("Beto", factor_porcion=1.5)]
    resultado = dg.construir_grupo(g, _catalogo(), numero_plan=1)
    assert len(resultado) == 2
    (pac_a, plan_a), (pac_b, plan_b) = resultado

    # mismo menú: mismos platillos por día/columna
    for dia in config.DIAS:
        nombres_a = [c.platillo.nombre if c and c.platillo else None
                     for c in plan_a.celdas[dia]]
        nombres_b = [c.platillo.nombre if c and c.platillo else None
                     for c in plan_b.celdas[dia]]
        assert nombres_a == nombres_b

    # distinta porción: el factor de cada celda corresponde a su paciente
    assert plan_a.celdas["Lunes"][0].factor == 1.0
    assert plan_b.celdas["Lunes"][0].factor == 1.5


def test_construir_grupo_agrega_nota_de_grupo():
    g = [Paciente("Ana"), Paciente("Beto")]
    (_, plan_a), _ = dg.construir_grupo(g, _catalogo(), numero_plan=1)
    assert any("grupo" in n.lower() for n in plan_a.notas_superiores)
