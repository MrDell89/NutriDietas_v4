# -*- coding: utf-8 -*-
"""
utilidades.py
=============
Funciones de apoyo que usan varios modulos:

  - normalizar(): quita acentos y mayusculas para poder comparar textos
    (por ejemplo "Sardinas" contra "sardina") sin importar como se escribieron.
  - cantidad_a_texto(): convierte un numero (0.5, 1.5, 4) en una cadena
    legible con fracciones ("1/2", "1 1/2", "4").
  - escalar_cantidad(): multiplica una porcion por un factor y la redondea
    de forma sensata segun la unidad (gramos vs piezas/tazas).
"""

import unicodedata
from fractions import Fraction


def normalizar(texto):
    """Pasa a minusculas y elimina acentos. Sirve para comparar palabras."""
    if texto is None:
        return ""
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


def cantidad_a_texto(valor):
    """
    Convierte un numero a texto con fracciones comunes.
      0.5  -> "1/2"      0.25 -> "1/4"     0.75 -> "3/4"
      1.5  -> "1 1/2"    2    -> "2"       3.33 -> "3 1/3"
    """
    if valor is None:
        return ""
    # Numero entero exacto
    if abs(valor - round(valor)) < 1e-6:
        return str(int(round(valor)))

    entero = int(valor)
    decimal = valor - entero
    # Buscamos la fraccion comun mas cercana (denominador hasta 4 o 3)
    frac = Fraction(decimal).limit_denominator(4)
    if frac == 0:
        return str(entero)
    parte_frac = f"{frac.numerator}/{frac.denominator}"
    if entero > 0:
        return f"{entero} {parte_frac}"
    return parte_frac


def escalar_cantidad(valor, factor, unidad):
    """
    Escala una porcion por un factor (p.ej. 1.2 = 20% mas) y redondea
    de manera razonable:
      - gramos / ml: al multiplo de 5 mas cercano.
      - piezas, tazas, cucharadas, etc.: a 1/4 mas cercano.
    """
    if valor is None:
        return None
    escalado = valor * factor
    u = normalizar(unidad)
    if u in ("gramos", "gr", "g", "ml", "mililitros"):
        return max(5, int(round(escalado / 5.0)) * 5)
    # Para piezas/tazas redondeamos a cuartos
    return round(escalado * 4) / 4.0


def coincide_no_deseado(texto_ingrediente, lista_no_deseados):
    """
    Devuelve la palabra que coincide si el ingrediente contiene algun
    alimento no deseado; si no, devuelve None.
    """
    ing = normalizar(texto_ingrediente)
    for no in lista_no_deseados:
        n = normalizar(no)
        if n and n in ing:
            return no
    return None
