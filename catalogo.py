# -*- coding: utf-8 -*-
"""
catalogo.py
===========
Administra el catalogo de platillos (la "base de datos" de recetas).

  - cargar() lee el JSON y devuelve una lista de objetos Platillo.
  - por_tiempo() filtra los platillos de un tiempo de comida.
  - aptos_para() devuelve los platillos que NO contienen alimentos no deseados.
  - agregar_platillo() / guardar() permiten ampliar el catalogo desde la app.
"""

import json
import os
from typing import List

import config
from modelos import Platillo, Ingrediente


class Catalogo:
    def __init__(self, ruta=None):
        self.ruta = ruta or config.RUTA_CATALOGO
        self.platillos: List[Platillo] = []
        self.cargar()

    # ----------------------------------------------------------------- #
    def cargar(self):
        if not os.path.exists(self.ruta):
            self.platillos = []
            return
        with open(self.ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.platillos = []
        ids_vistos    = set()   # deduplicación: evita IDs repetidos
        claves_vistas = set()   # deduplicación: evita (nombre, tiempo) repetidos
        for idx, p in enumerate(data.get("platillos", [])):
            nombre = p.get("nombre", "").strip()
            if not nombre:
                continue   # entrada sin nombre → saltar
            tiempo = p.get("tiempo", "comida")
            pid    = p.get("id", "").strip()
            if not pid:
                # generar ID desde el nombre si está vacío
                from utilidades import normalizar
                pid = normalizar(nombre).replace(" ", "_")[:60] or f"platillo_{idx}"
            # Un mismo nombre puede existir en distintos tiempos (p.ej. un
            # platillo que sirve para comida y cena), por eso la clave incluye
            # el tiempo. Solo se descarta el duplicado exacto (nombre + tiempo).
            clave = (nombre.lower(), tiempo)
            if clave in claves_vistas:
                continue   # duplicado exacto → saltar silenciosamente
            # garantizar ID único (nunca vacío, nunca repetido)
            pid_u, cnt = pid, 0
            while not pid_u or pid_u in ids_vistos:
                cnt += 1
                pid_u = f"{pid}_{cnt}" if pid else f"platillo_{idx}_{cnt}"
            ids_vistos.add(pid_u)
            claves_vistas.add(clave)
            ings = [
                Ingrediente(
                    nombre=i["nombre"],
                    cantidad=i.get("cantidad"),
                    unidad=i.get("unidad", ""),
                    texto_libre=i.get("texto_libre"),
                )
                for i in p.get("ingredientes", [])
            ]
            self.platillos.append(
                Platillo(
                    id    = pid_u,
                    nombre= nombre,
                    tiempo= tiempo,
                    ingredientes = ings,
                    video = p.get("video", False),
                    nota  = p.get("nota"),
                )
            )

    # ----------------------------------------------------------------- #
    def guardar(self):
        data = {"platillos": []}
        for p in self.platillos:
            data["platillos"].append({
                "id": p.id,
                "nombre": p.nombre,
                "tiempo": p.tiempo,
                "video": p.video,
                "nota": p.nota,
                "ingredientes": [
                    {k: v for k, v in {
                        "nombre": i.nombre,
                        "cantidad": i.cantidad,
                        "unidad": i.unidad,
                        "texto_libre": i.texto_libre,
                    }.items() if v is not None or k in ("cantidad", "unidad")}
                    for i in p.ingredientes
                ],
            })
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ----------------------------------------------------------------- #
    def por_tiempo(self, tiempo) -> List[Platillo]:
        return [p for p in self.platillos if p.tiempo == tiempo]

    def aptos_para(self, tiempo, no_deseados) -> List[Platillo]:
        """Platillos de un tiempo que el paciente SI puede comer."""
        return [p for p in self.por_tiempo(tiempo)
                if p.es_aceptable(no_deseados) is None]

    def aptos_para_todos(self, tiempo, lista_no_deseados) -> List[Platillo]:
        """
        Platillos de un tiempo aptos para TODOS (uso en dietas de grupo).
        lista_no_deseados es una lista de listas (una por paciente).
        """
        resultado = []
        for p in self.por_tiempo(tiempo):
            apto = all(p.es_aceptable(nd) is None for nd in lista_no_deseados)
            if apto:
                resultado.append(p)
        return resultado

    def agregar_platillo(self, platillo: Platillo):
        self.platillos.append(platillo)

    def buscar(self, texto) -> List[Platillo]:
        from utilidades import normalizar
        t = normalizar(texto)
        return [p for p in self.platillos if t in normalizar(p.nombre)]
