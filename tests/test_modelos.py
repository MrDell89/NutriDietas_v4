# -*- coding: utf-8 -*-
"""Tests de modelos.py: render de ingredientes, aptitud de platillos y plan."""

from modelos import Ingrediente, Platillo, Paciente, CeldaDieta, PlanSemanal


# ── Ingrediente.render ──────────────────────────────────────────────────────
def test_render_sin_cantidad_solo_nombre():
    assert Ingrediente("Sal").render() == "Sal"


def test_render_con_cantidad_y_unidad():
    assert Ingrediente("Pollo", 150, "gramos").render(1.0) == "Pollo (150 gramos)"


def test_render_escala_por_factor():
    assert Ingrediente("Pollo", 150, "gramos").render(1.3) == "Pollo (195 gramos)"


def test_render_texto_libre_ignora_factor():
    ing = Ingrediente("Atún", texto_libre="1/2 lata o 3/4 lata")
    assert ing.render(2.0) == "Atún (1/2 lata o 3/4 lata)"


def test_render_cantidad_sin_unidad():
    assert Ingrediente("Huevo", 2).render(1.0) == "Huevo (2)"


# ── Platillo.es_aceptable ───────────────────────────────────────────────────
def test_es_aceptable_apto_devuelve_none():
    p = Platillo("p1", "Bistec", "comida", [Ingrediente("Res", 150, "gramos")])
    assert p.es_aceptable(["pollo"]) is None


def test_es_aceptable_detecta_en_nombre():
    p = Platillo("p1", "Sardinas a la mexicana", "comida", [])
    assert p.es_aceptable(["sardina"]) == "sardina"


def test_es_aceptable_detecta_en_ingrediente():
    p = Platillo("p1", "Ensalada", "comida", [Ingrediente("Crema", 30, "gramos")])
    assert p.es_aceptable(["crema"]) == "crema"


# ── CeldaDieta.lineas ───────────────────────────────────────────────────────
def test_celda_vacia():
    assert CeldaDieta().lineas() == ("", [], None)


def test_celda_texto_especial():
    assert CeldaDieta(texto_especial="Comida libre").lineas() == ("Comida libre", [], None)


def test_celda_con_platillo_video_agrega_etiqueta():
    p = Platillo("p1", "Hotcakes", "desayuno", [Ingrediente("Avena", 40, "gramos")],
                 video=True)
    titulo, ings, nota = CeldaDieta(platillo=p, factor=1.0).lineas()
    assert titulo == "Hotcakes (Video)"
    assert ings == ["Avena (40 gramos)"]
    assert nota is None


# ── PlanSemanal ─────────────────────────────────────────────────────────────
def _paciente():
    return Paciente(nombre="Juan Perez")


def test_titulo_usa_ordinal():
    plan = PlanSemanal(paciente=_paciente(), numero_plan=3)
    assert plan.titulo() == "3er Plan alimenticio: Juan Perez"


def test_titulo_ordinal_fuera_de_tabla():
    plan = PlanSemanal(paciente=_paciente(), numero_plan=11)
    assert plan.titulo() == "11º Plan alimenticio: Juan Perez"


def test_nombre_archivo_reemplaza_espacios():
    plan = PlanSemanal(paciente=_paciente(), numero_plan=2)
    assert plan.nombre_archivo() == "2_Plan_alimenticio_Juan_Perez.docx"
