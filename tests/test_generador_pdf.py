# -*- coding: utf-8 -*-
"""Tests del exportador PDF."""

from nutridietas.nucleo.modelos import CeldaDieta, Ingrediente, Platillo
from nutridietas.salida import generador_pdf


def test_celda_contenido_pdf_respeta_factor_de_la_celda():
    platillo = Platillo(
        "p1",
        "Pollo",
        "comida",
        [Ingrediente("Pechuga de pollo", 100, "gramos")],
    )

    parrafos = generador_pdf._celda_contenido(
        CeldaDieta(platillo=platillo, factor=1.5),
        factor=1.0,
    )

    textos = "\n".join(p.getPlainText() for p in parrafos)
    assert "Pechuga de pollo (150 gramos)" in textos
