# -*- coding: utf-8 -*-
"""Tests de carga de plantillas Word."""

from docx import Document

from nutridietas.nucleo import plantillas_word
from nutridietas.nucleo.catalogo import Catalogo
from nutridietas.nucleo.modelos import Platillo


def _crear_docx(tmp_path):
    ruta = tmp_path / "plantilla.docx"
    doc = Document()
    tabla = doc.add_table(rows=3, cols=6)
    encabezados = ["", "Desayuno", "Colación 1", "Comida", "Colación 2", "Cena"]
    for i, texto in enumerate(encabezados):
        tabla.rows[0].cells[i].text = texto

    tabla.rows[1].cells[0].text = "Lunes"
    tabla.rows[1].cells[1].text = "Lonche de huevo\n• Huevo entero (1 pieza)"
    tabla.rows[1].cells[2].text = "Jicama rayada\n(1 taza)"
    tabla.rows[1].cells[3].text = "Pollo asado\n• Pollo (90 gr)"
    tabla.rows[1].cells[4].text = ""
    tabla.rows[1].cells[5].text = "Atún\n• Atún en agua (1 lata)"

    tabla.rows[2].cells[0].text = "Martes"
    tabla.rows[2].cells[1].text = ""
    tabla.rows[2].cells[2].text = "Manzana picada\n(1 taza)\n+\nAlmendras\n(10 piezas)"
    tabla.rows[2].cells[3].text = ""
    tabla.rows[2].cells[4].text = ""
    tabla.rows[2].cells[5].text = ""

    doc.save(ruta)
    return ruta


def test_cargar_word_llena_celdas_y_agrega_faltantes(tmp_path):
    catalogo = Catalogo(ruta=str(tmp_path / "catalogo.json"))
    catalogo.platillos = [
        Platillo("lonche_de_huevo", "Lonche de huevo", "desayuno", []),
    ]

    resultado = plantillas_word.cargar(str(_crear_docx(tmp_path)), catalogo)

    assert resultado.celdas["Lunes"][0]["titulo"] == "Lonche de huevo"
    assert resultado.celdas["Lunes"][0]["ingredientes"] == ["Huevo entero (1 pieza)"]
    assert resultado.celdas["Lunes"][1]["titulo"] == "Jicama rayada"
    assert resultado.celdas["Lunes"][1]["ingredientes"] == ["Jicama rayada (1 taza)"]
    assert resultado.celdas["Martes"][1]["titulo"] == "Manzana picada"
    assert resultado.celdas["Martes"][1]["ingredientes"] == [
        "Manzana picada (1 taza)",
        "Almendras (10 piezas)",
    ]

    agregados = {(p.nombre, p.tiempo) for p in resultado.agregados}
    assert ("Jicama rayada", "colacion") in agregados
    assert ("Pollo asado", "comida") in agregados
    assert ("Lonche de huevo", "desayuno") not in agregados

    catalogo_recargado = Catalogo(ruta=str(tmp_path / "catalogo.json"))
    assert any(p.nombre == "Jicama rayada" for p in catalogo_recargado.platillos)


def test_cargar_word_deja_vacia_celda_con_restriccion(tmp_path):
    catalogo = Catalogo(ruta=str(tmp_path / "catalogo.json"))

    resultado = plantillas_word.cargar(
        str(_crear_docx(tmp_path)),
        catalogo,
        restricciones=["pollo"],
    )

    assert resultado.celdas["Lunes"][2] == {}
    assert resultado.conflictos[0]["dia"] == "Lunes"
    assert resultado.conflictos[0]["restriccion"] == "pollo"
