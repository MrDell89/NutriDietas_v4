# -*- coding: utf-8 -*-
"""Panel de dieta individual de la GUI."""

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


class PanelIndividualMixin:
    def _panel_individual(self):
        f = tk.Frame(self.content, bg=C_BG)

        # ── encabezado ────────────────────────────────────────────────────── #
        hdr = tk.Frame(f, bg=C_WHITE, pady=8); hdr.pack(fill="x",padx=16,pady=(14,0))
        tk.Label(hdr, text="🍽  Dieta Individual", font=FT_TITLE,
                 bg=C_WHITE, fg=C_DARK).pack(side="left", padx=10)

        # notebook: Opciones | Tabla
        nb = ttk.Notebook(f); nb.pack(fill="both", expand=True, padx=16, pady=8)

        # ───── pestaña OPCIONES ──────────────────────────────────────────── #
        tab_op = tk.Frame(nb, bg=C_BG); nb.add(tab_op, text="  ⚙ Opciones  ")
        left  = tk.Frame(tab_op, bg=C_BG)
        right = tk.Frame(tab_op, bg=C_BG)
        left.pack(side="left", fill="both", expand=True, padx=(10,6), pady=8)
        right.pack(side="right", fill="both", expand=True, padx=(6,10), pady=8)

        # paciente
        pac_lf = ttk.LabelFrame(left, text="Paciente", padding=8); pac_lf.pack(fill="x",pady=(0,8))
        sf_ind = tk.Frame(pac_lf, bg=C_BG); sf_ind.pack(fill="x", pady=(0,3))
        tk.Label(sf_ind, text="🔎 Buscar:", bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(side="left")
        self._var_buscar_ind = tk.StringVar()
        self._var_buscar_ind.trace_add("write", lambda *a: self._filtrar_combo_pac())
        ttk.Entry(sf_ind, textvariable=self._var_buscar_ind, font=FT_BODY, width=26).pack(side="left", padx=4)
        self._combo_pac = ttk.Combobox(pac_lf, state="readonly", font=FT_BODY, width=34)
        self._combo_pac.pack(fill="x", pady=(0,4))
        self._combo_pac.bind("<<ComboboxSelected>>", lambda e: self._on_cambio_paciente())

        # alimentos que evita
        nd_lf = ttk.LabelFrame(left, text="Alimentos que evita (uno por línea)", padding=8)
        nd_lf.pack(fill="x", pady=(0,8))
        self._entry_nd = tk.Text(nd_lf, height=3, font=FT_BODY, relief="solid",
                                 bd=1, bg=C_WHITE, fg=C_TEXT)
        self._entry_nd.pack(fill="x")
        tk.Label(nd_lf, text="Se excluirán del selector de la tabla.",
                 bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(anchor="w")

        # opciones de generación
        opt_lf = ttk.LabelFrame(left, text="Opciones", padding=8); opt_lf.pack(fill="x",pady=(0,8))
        for lbl_txt, widget_fn in [("Nº plan:", lambda r: self._mk_spin(r,"_spin_plan",1,50,1)),
                                   ("Factor porción:", lambda r: self._mk_spin_f(r,"_spin_factor",0.5,3.0,1.0))]:
            row = tk.Frame(opt_lf, bg=C_BG); row.pack(fill="x",pady=3)
            tk.Label(row, text=lbl_txt, bg=C_BG, fg=C_TEXT, font=FT_BODY,
                     width=16, anchor="w").pack(side="left")
            widget_fn(row)
        chk = tk.Frame(opt_lf, bg=C_BG); chk.pack(fill="x",pady=3)
        self._var_col2  = tk.BooleanVar(value=False)
        self._var_libre = tk.BooleanVar(value=False)
        ttk.Checkbutton(chk,text="Incluir Colación 2",variable=self._var_col2).pack(side="left",padx=(0,14))
        ttk.Checkbutton(chk,text="Comida libre domingo",variable=self._var_libre).pack(side="left")

        # notas
        nt_lf = ttk.LabelFrame(left, text="Notas superiores (una por línea)", padding=8)
        nt_lf.pack(fill="x", pady=(0,8))
        self._txt_notas = tk.Text(nt_lf, height=3, font=FT_BODY, relief="solid",
                                  bd=1, bg=C_WHITE, fg=C_TEXT)
        self._txt_notas.pack(fill="x")

        # botones de acción (opciones tab)
        br_op = tk.Frame(left, bg=C_BG); br_op.pack(fill="x", pady=(4,0))
        ttk.Button(br_op, text="▶  Autocompletar tabla", style="Dark.TButton",
                   command=self._autocompletar_tabla_ind).pack(side="left", padx=(0,6))

        # exclusiones
        excl_lf = ttk.LabelFrame(right, text="Platillos excluidos", padding=8)
        excl_lf.pack(fill="both", expand=True, pady=(0,8))
        cols2 = ("Platillo","Contiene…")
        self._tree_excl = ttk.Treeview(excl_lf, columns=cols2, show="headings", height=8)
        self._tree_excl.heading("Platillo",text="Platillo excluido")
        self._tree_excl.heading("Contiene…",text="Ingrediente conflictivo")
        self._tree_excl.column("Platillo",width=230); self._tree_excl.column("Contiene…",width=140)
        self._tree_excl.tag_configure("excl",foreground=C_ERROR)
        vsb2 = ttk.Scrollbar(excl_lf, orient="vertical", command=self._tree_excl.yview)
        self._tree_excl.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right",fill="y"); self._tree_excl.pack(fill="both",expand=True)
        ttk.Button(excl_lf, text="↺  Actualizar", style="Outline.TButton",
                   command=self._actualizar_exclusiones).pack(anchor="e",pady=(4,0))

        # ───── pestaña TABLA ─────────────────────────────────────────────── #
        tab_tabla = tk.Frame(nb, bg=C_BG); nb.add(tab_tabla, text="  📋 Tabla de Dieta  ")

        # barra superior de la tabla
        tb_top = tk.Frame(tab_tabla, bg=C_BG); tb_top.pack(fill="x",padx=8,pady=(8,4))
        ttk.Button(tb_top, text="↺  Refrescar catálogo", style="Outline.TButton",
                   command=self._refrescar_tabla_ind).pack(side="left", padx=4)
        ttk.Button(tb_top, text="🗑  Limpiar tabla", style="Outline.TButton",
                   command=lambda: self._tabla_ind.limpiar_todo()).pack(side="left", padx=4)
        ttk.Button(tb_top, text="▶  Autocompletar desde catálogo", style="Dark.TButton",
                   command=self._autocompletar_tabla_ind).pack(side="left", padx=4)
        ttk.Button(tb_top, text="📂  Cargar plantilla", style="Outline.TButton",
                   command=lambda: self._cargar_plantilla(self._tabla_ind)).pack(side="left", padx=4)

        # tabla interactiva
        pac_tmp = self._get_pac_individual() if self.pacientes else None
        nd_tmp  = pac_tmp.no_deseados if pac_tmp else []
        self._tabla_ind = TablaDieta(tab_tabla, self.catalogo,
                                     no_deseados=nd_tmp, factor=1.0)
        self._tabla_ind.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # ── botones generar (fuera del notebook) ─────────────────────────── #
        btn_f = tk.Frame(f, bg=C_BG); btn_f.pack(fill="x", padx=16, pady=(0,12))
        self._btn_gen_ind = ttk.Button(btn_f, text="📄  Generar PDF",
                                       style="Green.TButton",
                                       command=lambda: self.generar_individual(fmt="pdf"))
        self._btn_gen_ind.pack(side="right", ipadx=10, ipady=4, padx=(6,0))
        ttk.Button(btn_f, text="📝  Generar Word", style="Dark.TButton",
                   command=lambda: self.generar_individual(fmt="docx")).pack(
                   side="right", ipadx=10, ipady=4)

        return f

    def _mk_spin(self, parent, attr, frm, to, default):
        sp = ttk.Spinbox(parent, from_=frm, to=to, width=6, font=FT_BODY)
        sp.set(default); sp.pack(side="left")
        setattr(self, attr, sp)

    def _mk_spin_f(self, parent, attr, frm, to, default):
        sp = ttk.Spinbox(parent, from_=frm, to=to, increment=0.1,
                         width=7, font=FT_BODY, format="%.1f")
        sp.set(f"{default:.1f}"); sp.pack(side="left")
        tk.Label(parent, text="  (1.0=base, 1.2=+20%)",
                 bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(side="left")
        setattr(self, attr, sp)

    def _filtrar_combo_pac(self):
        q = self._var_buscar_ind.get().lower().strip()
        nombres = [p.nombre for p in self.pacientes
                   if not q or q in p.nombre.lower()]
        self._combo_pac["values"] = nombres
        if nombres:
            self._combo_pac.current(0)
            self._on_cambio_paciente()

    def _refrescar_combo_individual(self):
        nombres = [p.nombre for p in self.pacientes]
        self._combo_pac["values"] = nombres
        if nombres: self._combo_pac.current(0); self._on_cambio_paciente()

    def _on_cambio_paciente(self,*_):
        pac = self._get_pac_individual()
        if not pac: return
        self._entry_nd.delete("1.0","end")
        self._entry_nd.insert("end","\n".join(pac.no_deseados))
        self._spin_plan.set(pac.num_planes+1)
        self._actualizar_exclusiones()
        self._tabla_ind.refrescar_catalogo(
            no_deseados=pac.no_deseados,
            factor=pac.factor_porcion)

    def _get_pac_individual(self):
        nombre = self._combo_pac.get()
        return next((p for p in self.pacientes if p.nombre==nombre), None)

    def _actualizar_exclusiones(self):
        pac = self._get_pac_individual()
        self._tree_excl.delete(*self._tree_excl.get_children())
        if not pac: return
        nd = [x.strip() for x in self._entry_nd.get("1.0","end").strip().splitlines() if x.strip()]
        pac.no_deseados = nd
        excluidos = di.reporte_excluidos(pac, self.catalogo)
        for p,palabra in excluidos:
            self._tree_excl.insert("","end",values=(p.nombre,palabra),tags=("excl",))
        if not excluidos:
            self._tree_excl.insert("","end",values=("(ningún platillo excluido)",""))

    def _refrescar_tabla_ind(self):
        self.catalogo.cargar()
        pac = self._get_pac_individual()
        nd = pac.no_deseados if pac else []
        self._tabla_ind.refrescar_catalogo(self.catalogo, no_deseados=nd)
        self.set_status("↺ Catálogo refrescado en la tabla")

    def _autocompletar_tabla_ind(self):
        """Rellena la tabla automáticamente desde el catálogo (respetando no-deseados)."""
        pac = self._get_pac_individual()
        if not pac: messagebox.showerror("Error","Selecciona un paciente."); return
        nd = [x.strip() for x in self._entry_nd.get("1.0","end").strip().splitlines() if x.strip()]
        pac.no_deseados = nd
        try:
            num   = int(self._spin_plan.get())
            fac   = float(self._spin_factor.get())
        except ValueError: fac=1.0; num=1
        pac.factor_porcion = fac
        col2  = self._var_col2.get(); libre = self._var_libre.get()
        notas = [l for l in self._txt_notas.get("1.0","end").splitlines() if l.strip()]
        plan  = di.construir(pac, self.catalogo, numero_plan=num,
                             incluir_colacion2=col2,
                             comida_libre_domingo=libre, notas=notas)
        # convertir plan a celdas del editor
        celdas_ed = {}
        for dia in config.DIAS:
            fila = []
            for ci, celda_obj in enumerate(plan.celdas.get(dia,[])):
                if celda_obj is None:
                    fila.append({})
                elif celda_obj.texto_especial:
                    fila.append({"titulo": celda_obj.texto_especial,
                                 "ingredientes":[],"nota":None,"video":False})
                elif celda_obj.platillo:
                    p = celda_obj.platillo
                    fila.append({
                        "titulo":      p.nombre,
                        "ingredientes":[ing.render(fac) for ing in p.ingredientes],
                        "nota":        p.nota,
                        "video":       p.video,
                    })
                else:
                    fila.append({})
            celdas_ed[dia] = fila
        self._tabla_ind.set_celdas(celdas_ed)
        self.set_status("✔ Tabla autocompletada. Puedes editar celda por celda antes de generar.")

    def generar_individual(self, fmt="pdf"):
        pac = self._get_pac_individual()
        if not pac: messagebox.showerror("Error","Selecciona un paciente."); return
        nd = [x.strip() for x in self._entry_nd.get("1.0","end").strip().splitlines() if x.strip()]
        pac.no_deseados = nd
        try:
            num   = int(self._spin_plan.get())
            fac   = float(self._spin_factor.get())
        except ValueError: messagebox.showerror("Error","Número de plan o factor inválido."); return
        pac.factor_porcion = fac
        notas = [l for l in self._txt_notas.get("1.0","end").splitlines() if l.strip()]

        # usar datos de la tabla (si tiene contenido) o generar automáticamente
        celdas_manual = self._tabla_ind.get_celdas()
        tiene_contenido = any(d for fila in celdas_manual.values() for d in fila if d)

        # destino en carpeta del paciente
        ext = generadores.extension(fmt)
        from nutridietas.nucleo.modelos import PlanSemanal
        plan_tmp = PlanSemanal(paciente=pac, numero_plan=num,
                               notas_superiores=notas, celdas={})
        nombre_base = plan_tmp.nombre_archivo().replace(".docx", ext)
        destino = None
        if pac.carpeta and os.path.isdir(pac.carpeta):
            destino = os.path.join(pac.carpeta, nombre_base)
            # alerta si ya existe ese plan
            if os.path.exists(destino):
                if not messagebox.askyesno(
                    "Plan ya existe",
                    f"Ya existe un archivo para el plan {num} de {pac.nombre}:\n{nombre_base}\n\n¿Sobreescribir?"):
                    return

        self._btn_gen_ind.config(state="disabled")
        self.set_status(f"Generando {fmt.upper()} de {pac.nombre}…")

        def _run():
            try:
                if tiene_contenido:
                    ruta = generadores.generar_desde_celdas_manual(
                        pac, celdas_manual, num, notas, destino, formato=fmt)
                else:
                    plan = di.construir(pac, self.catalogo, numero_plan=num,
                                        incluir_colacion2=self._var_col2.get(),
                                        comida_libre_domingo=self._var_libre.get(),
                                        notas=notas)
                    ruta = generadores.generar(plan, fmt, destino)
                self.root.after(0, lambda r=ruta: self._gen_ok(r))
            except Exception as e:
                self.root.after(0, lambda m=str(e): self._gen_error(m))

        threading.Thread(target=_run, daemon=True).start()

    def _gen_ok(self, ruta):
        try: self._btn_gen_ind.config(state="normal")
        except: pass
        try: self._btn_gen_grupo.config(state="normal")
        except: pass
        self.set_status(f"✔ {ruta}")
        if messagebox.askyesno("Generado", f"Guardado en:\n{ruta}\n\n¿Abrir carpeta?"):
            os.startfile(os.path.dirname(ruta))

    def _gen_error(self, msg):
        try: self._btn_gen_ind.config(state="normal")
        except: pass
        try: self._btn_gen_grupo.config(state="normal")
        except: pass
        self.set_status(f"Error: {msg}", C_ERROR)
        messagebox.showerror("Error al generar", msg)

    # ════════════════════════════════════════════════════════════════════════ #
    #  PANEL DIETA EN GRUPO  (tabla + PDF por paciente en su carpeta)         #
    # ════════════════════════════════════════════════════════════════════════ #
