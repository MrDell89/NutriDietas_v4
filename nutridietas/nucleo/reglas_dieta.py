# -*- coding: utf-8 -*-
"""Reglas compartidas para armar menus semanales."""

from nutridietas.nucleo import utilidades as U


PATRON_TRES_OPCIONES = {
    "Lunes": 0,
    "Martes": 1,
    "Miércoles": 2,
    "Jueves": 1,
    "Viernes": 0,
    "Sábado": 1,
    "Domingo": 2,
}


PROTEINAS_CLAVE = {
    "pollo": ("pollo",),
    "atun": ("atun",),
    "pescado": ("pescado", "filete de pescado"),
    "huevo": ("huevo", "clara de huevo"),
    "res": ("res", "bistec", "carne de res", "chuleta de res"),
    "cerdo": ("cerdo", "puerco", "lomo de cerdo", "chuleta de cerdo"),
    "jamon": ("jamon",),
    "pavo": ("pavo",),
    "camaron": ("camaron", "camarones"),
    "salmon": ("salmon",),
    "sardina": ("sardina", "sardinas"),
    "tilapia": ("tilapia",),
}


def proteinas_de_platillo(platillo):
    """Detecta proteinas principales desde nombre e ingredientes."""
    if platillo is None:
        return set()

    textos = [platillo.nombre]
    textos.extend(ing.nombre for ing in platillo.ingredientes)
    texto = U.normalizar(" ".join(textos))

    encontradas = set()
    for proteina, claves in PROTEINAS_CLAVE.items():
        if any(clave in texto for clave in claves):
            encontradas.add(proteina)
    return encontradas


def escoger_sin_repetir_proteina(lista, contador, proteinas_usadas,
                                 excluir=None):
    """
    Elige rotando, evitando platillos ya excluidos y proteinas usadas ese dia.
    """
    if not lista:
        return None, contador

    excluir = {_clave_platillo(p) for p in (excluir or [])}
    total = len(lista)
    for offset in range(total):
        idx = (contador + offset) % total
        platillo = lista[idx]
        if _clave_platillo(platillo) in excluir:
            continue
        proteinas = proteinas_de_platillo(platillo)
        if proteinas and proteinas & proteinas_usadas:
            continue
        return platillo, idx + 1
    return None, contador


def _clave_platillo(platillo):
    return getattr(platillo, "id", None) or id(platillo)


def escoger_patron_tres(lista, dia, patrones, proteinas_usadas):
    """
    Aplica el patron desayuno/cena:
    L-Mi son 3 opciones; jueves repite martes; viernes-domingo repiten L-Mi.
    """
    if not lista:
        return None

    patron_idx = PATRON_TRES_OPCIONES.get(dia)
    if patron_idx is None:
        return None

    if patron_idx in patrones:
        platillo = patrones[patron_idx]
        proteinas = proteinas_de_platillo(platillo)
        if proteinas and proteinas & proteinas_usadas:
            return None
        return platillo

    usados = list(patrones.values())
    platillo, _ = escoger_sin_repetir_proteina(
        lista,
        patron_idx,
        proteinas_usadas,
        excluir=usados,
    )
    if platillo is None:
        platillo, _ = escoger_sin_repetir_proteina(
            lista,
            patron_idx,
            proteinas_usadas,
        )
    if platillo is None:
        return None

    patrones[patron_idx] = platillo
    return platillo
