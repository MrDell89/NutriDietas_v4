# -*- coding: utf-8 -*-
"""Tests del extractor de planes alimenticios."""

from nutridietas.herramientas import extractor_planes_alimenticios as ext


def test_parsea_ingrediente_con_parentesis():
    ing = ext.parsear_ingrediente_texto("Manzana mediana (1 pieza)")
    assert ing == {"nombre": "Manzana mediana", "cantidad": 1, "unidad": "pieza"}


def test_parsea_ingrediente_sin_parentesis():
    ing = ext.parsear_ingrediente_texto("Jicama rayada 1 taza")
    assert ing == {"nombre": "Jicama rayada", "cantidad": 1, "unidad": "taza"}


def test_parsea_ingrediente_en_gramos_sin_parentesis():
    ing = ext.parsear_ingrediente_texto("frezas picadas 200 gramos")
    assert ing == {"nombre": "frezas picadas", "cantidad": 200, "unidad": "gramos"}


def test_parsea_fraccion_unicode_mixta():
    ing = ext.parsear_ingrediente_texto("Jícama picada (1 ½ taza)")
    assert ing == {"nombre": "Jícama picada", "cantidad": 1.5, "unidad": "taza"}


def test_parsea_fraccion_con_diagonal():
    ing = ext.parsear_ingrediente_texto("Zanahoria rallada (3/4 taza)")
    assert ing == {"nombre": "Zanahoria rallada", "cantidad": 0.75, "unidad": "taza"}
