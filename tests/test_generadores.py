# -*- coding: utf-8 -*-
"""Tests de generadores.py: fachada que elige el formato de salida."""

import generadores
from modelos import Paciente


def test_extension():
    assert generadores.extension("pdf") == ".pdf"
    assert generadores.extension("docx") == ".docx"
    assert generadores.extension("cualquier_otra_cosa") == ".docx"


def _grabador(registro, clave, retorno):
    """Crea un stub que registra que fue llamado y devuelve `retorno`."""
    def stub(plan, ruta_salida=None):
        registro[clave] = {"plan": plan, "ruta": ruta_salida}
        return retorno
    return stub


def test_generar_despacha_a_docx(monkeypatch):
    reg = {}
    monkeypatch.setattr(generadores.generador_docx, "generar",
                        _grabador(reg, "docx", "ruta.docx"))
    monkeypatch.setattr(generadores.generador_pdf, "generar",
                        _grabador(reg, "pdf", "ruta.pdf"))
    ruta = generadores.generar(object(), formato="docx", ruta_salida="x.docx")
    assert ruta == "ruta.docx"
    assert "docx" in reg and "pdf" not in reg
    assert reg["docx"]["ruta"] == "x.docx"


def test_generar_despacha_a_pdf(monkeypatch):
    reg = {}
    monkeypatch.setattr(generadores.generador_docx, "generar",
                        _grabador(reg, "docx", "ruta.docx"))
    monkeypatch.setattr(generadores.generador_pdf, "generar",
                        _grabador(reg, "pdf", "ruta.pdf"))
    ruta = generadores.generar(object(), formato="pdf", ruta_salida="x.pdf")
    assert ruta == "ruta.pdf"
    assert "pdf" in reg and "docx" not in reg


def test_generar_desde_celdas_manual_arma_y_despacha(monkeypatch):
    reg = {}
    monkeypatch.setattr(generadores.generador_docx, "generar",
                        _grabador(reg, "docx", "ok.docx"))
    cm = {"Lunes": [{"titulo": "Avena", "ingredientes": ["Hojuelas"]}]}
    ruta = generadores.generar_desde_celdas_manual(
        Paciente("Ana"), cm, numero_plan=1, formato="docx")
    assert ruta == "ok.docx"
    # el plan armado llegó al generador con la celda esperada
    plan = reg["docx"]["plan"]
    assert plan.celdas["Lunes"][0].platillo.nombre == "Avena"
