# -*- coding: utf-8 -*-
"""Tests del detector de ingredientes conflictivos."""

from nutridietas.nucleo import detector_ingredientes as det
from nutridietas.nucleo.modelos import Ingrediente, Platillo, Paciente


def test_detecta_acentos_y_plural():
    assert det.detectar_en_texto("Tostadas de frijoles", ["frijol"]) == "frijol"


def test_no_detecta_subcadena_dentro_de_otra_palabra():
    assert det.detectar_en_texto("Fresas picadas", ["res"]) is None


def test_detecta_frase_completa():
    assert (
        det.detectar_en_texto("Pan con crema de cacahuate", ["crema de cacahuate"])
        == "crema de cacahuate"
    )


def test_prepara_restricciones_desde_texto_con_y():
    restricciones = det.preparar_restricciones("Alérgico a camarón y nuez")
    assert restricciones == ["camarón", "nuez"]


def test_detecta_conflicto_en_ingrediente():
    platillo = Platillo(
        "p1",
        "Ensalada",
        "comida",
        [Ingrediente("Atún en agua", 1, "lata")],
    )
    conflicto = det.detectar_conflicto_platillo(platillo, ["atun"])
    assert conflicto.restriccion == "atun"
    assert conflicto.origen == "ingrediente"


def test_paciente_combina_disgustos_y_alergias():
    paciente = Paciente("Ana", no_deseados=["pollo"], alergias="camarón, nuez")
    assert paciente.restricciones_alimentarias() == ["pollo", "camarón", "nuez"]
