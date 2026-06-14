# -*- coding: utf-8 -*-
"""Panel de pacientes de la GUI (listado, búsqueda, selección)."""

import os, sys, threading, subprocess, json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import config
import pacientes as gp
from catalogo import Catalogo
from modelos import Platillo, Ingrediente, PlanSemanal, CeldaDieta
import dieta_individual as di
import dieta_grupal as dgrupo
import generadores
import planes
from tabla_dieta import TablaDieta
from gui_tema import (C_GREEN, C_DARK, C_HOVER, C_ACTIVE, C_BG, C_WHITE,
                      C_BORDER, C_TEXT, C_MUTED, C_ERROR, C_SIDEBAR, C_ACCENT,
                      FT_TITLE, FT_H3, FT_BODY, FT_SMALL, FT_BTN, FT_NAV, FT_MONO)


class PanelPacientesMixin:
    def _panel_pacientes(self):
        f = tk.Frame(self.content, bg=C_BG)
        hdr = tk.Frame(f, bg=C_WHITE, pady=10); hdr.pack(fill="x",padx=16,pady=(16,0))
        tk.Label(hdr, text="Pacientes", font=FT_TITLE,
                 bg=C_WHITE, fg=C_DARK).pack(side="left", padx=10)
        br = tk.Frame(hdr, bg=C_WHITE); br.pack(side="right", padx=10)
        self._btn_recargar = ttk.Button(br, text="↺  Recargar", style="Outline.TButton",
                   command=self.recargar_pacientes)
        self._btn_recargar.pack(side="left", padx=4)
        ttk.Button(br, text="📂  Carpeta", style="Outline.TButton",
                   command=self._abrir_carpeta_paciente).pack(side="left", padx=4)
        ttk.Button(br, text="🍽  Nueva Dieta", style="Green.TButton",
                   command=self._ir_a_dieta_individual).pack(side="left", padx=4)
        sf = tk.Frame(f, bg=C_BG); sf.pack(fill="x", padx=16, pady=(8,2))
        tk.Label(sf, text="Buscar:", bg=C_BG, fg=C_MUTED, font=FT_BODY).pack(side="left")
        self._var_buscar_pac = tk.StringVar()
        self._var_buscar_pac.trace_add("write", lambda *a: self._filtrar_pacientes())
        ttk.Entry(sf, textvariable=self._var_buscar_pac, font=FT_BODY, width=28).pack(side="left",padx=6)
        self._lbl_cargando = tk.Label(sf, text="", bg=C_BG, fg=C_MUTED, font=FT_SMALL)
        self._lbl_cargando.pack(side="left", padx=8)
        tf = tk.Frame(f, bg=C_BG); tf.pack(fill="both", expand=True, padx=16, pady=6)
        cols = ("#","Nombre","Planes","Evita","Prefiere","Última dieta")
        self._tree_pac = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for c,w in zip(cols,[36,220,50,250,140,160]):
            self._tree_pac.heading(c,text=c); self._tree_pac.column(c,width=w,minwidth=28)
        self._tree_pac.tag_configure("alt", background="#EBF7F2")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree_pac.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self._tree_pac.xview)
        self._tree_pac.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom",fill="x"); vsb.pack(side="right",fill="y")
        self._tree_pac.pack(fill="both",expand=True)
        self._tree_pac.bind("<<TreeviewSelect>>", self._on_select_paciente)
        self._tree_pac.bind("<Double-1>", lambda e: self._ir_a_dieta_individual())
        # panel de detalle del paciente
        det = ttk.LabelFrame(f, text="Detalle del paciente", padding=8)
        det.pack(fill="x", padx=16, pady=(0,12))
        det_top = tk.Frame(det, bg=C_BG); det_top.pack(fill="x")
        self._lbl_det_pac = tk.Label(det_top, text="Selecciona un paciente.",
                                     bg=C_BG, fg=C_MUTED, font=FT_BODY,
                                     anchor="w", justify="left")
        self._lbl_det_pac.pack(side="left", fill="x", expand=True)
        self._btn_abrir_det = ttk.Button(det_top, text="📂 Abrir carpeta",
                                          style="Outline.TButton",
                                          command=self._abrir_carpeta_paciente)
        self._btn_abrir_det.pack(side="right", padx=4)
        ttk.Button(det_top, text="🍽 Hacer dieta", style="Green.TButton",
                   command=self._ir_a_dieta_individual).pack(side="right", padx=4)
        self._lbl_ultima = tk.Label(det, text="", bg=C_BG, fg=C_SIDEBAR,
                                    font=FT_SMALL, anchor="w", justify="left")
        self._lbl_ultima.pack(fill="x", pady=(4,0))
        return f

    # ── carga de pacientes en hilo secundario ──────────────────────────────── #
    def recargar_pacientes(self):
        self.set_status("⏳ Cargando pacientes…")
        self._lbl_cargando.config(text="⏳ Cargando…")
        try: self._btn_recargar.config(state="disabled")
        except: pass
        threading.Thread(target=self._recargar_bg, daemon=True).start()

    def _recargar_bg(self):
        try:
            pacs = gp.listar_pacientes()
        except Exception as e:
            self.root.after(0, lambda: self.set_status(f"Error al cargar: {e}", C_ERROR))
            return
        self.root.after(0, lambda: self._recargar_done(pacs))

    def _recargar_done(self, pacs):
        self.pacientes = pacs
        self._poblar_tree_pacientes(pacs)
        self.set_status(f"✔ {len(pacs)} pacientes — {config.CARPETA_PACIENTES}")
        self._lbl_cargando.config(text=f"{len(pacs)} pacientes")
        try: self._btn_recargar.config(state="normal")
        except: pass
        self._refrescar_combo_individual()
        self._refrescar_checks_grupo()

    def _poblar_tree_pacientes(self, lista):
        t = self._tree_pac; t.delete(*t.get_children())
        for i,p in enumerate(lista):
            ultima, _ = self._get_ultima_dieta(p)
            t.insert("","end",tags=("alt" if i%2 else "",),
                     values=(i+1, p.nombre, p.num_planes,
                             ", ".join(p.no_deseados) or "—",
                             ", ".join(p.preferidos) or "—",
                             ultima or "—"))

    def _filtrar_pacientes(self):
        q = self._var_buscar_pac.get().lower()
        self._poblar_tree_pacientes(
            [p for p in self.pacientes if q in p.nombre.lower()] if q else self.pacientes)

    def _get_ultima_dieta(self, p):
        """Devuelve (nombre_archivo, fecha_str) del plan más reciente del paciente."""
        import datetime
        if not p.carpeta or not os.path.isdir(p.carpeta):
            return None, None
        try:
            archivos = os.listdir(p.carpeta)
        except Exception:
            return None, None
        planes = [a for a in archivos
                  if "plan alimenticio" in a.lower() and
                  (a.endswith(".docx") or a.endswith(".pdf"))]
        if not planes:
            return None, None
        planes.sort(key=lambda a: os.path.getmtime(os.path.join(p.carpeta, a)), reverse=True)
        nombre = planes[0]
        mtime  = os.path.getmtime(os.path.join(p.carpeta, nombre))
        fecha  = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y")
        return nombre, fecha

    def _on_select_paciente(self,_=None):
        sel = self._tree_pac.selection()
        if not sel: return
        idx = int(self._tree_pac.item(sel[0],"values")[0])-1
        if 0<=idx<len(self.pacientes):
            p = self.pacientes[idx]
            self._lbl_det_pac.config(text=(
                f"  Nombre: {p.nombre}   |   Planes generados: {p.num_planes}"
                f"   |   Factor: {p.factor_porcion:.1f}\n"
                f"  Evita: {', '.join(p.no_deseados) or '(ninguno)'}"
                f"   |   Prefiere: {', '.join(p.preferidos) or '(ninguno)'}\n"
                f"  Carpeta: {p.carpeta or '(sin carpeta)'}"))
            ultima, fecha = self._get_ultima_dieta(p)
            if ultima:
                self._lbl_ultima.config(
                    text=f"  📄 Última dieta: {ultima}  ({fecha})")
            else:
                self._lbl_ultima.config(text="  📄 Última dieta: (ninguna aún)")

    def _abrir_carpeta_paciente(self):
        sel = self._tree_pac.selection()
        if not sel: messagebox.showinfo("Selección","Selecciona un paciente."); return
        idx = int(self._tree_pac.item(sel[0],"values")[0])-1
        if 0<=idx<len(self.pacientes):
            p = self.pacientes[idx]
            if p.carpeta and os.path.isdir(p.carpeta): os.startfile(p.carpeta)
            else: messagebox.showwarning("Sin carpeta",f"No se encontró carpeta para {p.nombre}.")

    def _ir_a_dieta_individual(self):
        sel = self._tree_pac.selection()
        if sel:
            idx = int(self._tree_pac.item(sel[0],"values")[0])-1
            if 0<=idx<len(self.pacientes):
                self._combo_pac.set(self.pacientes[idx].nombre)
                self._on_cambio_paciente()
        self.navegar("individual")

    # ════════════════════════════════════════════════════════════════════════ #
    #  PANEL DIETA INDIVIDUAL  (con tabla visual + salida PDF/DOCX)           #
    # ════════════════════════════════════════════════════════════════════════ #
