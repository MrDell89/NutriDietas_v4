# -*- coding: utf-8 -*-
"""Tests de catalogo.py: carga, deduplicación y consultas."""

import json

from catalogo import Catalogo


def _escribir_catalogo(tmp_path, platillos):
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(json.dumps({"platillos": platillos}, ensure_ascii=False),
                    encoding="utf-8")
    return str(ruta)


def test_carga_basica(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Avena", "tiempo": "desayuno", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert len(c.platillos) == 1
    assert c.platillos[0].nombre == "Avena"


def test_entrada_sin_nombre_se_ignora(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "x", "nombre": "  ", "tiempo": "comida", "ingredientes": []},
        {"id": "y", "nombre": "Sopa", "tiempo": "comida", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert [p.nombre for p in c.platillos] == ["Sopa"]


def test_id_se_genera_si_falta(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"nombre": "Pollo Asado", "tiempo": "comida", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert c.platillos[0].id == "pollo_asado"


def test_dedup_mismo_nombre_mismo_tiempo_descarta(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Pollo", "tiempo": "comida", "ingredientes": []},
        {"id": "b", "nombre": "pollo", "tiempo": "comida", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert len(c.platillos) == 1


def test_dedup_mismo_nombre_distinto_tiempo_conserva_ambos(tmp_path):
    # Regresión del bug corregido: antes se perdía el segundo platillo.
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Pollo", "tiempo": "comida", "ingredientes": []},
        {"id": "b", "nombre": "Pollo", "tiempo": "cena", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert len(c.platillos) == 2
    assert {p.tiempo for p in c.platillos} == {"comida", "cena"}


def test_ids_duplicados_se_hacen_unicos(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "dup", "nombre": "Plato A", "tiempo": "comida", "ingredientes": []},
        {"id": "dup", "nombre": "Plato B", "tiempo": "cena", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    ids = [p.id for p in c.platillos]
    assert len(ids) == len(set(ids))  # todos únicos


def test_por_tiempo_y_aptos_para(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Avena", "tiempo": "desayuno",
         "ingredientes": [{"nombre": "Leche"}]},
        {"id": "b", "nombre": "Fruta", "tiempo": "desayuno", "ingredientes": []},
        {"id": "c", "nombre": "Sopa", "tiempo": "comida", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert {p.nombre for p in c.por_tiempo("desayuno")} == {"Avena", "Fruta"}
    # quien no tolera leche no debe recibir la Avena
    aptos = c.aptos_para("desayuno", ["leche"])
    assert {p.nombre for p in aptos} == {"Fruta"}


def test_aptos_para_todos(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Avena", "tiempo": "desayuno",
         "ingredientes": [{"nombre": "Leche"}]},
        {"id": "b", "nombre": "Fruta", "tiempo": "desayuno", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    # un paciente evita leche, otro evita fruta → solo queda lo que sirve a todos
    aptos = c.aptos_para_todos("desayuno", [["leche"], ["fruta"]])
    assert aptos == []


def test_buscar_ignora_acentos(tmp_path):
    ruta = _escribir_catalogo(tmp_path, [
        {"id": "a", "nombre": "Frijoles Charros", "tiempo": "comida", "ingredientes": []},
    ])
    c = Catalogo(ruta=ruta)
    assert len(c.buscar("frijol")) == 1
