# -*- coding: utf-8 -*-
"""Detector de ingredientes conflictivos para pacientes."""

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from nutridietas.nucleo import utilidades as U


DESCARTAR_RESTRICCIONES = {
    "",
    "n/a",
    "na",
    "no",
    "ninguna",
    "ninguno",
    "sin alergias",
    "no alergias",
    "no aplica",
    "come de todo",
    "todo",
}

PREFIJOS_RESTRICCION = (
    "alergico a",
    "alergica a",
    "alergia a",
    "intolerante a",
    "intolerancia a",
    "no tolera",
    "no le gusta",
    "no le agradan",
    "evita",
)


@dataclass
class ConflictoIngrediente:
    restriccion: str
    encontrado_en: str
    origen: str


def preparar_restricciones(*valores) -> List[str]:
    """Normaliza entradas de disgustos/alergias en una lista limpia."""
    resultado = []
    vistos = set()
    for valor in valores:
        for item in _aplanar(valor):
            item = _limpiar_restriccion(item)
            if not item:
                continue
            clave = U.normalizar(item)
            if clave in DESCARTAR_RESTRICCIONES or clave in vistos:
                continue
            vistos.add(clave)
            resultado.append(item)
    return resultado


def detectar_en_texto(texto, restricciones) -> Optional[str]:
    """Devuelve la primera restriccion que aparece como palabra/frase real."""
    tokens_texto = _tokens(texto)
    if not tokens_texto:
        return None
    for restriccion in preparar_restricciones(restricciones):
        if _coincide_tokens(tokens_texto, _tokens(restriccion)):
            return restriccion
    return None


def detectar_conflicto_platillo(platillo, restricciones) -> Optional[ConflictoIngrediente]:
    """Busca restricciones en nombre e ingredientes del platillo."""
    fuentes = [("nombre", platillo.nombre)]
    fuentes.extend(("ingrediente", ing.nombre) for ing in platillo.ingredientes)
    for origen, texto in fuentes:
        restriccion = detectar_en_texto(texto, restricciones)
        if restriccion:
            return ConflictoIngrediente(
                restriccion=restriccion,
                encontrado_en=texto,
                origen=origen,
            )
    return None


def _aplanar(valor) -> Iterable[str]:
    if valor is None:
        return []
    if isinstance(valor, str):
        return _separar_texto(valor)
    try:
        partes = []
        for item in valor:
            partes.extend(_aplanar(item))
        return partes
    except TypeError:
        return [str(valor)]


def _separar_texto(texto) -> List[str]:
    texto = texto.replace("•", "\n")
    partes = re.split(r"[\n,;]+", texto)
    resultado = []
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        resultado.extend(p.strip() for p in re.split(r"\s+y\s+", parte) if p.strip())
    return resultado


def _limpiar_restriccion(texto) -> str:
    limpio = re.sub(r"\s+", " ", str(texto)).strip(" .\t:-")
    normalizado = U.normalizar(limpio)
    for prefijo in PREFIJOS_RESTRICCION:
        if normalizado.startswith(prefijo + " "):
            limpio = " ".join(limpio.split()[len(prefijo.split()):])
            limpio = limpio.strip(" .\t:-")
            break
    return limpio


def _tokens(texto) -> List[str]:
    return re.findall(r"[a-z0-9]+", U.normalizar(texto))


def _coincide_tokens(tokens_texto, tokens_buscados) -> bool:
    if not tokens_buscados:
        return False
    n = len(tokens_buscados)
    for i in range(0, len(tokens_texto) - n + 1):
        ventana = tokens_texto[i:i + n]
        if all(_token_equivale(a, b) for a, b in zip(ventana, tokens_buscados)):
            return True
    return False


def _token_equivale(texto, buscado) -> bool:
    return texto == buscado or _singular(texto) == _singular(buscado)


def _singular(token):
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token
