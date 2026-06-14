# -*- coding: utf-8 -*-
"""
tabla_dieta.py
==============
Widget Tkinter reutilizable: tabla visual 6×8 (Día + 5 tiempos × 7 días)
con la misma estética del PDF/Word original.

Cada celda permite:
  - Seleccionar un platillo del catálogo (combobox)
  - Ver / editar sus ingredientes en texto libre
  - Marcar "Video" y agregar nota al pie
  - Limpiar la celda
  - Botón "Comida libre" para domingo

Uso:
    from tabla_dieta import TablaDieta
    t = TablaDieta(parent, catalogo, no_deseados=[...], factor=1.0)
    t.pack(fill="both", expand=True)
    # obtener datos:
    celdas = t.get_celdas()   # dict[dia] = list[dict]
    # cargar datos previos:
    t.set_celdas(celdas)
    # refrescar catálogo:
    t.refrescar_catalogo(catalogo)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional

import config

# colores tomados de la paleta central de config (con prefijo '#' para Tkinter)
_VERDE     = config.ui(config.COLOR_VERDE_ENCABEZADO)
_VERDE_OSC = config.ui(config.COLOR_VERDE_TITULO)
_HOVER     = config.ui(config.COLOR_HOVER)
_BG        = config.ui(config.COLOR_FONDO)
_WHITE     = config.ui(config.COLOR_BLANCO)
_BORDER    = config.ui(config.COLOR_BORDE_UI)
_TEXT      = config.ui(config.COLOR_TEXTO)
_MUTED     = config.ui(config.COLOR_TEXTO_TENUE)
_NOTA_C    = config.ui(config.COLOR_NOTA)
_LIBRE_BG  = config.ui(config.COLOR_ACENTO)

_FT_DIA    = ("Segoe UI", 9, "bold")
_FT_CAB    = ("Segoe UI", 9, "bold")
_FT_PLAT   = ("Segoe UI", 8, "bold")
_FT_ING    = ("Segoe UI", 8)
_FT_BTN    = ("Segoe UI", 8)
_FT_MONO   = ("Consolas", 8)

DIAS  = config.DIAS
COLS  = config.COLUMNAS   # [{"titulo":…, "tiempo":…, …}]


# ═══════════════════════════════════════════════════════════════════════════ #
class _CeldaEditor(tk.Frame):
    """
    Una celda individual de la tabla.  Muestra:
      ┌─────────────────────┐
      │ [Combo platillos ▼] │
      │ ▢ Video  [Limpiar]  │
      │ Ingredientes:       │
      │ [Text área 4 líneas]│
      │ Nota: [___________] │
      └─────────────────────┘
    """

    def __init__(self, parent, dia, col_idx, catalogo,
                 no_deseados=None, factor=1.0, **kw):
        super().__init__(parent, bg=_WHITE, relief="solid",
                         borderwidth=1, **kw)
        self.dia        = dia
        self.col_idx    = col_idx
        self.catalogo   = catalogo
        self.no_deseados = no_deseados or []
        self.factor      = factor
        self._tiempo     = COLS[col_idx]["tiempo"]

        self._build()

    def _build(self):
        # ── combo de platillos ─────────────────────────────────── #
        top = tk.Frame(self, bg=_WHITE)
        top.pack(fill="x", padx=3, pady=(3, 1))

        self._var_plat = tk.StringVar()
        self._combo = ttk.Combobox(top, textvariable=self._var_plat,
                                   state="readonly", font=_FT_PLAT,
                                   width=22)
        self._combo.pack(fill="x")
        self._combo.bind("<<ComboboxSelected>>", self._on_select_platillo)
        self._poblar_combo()

        # ── fila: video + limpiar ─────────────────────────────── #
        mid = tk.Frame(self, bg=_WHITE)
        mid.pack(fill="x", padx=3, pady=1)

        self._var_video = tk.BooleanVar(value=False)
        ttk.Checkbutton(mid, text="📹", variable=self._var_video,
                        style="TCheckbutton").pack(side="left")

        if self.dia == "Domingo" and COLS[self.col_idx]["titulo"] == "Comida":
            ttk.Button(mid, text="☺ Libre", width=7,
                       command=self._poner_libre).pack(side="left", padx=2)

        tk.Button(mid, text="✖", font=("Segoe UI", 7),
                  bg=_WHITE, fg=_MUTED, bd=0, cursor="hand2",
                  command=self.limpiar).pack(side="right")

        # ── ingredientes (text) ───────────────────────────────── #
        tk.Label(self, text="Ingredientes:", bg=_WHITE, fg=_MUTED,
                 font=("Segoe UI", 7), anchor="w").pack(
                 fill="x", padx=3)

        self._txt_ing = tk.Text(self, height=5, font=_FT_MONO,
                                relief="flat", bd=0,
                                bg="#FAFFFE", fg=_TEXT,
                                wrap="word", undo=True)
        self._txt_ing.pack(fill="both", expand=True, padx=3)

        # ── nota ─────────────────────────────────────────────── #
        nota_f = tk.Frame(self, bg=_WHITE)
        nota_f.pack(fill="x", padx=3, pady=(1, 3))
        tk.Label(nota_f, text="Nota:", bg=_WHITE, fg=_MUTED,
                 font=("Segoe UI", 7)).pack(side="left")
        self._var_nota = tk.StringVar()
        ttk.Entry(nota_f, textvariable=self._var_nota,
                  font=_FT_ING, width=18).pack(side="left", padx=2, fill="x", expand=True)

    # ── poblar combo ─────────────────────────────────────────────── #
    def _poblar_combo(self):
        from catalogo import Catalogo
        aptos = self.catalogo.aptos_para(self._tiempo, self.no_deseados)
        nombres = ["(vacío)"] + [p.nombre for p in aptos]
        self._combo["values"] = nombres
        if not self._var_plat.get():
            self._combo.current(0)
        # mapa nombre→platillo
        self._mapa = {p.nombre: p for p in aptos}

    def _on_select_platillo(self, _=None):
        nombre = self._var_plat.get()
        if nombre == "(vacío)":
            self.limpiar()
            return
        p = self._mapa.get(nombre)
        if not p:
            return
        self._var_video.set(p.video)
        self._var_nota.set(p.nota or "")
        self._txt_ing.delete("1.0", "end")
        for ing in p.ingredientes:
            self._txt_ing.insert("end", ing.render(self.factor) + "\n")
        self._highlight_titulo()

    def _poner_libre(self):
        self._var_plat.set("Comida libre")
        self._combo["values"] = list(self._combo["values"]) + ["Comida libre"]
        self._txt_ing.delete("1.0", "end")
        self._var_nota.set("")
        self._var_video.set(False)
        self.config(bg=_LIBRE_BG)
        self._txt_ing.config(bg=_LIBRE_BG)

    def _highlight_titulo(self):
        nombre = self._var_plat.get()
        if nombre and nombre != "(vacío)":
            self.config(bg="#EBF7F2")
        else:
            self.config(bg=_WHITE)

    def limpiar(self):
        self._combo.current(0)
        self._var_video.set(False)
        self._var_nota.set("")
        self._txt_ing.delete("1.0", "end")
        self.config(bg=_WHITE)
        self._txt_ing.config(bg="#FAFFFE")

    # ── get / set ──────────────────────────────────────────────────── #
    def get_datos(self) -> dict:
        nombre = self._var_plat.get()
        if nombre in ("(vacío)", ""):
            return {}
        ings = [l.strip() for l in
                self._txt_ing.get("1.0", "end").splitlines()
                if l.strip()]
        return {
            "titulo":       nombre,
            "ingredientes": ings,
            "nota":         self._var_nota.get().strip() or None,
            "video":        self._var_video.get(),
        }

    def set_datos(self, datos: dict):
        if not datos:
            self.limpiar()
            return
        titulo = datos.get("titulo", "")
        if titulo.lower() == "comida libre":
            self._poner_libre()
            return
        # intentar seleccionar del combo
        vals = list(self._combo["values"])
        if titulo not in vals:
            vals.append(titulo)
            self._combo["values"] = vals
        self._var_plat.set(titulo)
        self._var_video.set(datos.get("video", False))
        self._var_nota.set(datos.get("nota") or "")
        self._txt_ing.delete("1.0", "end")
        for ing in datos.get("ingredientes", []):
            self._txt_ing.insert("end", ing + "\n")
        self._highlight_titulo()

    def refrescar(self, catalogo, no_deseados=None, factor=None):
        if catalogo:
            self.catalogo = catalogo
        if no_deseados is not None:
            self.no_deseados = no_deseados
        if factor is not None:
            self.factor = factor
        actual = self._var_plat.get()
        self._poblar_combo()
        if actual:
            self._var_plat.set(actual)


# ═══════════════════════════════════════════════════════════════════════════ #
class TablaDieta(tk.Frame):
    """
    Tabla completa 6 columnas × 8 filas con scroll.
    """

    def __init__(self, parent, catalogo, no_deseados=None,
                 factor=1.0, **kw):
        super().__init__(parent, bg=_BG, **kw)
        self.catalogo    = catalogo
        self.no_deseados = no_deseados or []
        self.factor      = factor
        self._celdas: Dict[str, List[_CeldaEditor]] = {}

        self._build()

    def _build(self):
        # canvas + scrollbars
        self._canvas = tk.Canvas(self, bg=_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical",
                            command=self._canvas.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal",
                            command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set,
                               xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right",  fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # frame interior
        self._inner = tk.Frame(self._canvas, bg=_BG)
        self._win = self._canvas.create_window((0, 0),
                                               window=self._inner,
                                               anchor="nw")
        self._inner.bind("<Configure>", self._on_cfg)
        self._canvas.bind("<Configure>", self._on_canvas_cfg)

        # mousewheel — solo activo cuando el cursor está sobre ESTE canvas
        self._canvas.bind("<Enter>", self._bind_scroll)
        self._canvas.bind("<Leave>", self._unbind_scroll)

        self._construir_tabla()

    def _bind_scroll(self, _=None):
        self._canvas.bind_all("<MouseWheel>",       self._on_mousewheel)
        self._canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _unbind_scroll(self, _=None):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Shift-MouseWheel>")

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * e.delta / 120), "units")

    def _on_shift_mousewheel(self, e):
        self._canvas.xview_scroll(int(-1 * e.delta / 120), "units")

    def _on_cfg(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_cfg(self, e):
        self._canvas.itemconfig(self._win, width=max(e.width,
                                                     self._inner.winfo_reqwidth()))

    def _construir_tabla(self):
        # anchos
        W_DIA  = 70
        W_COL  = 185

        # cabecera (fila 0)
        cel_vacio = tk.Label(self._inner, text="",
                             bg=_VERDE, width=8)
        cel_vacio.grid(row=0, column=0, sticky="nsew",
                       padx=1, pady=1, ipady=6)

        for ci, col in enumerate(COLS):
            lbl = tk.Label(self._inner, text=col["titulo"],
                           bg=_VERDE, fg=_WHITE,
                           font=_FT_CAB, width=W_COL // 8)
            lbl.grid(row=0, column=ci + 1, sticky="nsew",
                     padx=1, pady=1, ipady=6)

        # filas de días
        for di, dia in enumerate(DIAS, start=1):
            lbl_dia = tk.Label(self._inner, text=dia,
                               bg=_VERDE, fg=_WHITE,
                               font=_FT_DIA, width=8,
                               wraplength=W_DIA - 8)
            lbl_dia.grid(row=di, column=0, sticky="nsew",
                         padx=1, pady=1)

            fila_celdas = []
            for ci, col in enumerate(COLS):
                editor = _CeldaEditor(
                    self._inner, dia, ci,
                    self.catalogo,
                    no_deseados=self.no_deseados,
                    factor=self.factor,
                    width=W_COL,
                )
                editor.grid(row=di, column=ci + 1, sticky="nsew",
                            padx=1, pady=1)
                fila_celdas.append(editor)
            self._celdas[dia] = fila_celdas

        # pesos de columnas para que se expandan
        self._inner.grid_columnconfigure(0, weight=0, minsize=W_DIA)
        for ci in range(len(COLS)):
            self._inner.grid_columnconfigure(ci + 1, weight=1, minsize=W_COL)
        for di in range(len(DIAS) + 1):
            self._inner.grid_rowconfigure(di, weight=1)

    # ── API pública ──────────────────────────────────────────────────────── #
    def get_celdas(self) -> Dict[str, List[dict]]:
        """Devuelve los datos de todas las celdas como dict[dia][col_idx] = dict."""
        resultado = {}
        for dia in DIAS:
            resultado[dia] = [c.get_datos() for c in self._celdas[dia]]
        return resultado

    def set_celdas(self, celdas: Dict[str, List[dict]]):
        """Carga datos previos en la tabla."""
        for dia in DIAS:
            fila = celdas.get(dia, [])
            for ci, editor in enumerate(self._celdas[dia]):
                datos = fila[ci] if ci < len(fila) else {}
                editor.set_datos(datos)

    def limpiar_todo(self):
        for dia in DIAS:
            for editor in self._celdas[dia]:
                editor.limpiar()

    def refrescar_catalogo(self, catalogo=None, no_deseados=None, factor=None):
        """Recarga el catálogo en todas las celdas sin borrar lo ya escrito."""
        if catalogo:
            self.catalogo = catalogo
        if no_deseados is not None:
            self.no_deseados = no_deseados
        if factor is not None:
            self.factor = factor
        for dia in DIAS:
            for editor in self._celdas[dia]:
                editor.refrescar(self.catalogo, self.no_deseados, self.factor)

    def set_no_deseados(self, nd: list):
        self.no_deseados = nd
        self.refrescar_catalogo()

    def set_factor(self, factor: float):
        self.factor = factor
        self.refrescar_catalogo()
