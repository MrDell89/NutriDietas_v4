# -*- coding: utf-8 -*-
"""
config.py
=========
Configuracion central de la aplicacion. Aqui se definen:
  - Rutas de trabajo (carpeta de pacientes, salidas, recursos).
  - Colores, fuentes y medidas EXACTAS tomadas del formato Word original
    del Lic. Juan Pablo Espino, para que las dietas generadas se vean idénticas.
  - La estructura de comidas (columnas) y los dias de la semana.

Todo lo "ajustable" del programa vive aqui para no tener que tocar el resto
de los modulos.
"""

import os

# --------------------------------------------------------------------------- #
#  RUTAS
# --------------------------------------------------------------------------- #
# Carpeta raiz donde estan las carpetas de cada paciente.
# Por defecto se usa la carpeta "Pacientes" junto a este archivo, pero puede
# cambiarse a la ruta real de OneDrive del nutriologo, por ejemplo:
#   CARPETA_PACIENTES = r"C:\Users\Juan\OneDrive\Pacientes"
DIR_BASE = os.path.dirname(os.path.abspath(__file__))           # carpeta del paquete
RAIZ_PROYECTO = os.path.dirname(DIR_BASE)                        # raiz del repositorio
CARPETA_PACIENTES = os.path.join(RAIZ_PROYECTO, "Pacientes")

# Carpeta donde se guardan las dietas generadas por la app.
CARPETA_SALIDAS = os.path.join(RAIZ_PROYECTO, "salidas")

# Recursos (logo, etc.)
CARPETA_RECURSOS = os.path.join(RAIZ_PROYECTO, "recursos")
RUTA_LOGO = os.path.join(CARPETA_RECURSOS, "logo.png")

# Catalogo de platillos (base de datos en JSON).
RUTA_CATALOGO = os.path.join(RAIZ_PROYECTO, "datos", "catalogo_platos.json")

# Firma que aparece al pie de cada dieta.
FIRMA = "Lic. Nutrición. Juan Pablo Espino"

# --------------------------------------------------------------------------- #
#  PALETA DE COLORES  (única fuente de verdad)
# --------------------------------------------------------------------------- #
# Los valores se guardan en hexadecimal SIN '#', tal como los necesita
# python-docx (RGBColor.from_string). Para Tkinter o reportlab, que requieren
# el prefijo '#', usa el helper ui() de abajo, p.ej.:
#     fondo = config.ui(config.COLOR_VERDE_ENCABEZADO)   # -> "#1AA27E"
#
# Colores del documento original (Word/PDF):
COLOR_VERDE_ENCABEZADO = "1AA27E"   # fondo de cabeceras y columna de dias
COLOR_VERDE_TITULO     = "072F25"   # titulos y nombres de platillos
COLOR_TEXTO            = "0D0D0D"    # texto normal (casi negro)
COLOR_NOTA             = "385623"    # notas en verde oscuro
COLOR_BLANCO           = "FFFFFF"
COLOR_BORDE            = "000000"    # borde de tabla (negro)

# Colores adicionales de la interfaz gráfica (Tkinter):
COLOR_HOVER     = "148A6A"   # verde al pasar el mouse
COLOR_ACTIVE    = "0D6E55"   # verde al presionar
COLOR_FONDO     = "F4F7F6"   # fondo general de la app
COLOR_BORDE_UI  = "C4DDD6"   # bordes suaves de la UI
COLOR_TEXTO_TENUE = "6B8C82" # texto secundario / etiquetas
COLOR_ERROR     = "D9534F"   # mensajes de error
COLOR_SIDEBAR   = "0B5C46"   # barra lateral / encabezado oscuro
COLOR_ACENTO    = "E6F5EF"   # resaltados suaves y celdas "libre"


def ui(color_hex):
    """Devuelve el color con prefijo '#' para Tkinter / reportlab."""
    return "#" + color_hex

# --------------------------------------------------------------------------- #
#  TIPOGRAFIA
# --------------------------------------------------------------------------- #
FUENTE_PRINCIPAL = "Century Gothic"
TAM_TITULO      = 18    # puntos
TAM_NOTA_SUP    = 13
TAM_CABECERA    = 11
TAM_DIA         = 11
TAM_PLATILLO    = 11
TAM_INGREDIENTE = 9
TAM_FIRMA       = 11

# --------------------------------------------------------------------------- #
#  PAGINA  (en twips; 1440 twips = 1 pulgada). Carta horizontal.
# --------------------------------------------------------------------------- #
PAGINA_ANCHO   = 15840   # 11"
PAGINA_ALTO    = 12240   # 8.5"
MARGEN_SUP     = 227
MARGEN_INF     = 227
MARGEN_IZQ     = 567
MARGEN_DER     = 567

# Anchos de columna de la tabla (twips) — idénticos al original.
ANCHO_COL_DIA       = 1250
ANCHO_COL_DESAYUNO  = 3249
ANCHO_COL_COLACION1 = 2017
ANCHO_COL_COMIDA    = 3219
ANCHO_COL_COLACION2 = 2026
ANCHO_COL_CENA      = 3170

# --------------------------------------------------------------------------- #
#  ESTRUCTURA DE LA DIETA
# --------------------------------------------------------------------------- #
# Columnas de la tabla (en orden). La clave "tiempo" indica de que tipo de
# platillo se llena cada columna desde el catalogo.
COLUMNAS = [
    {"titulo": "Desayuno",   "tiempo": "desayuno", "ancho": ANCHO_COL_DESAYUNO},
    {"titulo": "Colación 1", "tiempo": "colacion", "ancho": ANCHO_COL_COLACION1},
    {"titulo": "Comida",     "tiempo": "comida",   "ancho": ANCHO_COL_COMIDA},
    {"titulo": "Colación 2", "tiempo": "colacion", "ancho": ANCHO_COL_COLACION2},
    {"titulo": "Cena",       "tiempo": "cena",     "ancho": ANCHO_COL_CENA},
]

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Texto que indica en la ficha del paciente la lista de alimentos no deseados.
ETIQUETA_NO_AGRADAN = "Alimentos que no le agradan"
ETIQUETA_PREFERIDOS = "Alimentos preferidos"
ETIQUETA_ALERGIAS   = "alérgico o intolerante"
ETIQUETA_NOMBRE     = "Nombre"
