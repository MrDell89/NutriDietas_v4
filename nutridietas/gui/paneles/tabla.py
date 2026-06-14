# -*- coding: utf-8 -*-
"""Helpers de tabla/plantilla compartidos por los paneles de dieta."""

import os, sys, threading, subprocess, json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

from nutridietas import config
from nutridietas.nucleo import pacientes as gp
from nutridietas.nucleo.catalogo import Catalogo
from nutridietas.nucleo.modelos import Platillo, Ingrediente, PlanSemanal, CeldaDieta
from nutridietas.nucleo import dieta_individual as di
from nutridietas.nucleo import dieta_grupal as dgrupo
from nutridietas.salida import generadores
from nutridietas.nucleo import planes
from nutridietas.gui.tabla_dieta import TablaDieta
from nutridietas.gui.tema import (C_GREEN, C_DARK, C_HOVER, C_ACTIVE, C_BG, C_WHITE,
                      C_BORDER, C_TEXT, C_MUTED, C_ERROR, C_SIDEBAR, C_ACCENT,
                      FT_TITLE, FT_H3, FT_BODY, FT_SMALL, FT_BTN, FT_NAV, FT_MONO)


class TablaMixin:
    def _cargar_plantilla(self, tabla: "TablaDieta"):
        """Carga una plantilla JSON de plan semanal en la tabla indicada."""
        carpeta_plantillas = os.path.join(os.path.dirname(__file__), "plantillas")
        os.makedirs(carpeta_plantillas, exist_ok=True)

        # buscar JSON en la carpeta de plantillas
        archivos = [f for f in os.listdir(carpeta_plantillas) if f.endswith(".json")]

        if not archivos:
            if messagebox.askyesno(
                "Sin plantillas",
                f"No hay plantillas en:\n{carpeta_plantillas}\n\n"
                "¿Deseas seleccionar un archivo JSON manualmente?"):
                ruta = filedialog.askopenfilename(
                    title="Abrir plantilla de dieta",
                    filetypes=[("JSON", "*.json"), ("Todos", "*")])
                if not ruta: return
                self._aplicar_plantilla(tabla, ruta)
            return

        # diálogo de selección
        dlg = tk.Toplevel(self.root)
        dlg.title("Cargar plantilla")
        dlg.geometry("420x360"); dlg.configure(bg=C_BG); dlg.grab_set()
        tk.Label(dlg, text="Selecciona una plantilla:", bg=C_BG, fg=C_DARK,
                 font=FT_H3).pack(anchor="w", padx=16, pady=(14,4))
        tk.Label(dlg, text=f"Carpeta: {carpeta_plantillas}",
                 bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(anchor="w", padx=16)

        lb = tk.Listbox(dlg, font=FT_BODY, selectmode="single",
                        bg=C_WHITE, fg=C_TEXT, relief="solid", bd=1,
                        activestyle="dotbox")
        lb.pack(fill="both", expand=True, padx=16, pady=8)
        for a in archivos:
            lb.insert("end", a)
        lb.selection_set(0)

        def _ok():
            sel = lb.curselection()
            if not sel: return
            ruta = os.path.join(carpeta_plantillas, archivos[sel[0]])
            dlg.destroy()
            self._aplicar_plantilla(tabla, ruta)

        bf = tk.Frame(dlg, bg=C_BG); bf.pack(fill="x", padx=16, pady=(0,12))
        ttk.Button(bf, text="Cancelar", style="Outline.TButton",
                   command=dlg.destroy).pack(side="right", padx=4)
        ttk.Button(bf, text="Cargar", style="Green.TButton",
                   command=_ok).pack(side="right", padx=4)
        ttk.Button(bf, text="📂 Otro archivo…", style="Outline.TButton",
                   command=lambda: [dlg.destroy(),
                       self._aplicar_plantilla(tabla,
                           filedialog.askopenfilename(
                               title="Abrir plantilla",
                               filetypes=[("JSON","*.json"),("Todos","*")]) or "")]
                   ).pack(side="left", padx=4)

    def _aplicar_plantilla(self, tabla, ruta):
        if not ruta or not os.path.exists(ruta): return
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            celdas = data.get("celdas", data)  # acepta wrapper o dict directo
            tabla.set_celdas(celdas)
            nombre = data.get("nombre", os.path.basename(ruta))
            self.set_status(f"✔ Plantilla '{nombre}' cargada en la tabla.")
        except Exception as e:
            messagebox.showerror("Error al cargar plantilla", str(e))

    # ── helpers públicos para atajos ──────────────────────────────────────── #
    def limpiar_tabla_activa(self):
        if self._panel_activo == "individual":
            self._tabla_ind.limpiar_todo()
            self.set_status("✔ Tabla individual limpiada (Ctrl+L)")
        elif self._panel_activo == "grupo":
            self._tabla_gr.limpiar_todo()
            self.set_status("✔ Tabla de grupo limpiada (Ctrl+L)")

    def autocompletar_tabla_activa(self):
        if self._panel_activo == "individual":
            self._autocompletar_tabla_ind()
        elif self._panel_activo == "grupo":
            self._autocompletar_tabla_gr()
        else:
            self.set_status("Ctrl+K: navega a Individual o Grupo primero.")

    def ir_a_pestana_tabla(self):
        """Cambia a la pestaña Tabla en el panel activo."""
        try:
            if self._panel_activo == "individual":
                nb = self._panels["individual"].winfo_children()[1]  # notebook
                nb.select(1)
            elif self._panel_activo == "grupo":
                nb = self._panels["grupo"].winfo_children()[1]
                nb.select(1)
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════════════ #
    #  PANEL CATÁLOGO                                                          #
    # ════════════════════════════════════════════════════════════════════════ #
