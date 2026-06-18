# -*- coding: utf-8 -*-
"""
pacientes.py
============
Lee la estructura de carpetas de pacientes tal como la maneja el nutriologo:

    Pacientes/
        19 Raymundo/
            Raymundo.docx                         <- ficha (informacion)
            1er 3 Plan alimenticio Raymundo.docx  <- dieta semana 1
            2do 4to Plan alimenticio Raymundo.docx<- dieta semana 2
            ...

Reglas:
  - El archivo de FICHA es el .docx cuyo nombre NO contiene "plan alimenticio".
  - Los archivos de DIETA contienen "plan alimenticio".
De la ficha se extraen automaticamente los "alimentos que no le agradan".
"""

import logging
import os
import re
from typing import List

from nutridietas import config
from nutridietas.nucleo import utilidades as U
from nutridietas.nucleo.modelos import Paciente

log = logging.getLogger(__name__)

try:
    import docx  # python-docx
except ImportError:
    docx = None


# --------------------------------------------------------------------------- #
def _texto_completo_docx(ruta) -> str:
    """Devuelve TODO el texto de un .docx (parrafos + celdas de tablas)."""
    if docx is None:
        log.warning("python-docx no esta instalado; no se puede leer %s", ruta)
        return ""
    try:
        d = docx.Document(ruta)
    except Exception:
        log.warning("No se pudo leer el .docx: %s", ruta, exc_info=True)
        return ""
    partes = [p.text for p in d.paragraphs]
    for tabla in d.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                partes.append(celda.text)
    return "\n".join(partes)


def _extraer_lista(texto, etiqueta) -> List[str]:
    """
    Busca una linea tipo 'Etiqueta: a, b, c' y devuelve [a, b, c] ya limpios.
    """
    norm = U.normalizar(texto)
    et = U.normalizar(etiqueta)
    idx = norm.find(et)
    if idx == -1:
        return []
    # Tomamos el texto original a partir de la etiqueta
    # (buscamos la posicion equivalente en el texto sin normalizar)
    fragmento = texto[idx: idx + 400]
    # Cortamos a partir de los dos puntos
    if ":" in fragmento:
        fragmento = fragmento.split(":", 1)[1]
    # Cortamos en el siguiente salto de linea o etiqueta conocida
    fragmento = fragmento.split("\n")[0]
    # Separamos por comas y limpiamos palabras vacias / frases no útiles
    crudos = re.split(r"[,;]", fragmento)
    descartar = {"come de todo", "si", "no", "regular", "poquito", "poco", ""}
    items = []
    for c in crudos:
        c = c.strip(" .\t")
        if not c:
            continue
        if U.normalizar(c) in {U.normalizar(d) for d in descartar}:
            continue
        # quitamos colas tipo "en licuados si"
        items.append(c)
    return items


# --------------------------------------------------------------------------- #
def cargar_paciente(carpeta) -> Paciente:
    """Construye un objeto Paciente a partir de su carpeta."""
    nombre_carpeta = os.path.basename(carpeta.rstrip("/\\"))
    # quitamos el numero al inicio ("19 Raymundo" -> "Raymundo")
    nombre = re.sub(r"^\s*\d+\s*", "", nombre_carpeta).strip()

    ficha = ""
    num_planes = 0
    for archivo in os.listdir(carpeta):
        if not archivo.lower().endswith(".docx"):
            continue
        if archivo.startswith("~$"):
            continue
        if "plan alimenticio" in U.normalizar(archivo):
            num_planes += 1
        else:
            ficha = os.path.join(carpeta, archivo)

    paciente = Paciente(
        nombre=nombre or nombre_carpeta,
        carpeta=carpeta,
        ficha=ficha,
        num_planes=num_planes,
    )

    if ficha:
        texto = _texto_completo_docx(ficha)
        paciente.no_deseados = _extraer_lista(texto, config.ETIQUETA_NO_AGRADAN)
        paciente.preferidos = _extraer_lista(texto, config.ETIQUETA_PREFERIDOS)
        paciente.alergias = ", ".join(
            _extraer_lista(texto, config.ETIQUETA_ALERGIAS)
        )
        # nombre real desde la ficha si aparece
        m = re.search(r"Nombre:\s*\n?\s*([^\n]+)", texto)
        if m and m.group(1).strip():
            posible = m.group(1).strip()
            if len(posible) > 2 and not posible.lower().startswith("edad"):
                paciente.nombre = posible

    return paciente


def listar_pacientes() -> List[Paciente]:
    """Devuelve todos los pacientes encontrados en CARPETA_PACIENTES."""
    base = config.CARPETA_PACIENTES
    if not os.path.isdir(base):
        return []
    pacientes = []
    for nombre in sorted(os.listdir(base), key=_clave_orden):
        ruta = os.path.join(base, nombre)
        if os.path.isdir(ruta):
            pacientes.append(cargar_paciente(ruta))
    return pacientes


def _clave_orden(nombre):
    """Ordena por el numero inicial de la carpeta si existe."""
    m = re.match(r"\s*(\d+)", nombre)
    return (0, int(m.group(1))) if m else (1, nombre.lower())
