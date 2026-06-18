# -*- coding: utf-8 -*-
"""
modelos.py
==========
Define las "piezas" de informacion con las que trabaja el programa, usando
dataclasses (clases de datos sencillas):

  - Ingrediente : un alimento con su cantidad y unidad (escalable).
  - Platillo    : una receta (nombre, tiempo de comida, lista de ingredientes).
  - Paciente    : datos de la persona + sus alimentos no deseados + factor de
                  porcion (para dietas en grupo).
  - CeldaDieta  : el contenido de una celda (un platillo ya con sus porciones).
  - PlanSemanal : la dieta completa de una semana (7 dias x 5 tiempos).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict

from nutridietas.nucleo import utilidades as U
from nutridietas.nucleo import detector_ingredientes


# --------------------------------------------------------------------------- #
@dataclass
class Ingrediente:
    nombre: str
    cantidad: Optional[float] = None     # None = "al gusto" o cantidad libre
    unidad: str = ""
    texto_libre: Optional[str] = None    # para porciones irregulares ("1/2 lata o 3/4 lata")

    def render(self, factor: float = 1.0) -> str:
        """Devuelve el texto del ingrediente, escalando la cantidad por factor."""
        if self.texto_libre:
            return f"{self.nombre} ({self.texto_libre})"
        if self.cantidad is None:
            return self.nombre
        cant = U.escalar_cantidad(self.cantidad, factor, self.unidad)
        cant_txt = U.cantidad_a_texto(cant)
        if self.unidad:
            return f"{self.nombre} ({cant_txt} {self.unidad})"
        return f"{self.nombre} ({cant_txt})"


# --------------------------------------------------------------------------- #
@dataclass
class Platillo:
    id: str
    nombre: str
    tiempo: str                          # desayuno | colacion | comida | cena
    ingredientes: List[Ingrediente] = field(default_factory=list)
    video: bool = False
    nota: Optional[str] = None           # nota en cursiva al final de la celda

    def palabras_ingredientes(self) -> List[str]:
        """Lista de nombres de ingredientes (para detectar no deseados)."""
        return [i.nombre for i in self.ingredientes]

    def es_aceptable(self, no_deseados: List[str]) -> Optional[str]:
        """
        Devuelve None si el platillo es apto para el paciente, o la palabra
        que choca con sus alimentos no deseados.
        """
        conflicto = detector_ingredientes.detectar_conflicto_platillo(
            self, no_deseados
        )
        return conflicto.restriccion if conflicto else None


# --------------------------------------------------------------------------- #
@dataclass
class Paciente:
    nombre: str
    carpeta: str = ""                    # ruta de su carpeta
    ficha: str = ""                      # ruta del .docx de informacion
    no_deseados: List[str] = field(default_factory=list)
    preferidos: List[str] = field(default_factory=list)
    alergias: str = ""
    factor_porcion: float = 1.0          # 1.0 = porciones base
    num_planes: int = 0                  # cuantas dietas tiene ya

    def __str__(self):
        extra = f" | evita: {', '.join(self.no_deseados)}" if self.no_deseados else ""
        return f"{self.nombre}{extra}"

    def restricciones_alimentarias(self) -> List[str]:
        """Alimentos a excluir por disgusto, alergia o intolerancia."""
        return detector_ingredientes.preparar_restricciones(
            self.no_deseados,
            self.alergias,
        )

    def restricciones_a_revisar(self) -> List[str]:
        """Comentarios ambiguos que deben revisarse manualmente."""
        return detector_ingredientes.preparar_revisiones(
            self.no_deseados,
            self.alergias,
        )


# --------------------------------------------------------------------------- #
@dataclass
class CeldaDieta:
    """Lo que va dentro de una celda: un platillo y el factor de porcion."""
    platillo: Optional[Platillo] = None
    factor: float = 1.0
    texto_especial: Optional[str] = None   # ej. "Comida libre"

    def lineas(self):
        """Devuelve (titulo, lista_de_ingredientes, nota) ya renderizados."""
        if self.texto_especial:
            return (self.texto_especial, [], None)
        if not self.platillo:
            return ("", [], None)
        titulo = self.platillo.nombre
        if self.platillo.video:
            titulo += " (Video)"
        ingredientes = [ing.render(self.factor) for ing in self.platillo.ingredientes]
        return (titulo, ingredientes, self.platillo.nota)


# --------------------------------------------------------------------------- #
@dataclass
class PlanSemanal:
    """Una dieta semanal completa para un paciente."""
    paciente: Paciente
    numero_plan: int                       # 1, 2, 3...
    notas_superiores: List[str] = field(default_factory=list)
    # estructura: celdas[dia][indice_columna] = CeldaDieta
    celdas: Dict[str, List[CeldaDieta]] = field(default_factory=dict)

    def titulo(self):
        ordinales = {
            1: "1er", 2: "2do", 3: "3er", 4: "4to", 5: "5to", 6: "6to",
            7: "7mo", 8: "8vo", 9: "9no", 10: "10mo",
        }
        ord_txt = ordinales.get(self.numero_plan, f"{self.numero_plan}º")
        return f"{ord_txt} Plan alimenticio: {self.paciente.nombre}"

    def nombre_archivo(self):
        seguro = self.paciente.nombre.replace(" ", "_")
        return f"{self.numero_plan}_Plan_alimenticio_{seguro}.docx"
