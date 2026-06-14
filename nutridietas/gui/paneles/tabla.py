# -*- coding: utf-8 -*-
"""Helpers de tabla/plantilla compartidos por los paneles de dieta."""

import os, sys, threading, subprocess, json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import re

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
        """Carga una plantilla JSON o Word de plan semanal en la tabla indicada."""
        carpeta_plantillas = getattr(
            config,
            "CARPETA_PLANTILLAS",
            os.path.join(config.RAIZ_PROYECTO, "plantillas"),
        )
        os.makedirs(carpeta_plantillas, exist_ok=True)

        # buscar plantillas en la carpeta
        archivos = [
            f for f in os.listdir(carpeta_plantillas)
            if f.lower().endswith((".json", ".docx"))
        ]

        if not archivos:
            messagebox.showinfo(
                "Sin plantillas",
                f"No hay plantillas en:\n{carpeta_plantillas}\n\n"
                "Puedes cambiar esta carpeta en Configuración."
            )
            return

        archivos = sorted(archivos, key=_orden_plantilla)

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
                               filetypes=[
                                   ("Plantillas","*.json *.docx"),
                                   ("Word","*.docx"),
                                   ("JSON","*.json"),
                                   ("Todos","*"),
                               ]) or "")]
                   ).pack(side="left", padx=4)

    def _aplicar_plantilla(self, tabla, ruta):
        if not ruta or not os.path.exists(ruta): return
        try:
            if ruta.lower().endswith(".docx"):
                from nutridietas.nucleo import plantillas_word
                restricciones, revisiones = self._restricciones_para_plantilla()
                resultado = plantillas_word.cargar(
                    ruta,
                    self.catalogo,
                    restricciones=restricciones,
                )
                tabla.refrescar_catalogo(self.catalogo)
                tabla.set_celdas(resultado.celdas)
                nombre = os.path.basename(ruta)
                self.set_status(f"✔ Plantilla Word '{nombre}' cargada en la tabla.")
                self._avisar_resultado_plantilla(resultado, revisiones)
                return

            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            celdas = data.get("celdas", data)  # acepta wrapper o dict directo
            tabla.set_celdas(celdas)
            nombre = data.get("nombre", os.path.basename(ruta))
            self.set_status(f"✔ Plantilla '{nombre}' cargada en la tabla.")
        except Exception as e:
            messagebox.showerror("Error al cargar plantilla", str(e))

    def _restricciones_para_plantilla(self):
        pacientes = []
        if getattr(self, "_panel_activo", None) == "individual":
            try:
                pac = self._get_pac_individual()
            except Exception:
                pac = None
            if pac:
                nd = [
                    x.strip()
                    for x in self._entry_nd.get("1.0", "end").splitlines()
                    if x.strip()
                ]
                pac.no_deseados = nd
                pacientes = [pac]
        elif getattr(self, "_panel_activo", None) == "grupo":
            pacientes = [
                p for _, (p, v) in getattr(self, "_grupo_checks", {}).items()
                if v.get()
            ]

        restricciones = []
        revisiones = []
        for pac in pacientes:
            restricciones.extend(pac.restricciones_alimentarias())
            revisiones.extend(pac.restricciones_a_revisar())
        return list(dict.fromkeys(restricciones)), list(dict.fromkeys(revisiones))

    def _avisar_resultado_plantilla(self, resultado, revisiones):
        mensajes = []
        if resultado.conflictos:
            lineas = [
                f"• {c['dia']} / {c['tiempo']}: {c['platillo']} "
                f"(contiene: {c['restriccion']})"
                for c in resultado.conflictos[:20]
            ]
            if len(resultado.conflictos) > 20:
                lineas.append(f"... y {len(resultado.conflictos) - 20} más")
            mensajes.append(
                "Se dejaron vacías estas celdas por alergias/no deseados:\n"
                + "\n".join(lineas)
            )
        if resultado.agregados:
            lineas = [
                f"• {p.nombre} [{p.tiempo}]"
                for p in resultado.agregados[:20]
            ]
            if len(resultado.agregados) > 20:
                lineas.append(f"... y {len(resultado.agregados) - 20} más")
            mensajes.append(
                "Estos platillos no estaban en el catálogo y se agregaron:\n"
                + "\n".join(lineas)
            )
        if revisiones:
            mensajes.append(
                "Revisa manualmente estas notas del paciente porque son ambiguas:\n"
                + "\n".join(f"• {x}" for x in revisiones[:20])
            )
        if mensajes:
            messagebox.showinfo("Plantilla cargada", "\n\n".join(mensajes))

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


def _orden_plantilla(nombre):
    m = re.search(r"(\d+)", nombre)
    return (int(m.group(1)) if m else 9999, nombre.lower())
