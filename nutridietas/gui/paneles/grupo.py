# -*- coding: utf-8 -*-
"""Panel de dieta en grupo de la GUI."""

import copy
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

_GRUPO_BASE = "Grupo base"


class PanelGrupoMixin:
    def _panel_grupo(self):
        self._grupo_overrides = {}
        self._grupo_base_celdas = None
        self._grupo_edicion_actual = _GRUPO_BASE

        f = tk.Frame(self.content, bg=C_BG)
        hdr = tk.Frame(f, bg=C_WHITE, pady=8); hdr.pack(fill="x",padx=16,pady=(14,0))
        tk.Label(hdr, text="👫  Dieta en Grupo", font=FT_TITLE,
                 bg=C_WHITE, fg=C_DARK).pack(side="left", padx=10)

        nb = ttk.Notebook(f); nb.pack(fill="both", expand=True, padx=16, pady=8)

        # ───── pestaña OPCIONES GRUPO ────────────────────────────────────── #
        tab_op = tk.Frame(nb, bg=C_BG); nb.add(tab_op, text="  ⚙ Opciones  ")
        left = tk.Frame(tab_op, bg=C_BG, width=250); left.pack(side="left",fill="y",padx=(10,6),pady=8)
        left.pack_propagate(False)
        right = tk.Frame(tab_op, bg=C_BG); right.pack(side="right",fill="both",expand=True,padx=(6,10),pady=8)

        # checks pacientes
        tk.Label(left, text="Pacientes del grupo:", bg=C_BG, fg=C_DARK, font=FT_H3).pack(anchor="w",pady=(0,2))
        # buscador de pacientes en grupo
        sf_buscar = tk.Frame(left, bg=C_BG); sf_buscar.pack(fill="x",pady=(0,2))
        tk.Label(sf_buscar, text="🔎", bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(side="left")
        self._var_buscar_grupo = tk.StringVar()
        self._var_buscar_grupo.trace_add("write", lambda *a: self._filtrar_checks_grupo())
        ttk.Entry(sf_buscar, textvariable=self._var_buscar_grupo, font=FT_BODY, width=18).pack(side="left",padx=3)
        sf2 = tk.Frame(left, bg=C_BG); sf2.pack(fill="x",pady=(0,4))
        ttk.Button(sf2,text="✔ Todos",style="Outline.TButton",
                   command=lambda:self._sel_grupo(True)).pack(side="left",padx=(0,4))
        ttk.Button(sf2,text="✖ Ninguno",style="Outline.TButton",
                   command=lambda:self._sel_grupo(False)).pack(side="left")
        cv = tk.Canvas(left, bg=C_BG, highlightthickness=0)
        vsb3 = ttk.Scrollbar(left, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=vsb3.set)
        vsb3.pack(side="right",fill="y"); cv.pack(side="left",fill="both",expand=True)
        self._frame_checks = tk.Frame(cv, bg=C_BG)
        wid = cv.create_window((0,0), window=self._frame_checks, anchor="nw")
        self._frame_checks.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(wid, width=e.width))

        # comparación y factores
        cmp_lf = ttk.LabelFrame(right, text="Comparación de gustos", padding=8)
        cmp_lf.pack(fill="x", pady=(0,8))
        self._txt_cmp = scrolledtext.ScrolledText(cmp_lf, height=6, font=FT_MONO,
                                                   bg=C_DARK, fg="#A8D5C5",
                                                   relief="flat", state="disabled")
        self._txt_cmp.pack(fill="x")
        ttk.Button(cmp_lf, text="🔍  Comparar gustos", style="Dark.TButton",
                   command=self._comparar_grupo).pack(anchor="e", pady=(6,0))

        self._fac_lf = ttk.LabelFrame(right, text="Factor de porción por paciente", padding=8)
        self._fac_lf.pack(fill="x", pady=(0,8))
        self._frame_factores = tk.Frame(self._fac_lf, bg=C_BG); self._frame_factores.pack(fill="x")
        tk.Label(self._fac_lf, text="Aparecen al comparar.", bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(anchor="w")

        opt2 = tk.Frame(right, bg=C_BG); opt2.pack(fill="x",pady=(0,8))
        tk.Label(opt2,text="Plan/semana:",bg=C_BG,fg=C_TEXT,font=FT_BODY).pack(side="left")
        self._spin_plan_gr = ttk.Spinbox(opt2, from_=1, to=50, width=5, font=FT_BODY)
        self._spin_plan_gr.set(1); self._spin_plan_gr.pack(side="left",padx=(4,18))
        self._var_col2_gr = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt2,text="Incluir Colación 2",variable=self._var_col2_gr).pack(side="left")

        # ───── pestaña TABLA GRUPO ───────────────────────────────────────── #
        tab_tg = tk.Frame(nb, bg=C_BG); nb.add(tab_tg, text="  📋 Tabla del Grupo  ")
        tb_top2 = tk.Frame(tab_tg, bg=C_BG); tb_top2.pack(fill="x",padx=8,pady=(8,4))
        ttk.Button(tb_top2, text="↺  Refrescar", style="Outline.TButton",
                   command=self._refrescar_tabla_gr).pack(side="left",padx=4)
        ttk.Button(tb_top2, text="🗑  Limpiar", style="Outline.TButton",
                   command=lambda: self._tabla_gr.limpiar_todo()).pack(side="left",padx=4)
        ttk.Button(tb_top2, text="▶  Autocompletar", style="Dark.TButton",
                   command=self._autocompletar_tabla_gr).pack(side="left",padx=4)
        ttk.Button(tb_top2, text="📂  Cargar plantilla", style="Outline.TButton",
                   command=lambda: self._cargar_plantilla(self._tabla_gr)).pack(side="left",padx=4)
        ttk.Button(tb_top2, text="💾  Guardar ajuste", style="Outline.TButton",
                   command=self._guardar_edicion_actual_grupo).pack(side="left",padx=4)
        tk.Label(tb_top2, text="Editar para:", bg=C_BG, fg=C_TEXT, font=FT_SMALL).pack(side="left",padx=(12,3))
        self._var_edicion_grupo = tk.StringVar(value=_GRUPO_BASE)
        self._combo_edicion_grupo = ttk.Combobox(
            tb_top2, textvariable=self._var_edicion_grupo,
            state="readonly", width=24, values=[_GRUPO_BASE],
        )
        self._combo_edicion_grupo.pack(side="left", padx=4)
        self._combo_edicion_grupo.bind("<<ComboboxSelected>>", self._cambiar_edicion_grupo)
        tk.Label(tb_top2, text="Base compartida o ajuste individual.",
                 bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(side="right",padx=4)

        self._tabla_gr = TablaDieta(tab_tg, self.catalogo, no_deseados=[], factor=1.0)
        self._tabla_gr.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # botones generar grupo
        btn_f2 = tk.Frame(f, bg=C_BG); btn_f2.pack(fill="x",padx=16,pady=(0,12))
        self._btn_gen_grupo = ttk.Button(btn_f2, text="📄  Generar PDF para cada paciente",
                                          style="Green.TButton",
                                          command=lambda: self.generar_grupo(fmt="pdf"))
        self._btn_gen_grupo.pack(side="right", ipadx=10, ipady=4, padx=(6,0))
        ttk.Button(btn_f2, text="📝  Generar Word para cada paciente",
                   style="Dark.TButton",
                   command=lambda: self.generar_grupo(fmt="docx")).pack(
                   side="right", ipadx=10, ipady=4)
        return f

    def _refrescar_checks_grupo(self):
        for w in self._frame_checks.winfo_children(): w.destroy()
        self._grupo_checks.clear()
        for p in self.pacientes:
            var = tk.BooleanVar(value=False)
            self._grupo_checks[p.nombre] = (p, var)
            ttk.Checkbutton(self._frame_checks, text=p.nombre,
                            variable=var).pack(anchor="w",pady=2,padx=4)
        # re-aplicar filtro si hay texto
        try:
            if self._var_buscar_grupo.get().strip():
                self._filtrar_checks_grupo()
        except AttributeError:
            pass

    def _sel_grupo(self, val):
        for _,(_, v) in self._grupo_checks.items(): v.set(val)

    def _comparar_grupo(self):
        grupo = [p for _,(p,v) in self._grupo_checks.items() if v.get()]
        if len(grupo)<2: messagebox.showwarning("Grupo","Selecciona al menos 2 pacientes."); return
        rep = dgrupo.comparar_gustos(grupo, self.catalogo)
        self._txt_cmp.config(state="normal"); self._txt_cmp.delete("1.0","end")
        self._txt_cmp.insert("end", f"Grupo: {', '.join(p.nombre for p in grupo)}\n")
        union = rep["no_deseados_union"]
        self._txt_cmp.insert("end", f"Evitan: {', '.join(sorted(union)) or '(ninguno)'}\n\nAptos para TODOS:\n")
        vistos=set()
        for col in config.COLUMNAS:
            t=col["tiempo"]
            if t in vistos: continue
            vistos.add(t)
            nms=[pl.nombre for pl in rep["comunes"][t]]
            self._txt_cmp.insert("end",f"  [{t:10s}] {', '.join(nms) or '(ninguno)'}\n")
        if rep["conflictos"]:
            self._txt_cmp.insert("end","\nConflictos (excluidos):\n")
            for pl,choca in rep["conflictos"]:
                q="; ".join(f"{n}→{pa}" for n,pa in choca)
                self._txt_cmp.insert("end",f"  ✖ {pl.nombre}: {q}\n")
        self._txt_cmp.config(state="disabled")
        # spinboxes de factor
        for w in self._frame_factores.winfo_children(): w.destroy()
        self._grupo_factores.clear()
        for p in grupo:
            row=tk.Frame(self._frame_factores,bg=C_BG); row.pack(fill="x",pady=2)
            tk.Label(row,text=f"{p.nombre}:",bg=C_BG,fg=C_TEXT,font=FT_BODY,
                     width=26,anchor="w").pack(side="left")
            var=tk.DoubleVar(value=1.0); self._grupo_factores[p.nombre]=(p,var)
            ttk.Spinbox(row,from_=0.5,to=3.0,increment=0.1,textvariable=var,
                        width=6,format="%.1f").pack(side="left")
            tk.Label(row,text="× porción",bg=C_BG,fg=C_MUTED,font=FT_SMALL).pack(side="left",padx=5)
        nd_union = list(union)
        self._nd_union_gr = nd_union
        self._sincronizar_selector_edicion_grupo()
        self._tabla_gr.refrescar_catalogo(no_deseados=nd_union)
        self.set_status(f"Grupo comparado — {len(grupo)} pacientes")

    def _refrescar_tabla_gr(self):
        self.catalogo.cargar()
        nd = list(getattr(self,"_nd_union_gr",[]))
        self._tabla_gr.refrescar_catalogo(self.catalogo, no_deseados=nd)
        self.set_status("↺ Catálogo refrescado en tabla de grupo")

    def _autocompletar_tabla_gr(self):
        if not self._grupo_factores:
            messagebox.showinfo("Paso previo","Usa primero 'Comparar gustos'."); return
        grupo=[p for _,(p,v) in self._grupo_checks.items() if v.get()]
        if len(grupo)<2: return
        nd_union = list(set(
            nd for p in grupo for nd in p.restricciones_alimentarias()
        ))
        self._nd_union_gr = nd_union
        try: num=int(self._spin_plan_gr.get()); col2=self._var_col2_gr.get()
        except: num=1; col2=False
        planes=dgrupo.construir_grupo(grupo,self.catalogo,numero_plan=num,incluir_colacion2=col2)
        _,plan0=planes[0]
        fac0=grupo[0].factor_porcion
        celdas_ed={}
        for dia in config.DIAS:
            fila=[]
            for ci,celda_obj in enumerate(plan0.celdas.get(dia,[])):
                if celda_obj is None: fila.append({})
                elif celda_obj.texto_especial:
                    fila.append({"titulo":celda_obj.texto_especial,"ingredientes":[],"nota":None,"video":False})
                elif celda_obj.platillo:
                    p=celda_obj.platillo
                    fila.append({"titulo":p.nombre,
                                 "ingredientes":[ing.render(fac0) for ing in p.ingredientes],
                                 "nota":p.nota,"video":p.video})
                else: fila.append({})
            celdas_ed[dia]=fila
        self._tabla_gr.set_celdas(celdas_ed)
        self._grupo_base_celdas = copy.deepcopy(celdas_ed)
        self._grupo_overrides.clear()
        self._grupo_edicion_actual = _GRUPO_BASE
        self._var_edicion_grupo.set(_GRUPO_BASE)
        self._sincronizar_selector_edicion_grupo()
        self.set_status("✔ Tabla de grupo autocompletada — puedes ajustar antes de generar.")

    def generar_grupo(self, fmt="pdf"):
        if not self._grupo_factores:
            messagebox.showinfo("Paso previo","Usa 'Comparar gustos' primero."); return
        grupo=[]
        for nombre,(p,var) in self._grupo_factores.items():
            p.factor_porcion=var.get(); grupo.append(p)
        try: num=int(self._spin_plan_gr.get()); col2=self._var_col2_gr.get()
        except: messagebox.showerror("Error","Número de plan inválido."); return

        self._guardar_edicion_actual_grupo(silencioso=True)
        celdas_manual=self._grupo_base_celdas or self._tabla_gr.get_celdas()
        tiene_contenido=any(d for fila in celdas_manual.values() for d in fila if d)

        self._btn_gen_grupo.config(state="disabled")
        self.set_status(f"Generando {len(grupo)} dietas ({fmt.upper()})…")

        def _run():
            try:
                rutas=[]
                for pac in grupo:
                    ext = generadores.extension(fmt)
                    from nutridietas.nucleo.modelos import PlanSemanal
                    plan_tmp=PlanSemanal(paciente=pac,numero_plan=num,
                                        notas_superiores=["Dieta en grupo."],celdas={})
                    nombre_base=plan_tmp.nombre_archivo().replace(".docx",ext)
                    destino=None
                    if pac.carpeta and os.path.isdir(pac.carpeta):
                        destino=os.path.join(pac.carpeta,nombre_base)
                    if tiene_contenido:
                        # tabla base del grupo, con posibles ajustes por paciente
                        celdas_origen = self._grupo_overrides.get(pac.nombre, celdas_manual)
                        celdas_pac = {}
                        for dia in config.DIAS:
                            fila_pac=[]
                            for ci,datos in enumerate(celdas_origen.get(dia,[])):
                                if not datos: fila_pac.append({})
                                else:
                                    # re-renderizar con factor del paciente
                                    platillo_orig=next(
                                        (x for x in self.catalogo.platillos
                                         if x.nombre==datos.get("titulo","")), None)
                                    if platillo_orig:
                                        fila_pac.append({
                                            "titulo":platillo_orig.nombre,
                                            "ingredientes":[ing.render(pac.factor_porcion)
                                                            for ing in platillo_orig.ingredientes],
                                            "nota":platillo_orig.nota,
                                            "video":platillo_orig.video,
                                        })
                                    else:
                                        fila_pac.append(datos)
                            celdas_pac[dia]=fila_pac
                        ruta=generadores.generar_desde_celdas_manual(
                            pac,celdas_pac,num,["Dieta en grupo."],destino,formato=fmt)
                    else:
                        planes_grupo=dgrupo.construir_grupo(grupo,self.catalogo,
                                                      numero_plan=num,incluir_colacion2=col2)
                        for pac2,plan2 in planes_grupo:
                            if pac2.nombre==pac.nombre:
                                ext2=generadores.extension(fmt)
                                dest2=None
                                if pac2.carpeta and os.path.isdir(pac2.carpeta):
                                    dest2=os.path.join(pac2.carpeta,
                                        plan2.nombre_archivo().replace(".docx",ext2))
                                ruta = generadores.generar(plan2,fmt,dest2)
                    rutas.append((pac.nombre,ruta))
                self.root.after(0, lambda r=rutas: self._gen_ok_grupo(r))
            except Exception as e:
                self.root.after(0, lambda m=str(e): self._gen_error(m))

        threading.Thread(target=_run, daemon=True).start()

    def _gen_ok_grupo(self, rutas):
        try: self._btn_gen_grupo.config(state="normal")
        except: pass
        resumen="\n".join(f"• {n}: {os.path.basename(r)}" for n,r in rutas)
        self.set_status(f"✔ {len(rutas)} dietas generadas")
        messagebox.showinfo("Grupo generado",f"Se generaron {len(rutas)} dietas:\n\n{resumen}")

    def _sincronizar_selector_edicion_grupo(self):
        opciones = [_GRUPO_BASE] + [
            p.nombre for _, (p, _var) in getattr(self, "_grupo_factores", {}).items()
        ]
        try:
            self._combo_edicion_grupo["values"] = opciones
        except AttributeError:
            return
        actual = self._var_edicion_grupo.get() or _GRUPO_BASE
        if actual not in opciones:
            actual = _GRUPO_BASE
            self._var_edicion_grupo.set(actual)
        self._grupo_edicion_actual = actual

    def _guardar_edicion_actual_grupo(self, silencioso=False):
        if not hasattr(self, "_tabla_gr"):
            return
        nombre = getattr(self, "_grupo_edicion_actual", _GRUPO_BASE)
        datos = copy.deepcopy(self._tabla_gr.get_celdas())
        if nombre == _GRUPO_BASE:
            self._grupo_base_celdas = datos
        else:
            self._grupo_overrides[nombre] = datos
        if not silencioso:
            self.set_status(f"✔ Ajuste guardado: {nombre}")

    def _cambiar_edicion_grupo(self, _=None):
        anterior = getattr(self, "_grupo_edicion_actual", _GRUPO_BASE)
        nuevo = self._var_edicion_grupo.get() or _GRUPO_BASE
        if nuevo == anterior:
            return

        self._guardar_edicion_actual_grupo(silencioso=True)
        base = self._grupo_base_celdas or self._tabla_gr.get_celdas()
        datos = self._grupo_overrides.get(nuevo, base) if nuevo != _GRUPO_BASE else base
        self._grupo_edicion_actual = nuevo
        self._tabla_gr.set_celdas(copy.deepcopy(datos))
        self._aplicar_contexto_tabla_grupo(nuevo)
        self.set_status(f"Editando tabla de grupo para: {nuevo}")

    def _aplicar_contexto_tabla_grupo(self, nombre):
        if nombre == _GRUPO_BASE:
            nd = list(getattr(self, "_nd_union_gr", []))
            self._tabla_gr.refrescar_catalogo(no_deseados=nd, factor=1.0)
            return

        item = getattr(self, "_grupo_factores", {}).get(nombre)
        if not item:
            return
        pac, var = item
        try:
            factor = float(var.get())
        except Exception:
            factor = pac.factor_porcion
        self._tabla_gr.refrescar_catalogo(
            no_deseados=pac.restricciones_alimentarias(),
            factor=factor,
        )

    # ── buscador en grupo ─────────────────────────────────────────────────── #
    def _filtrar_checks_grupo(self):
        q = self._var_buscar_grupo.get().lower().strip()
        for w in self._frame_checks.winfo_children():
            nombre = w.cget("text").lower() if hasattr(w, "cget") else ""
            try:
                if q and q not in nombre:
                    w.pack_forget()
                else:
                    w.pack(anchor="w", pady=2, padx=4)
            except Exception:
                pass

    # ── plantillas (cargar plan preestablecido) ───────────────────────────── #
