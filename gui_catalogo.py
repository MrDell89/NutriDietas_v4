# -*- coding: utf-8 -*-
"""Panel de catálogo de platillos de la GUI."""

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


class PanelCatalogoMixin:
    def _panel_catalogo(self):
        f = tk.Frame(self.content, bg=C_BG)
        hdr=tk.Frame(f,bg=C_WHITE,pady=8); hdr.pack(fill="x",padx=16,pady=(14,0))
        tk.Label(hdr,text="📋  Catálogo de Platillos",font=FT_TITLE,bg=C_WHITE,fg=C_DARK).pack(side="left",padx=10)
        ttk.Button(hdr,text="＋  Agregar",style="Green.TButton",command=self._dialogo_agregar_platillo).pack(side="right",padx=4)
        ttk.Button(hdr,text="🔍  Extraer de DOCX",style="Dark.TButton",command=self._extraer_docx_a_catalogo).pack(side="right",padx=4)
        tools=tk.Frame(f,bg=C_BG); tools.pack(fill="x",padx=16,pady=(6,2))
        tk.Label(tools,text="Buscar:",bg=C_BG,fg=C_MUTED,font=FT_BODY).pack(side="left")
        self._var_buscar_cat=tk.StringVar()
        self._var_buscar_cat.trace_add("write",lambda *a:self._cargar_catalogo_tree())
        ttk.Entry(tools,textvariable=self._var_buscar_cat,font=FT_BODY,width=22).pack(side="left",padx=6)
        self._var_filtro_t=tk.StringVar(value="todos")
        for val,txt in [("todos","Todos"),("desayuno","Desayuno"),("colacion","Colación"),("comida","Comida"),("cena","Cena")]:
            ttk.Radiobutton(tools,text=txt,variable=self._var_filtro_t,value=val,
                            command=self._cargar_catalogo_tree).pack(side="left",padx=3)
        ttk.Button(tools,text="↺ Refrescar",style="Outline.TButton",
                   command=self._refrescar_catalogo_completo).pack(side="right",padx=4)
        ttk.Button(tools,text="🗑 Eliminar",style="Outline.TButton",
                   command=self._eliminar_platillo).pack(side="right",padx=4)
        ttk.Button(tools,text="✏ Editar",style="Dark.TButton",
                   command=self._dialogo_editar_platillo).pack(side="right",padx=4)
        ttk.Button(tools,text="📊 Importar CSV",style="Outline.TButton",
                   command=self._importar_csv_catalogo).pack(side="right",padx=4)
        body=tk.Frame(f,bg=C_BG); body.pack(fill="both",expand=True,padx=16,pady=6)
        tf=tk.Frame(body,bg=C_BG); tf.pack(side="left",fill="both",expand=True,padx=(0,6))
        cols=("Nombre","Tiempo","Video","Ingr.")
        self._tree_cat=ttk.Treeview(tf,columns=cols,show="headings",selectmode="browse")
        for c,w in zip(cols,[280,88,52,50]): self._tree_cat.heading(c,text=c); self._tree_cat.column(c,width=w)
        self._tree_cat.tag_configure("alt",background="#EBF7F2")
        vsb=ttk.Scrollbar(tf,orient="vertical",command=self._tree_cat.yview)
        self._tree_cat.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y"); self._tree_cat.pack(fill="both",expand=True)
        self._tree_cat.bind("<<TreeviewSelect>>",self._on_select_platillo)
        self._tree_cat.bind("<Double-1>", lambda e: self._dialogo_editar_platillo())
        det=tk.Frame(body,bg=C_BG,width=290); det.pack(side="right",fill="y"); det.pack_propagate(False)
        tk.Label(det,text="Ingredientes",bg=C_BG,fg=C_DARK,font=FT_H3).pack(anchor="w",pady=(0,4))
        self._txt_ing=scrolledtext.ScrolledText(det,font=FT_MONO,bg=C_WHITE,fg=C_TEXT,
                                                relief="solid",bd=1,state="disabled")
        self._txt_ing.pack(fill="both",expand=True)
        self._cargar_catalogo_tree()
        return f

    def _cargar_catalogo_tree(self):
        t = self._tree_cat; t.delete(*t.get_children())
        filtro  = self._var_filtro_t.get()
        buscar  = self._var_buscar_cat.get().lower()
        lista   = self.catalogo.platillos
        if filtro != "todos": lista = [p for p in lista if p.tiempo == filtro]
        if buscar: lista = [p for p in lista if buscar in p.nombre.lower()]
        usados = set()
        for i, p in enumerate(lista):
            # "" es el ítem raíz en Tkinter — nunca usar como iid
            iid = p.id.strip() if p.id else f"_p{i}"
            if not iid:
                iid = f"_p{i}"
            # garantizar unicidad dentro de esta llamada
            base, cnt = iid, 0
            while iid in usados:
                cnt += 1; iid = f"{base}_{cnt}"
            usados.add(iid)
            try:
                t.insert("", "end", iid=iid, tags=("alt" if i % 2 else "",),
                         values=(p.nombre, p.tiempo, "✓" if p.video else "", len(p.ingredientes)))
            except Exception:
                # último recurso: insertar sin iid específico
                t.insert("", "end", tags=("alt" if i % 2 else "",),
                         values=(p.nombre, p.tiempo, "✓" if p.video else "", len(p.ingredientes)))

    def _on_select_platillo(self,_=None):
        sel=self._tree_cat.selection()
        if not sel: return
        p=next((x for x in self.catalogo.platillos if x.id==sel[0]),None)
        if not p: return
        self._txt_ing.config(state="normal"); self._txt_ing.delete("1.0","end")
        self._txt_ing.insert("end",f"{p.nombre}\n[{p.tiempo}]"+("  📹" if p.video else "")+"\n\n")
        for ing in p.ingredientes: self._txt_ing.insert("end","• "+ing.render()+"\n")
        if p.nota: self._txt_ing.insert("end",f"\n📌 {p.nota}\n")
        self._txt_ing.config(state="disabled")

    def _eliminar_platillo(self):
        sel=self._tree_cat.selection()
        if not sel: messagebox.showinfo("Selección","Selecciona un platillo primero."); return
        p=next((x for x in self.catalogo.platillos if x.id==sel[0]),None)
        if p and messagebox.askyesno("Eliminar",f"¿Eliminar '{p.nombre}'?"):
            self.catalogo.platillos=[x for x in self.catalogo.platillos if x.id!=sel[0]]
            self.catalogo.guardar(); self._cargar_catalogo_tree()
            self.set_status(f"'{p.nombre}' eliminado.")

    # ── extraer platillos desde DOCX al catálogo ─────────────────────────── #
    def _extraer_docx_a_catalogo(self):
        """
        Usa extractor_planes_alimenticios.py para leer carpetas de DOCX
        y agrega los platillos nuevos directamente a catalogo_platos.json.
        Omite automáticamente los que ya existen por ID o nombre.
        """
        # Verificar que el extractor esté disponible
        try:
            import extractor_planes_alimenticios as _ext
        except ImportError:
            messagebox.showerror(
                "Módulo no encontrado",
                "No se encontró 'extractor_planes_alimenticios.py'.\n"
                "Asegúrate de que esté en la misma carpeta que gui.pyw.")
            return

        carpeta = filedialog.askdirectory(
            title="Selecciona carpeta con archivos Word (.docx) de planes alimenticios")
        if not carpeta:
            return

        from pathlib import Path as _Path

        archivos = sorted(_Path(carpeta).glob("*.docx"))
        if not archivos:
            messagebox.showwarning("Sin archivos",
                f"No se encontraron archivos .docx en:\n{carpeta}")
            return

        # ventana de progreso
        prog = tk.Toplevel(self.root)
        prog.title("Extrayendo platillos…")
        prog.geometry("540x380"); prog.configure(bg=C_DARK); prog.grab_set()
        prog.resizable(False, False)
        tk.Label(prog, text="🔍  Extrayendo platillos de archivos Word",
                 bg=C_DARK, fg=C_WHITE, font=FT_H3).pack(anchor="w", padx=16, pady=(14,4))
        lbl_arch = tk.Label(prog, text="Iniciando…", bg=C_DARK, fg="#8ECFBF", font=FT_SMALL)
        lbl_arch.pack(anchor="w", padx=16)
        pbar = ttk.Progressbar(prog, length=480, maximum=len(archivos), mode="determinate")
        pbar.pack(padx=16, pady=8)

        from tkinter import scrolledtext as _st
        log_txt = _st.ScrolledText(prog, height=10, font=FT_MONO,
                                   bg="#0A1F1A", fg="#A8D5C5",
                                   relief="flat", state="normal")
        log_txt.pack(fill="both", expand=True, padx=16, pady=(0,8))
        log_txt.tag_config("ok",    foreground="#69F0AE")
        log_txt.tag_config("warn",  foreground="#FFD740")
        log_txt.tag_config("error", foreground="#FF5252")
        log_txt.tag_config("info",  foreground="#82B1FF")

        def _log(msg, tag="info"):
            log_txt.config(state="normal")
            log_txt.insert("end", msg + "\n", tag)
            log_txt.see("end")
            log_txt.config(state="disabled")

        ids_existentes    = {p.id     for p in self.catalogo.platillos}
        nombres_existentes = {p.nombre.lower() for p in self.catalogo.platillos}

        def _run():
            todos = []
            vistas_batch = set()   # dedup dentro del mismo lote
            for i, arch in enumerate(archivos, 1):
                self.root.after(0, lambda a=arch, idx=i: [
                    lbl_arch.config(text=f"[{idx}/{len(archivos)}] {a.name}"),
                    pbar.config(value=idx)])
                try:
                    platillos = _ext.procesar_docx(str(arch))
                    nuevos_arch = 0
                    for p in platillos:
                        nombre_low = p["nombre"].lower()
                        pid_orig   = p["id"]
                        # omitir si ya existe por nombre
                        if nombre_low in nombres_existentes or nombre_low in vistas_batch:
                            continue
                        # hacer ID único si colisiona
                        pid_u, cnt = pid_orig, 0
                        while pid_u in ids_existentes or pid_u in {t["id"] for t in todos}:
                            cnt += 1; pid_u = f"{pid_orig}_{cnt}"
                        p["id"] = pid_u
                        todos.append(p)
                        vistas_batch.add(nombre_low)
                        ids_existentes.add(pid_u)
                        nuevos_arch += 1
                    self.root.after(0, _log, f"  ✔ {arch.name}: {nuevos_arch} nuevos", "ok")
                except Exception as e:
                    self.root.after(0, _log, f"  ✗ {arch.name}: {e}", "error")

            self.root.after(0, lambda: _finalizar(todos))

        def _finalizar(todos):
            if not todos:
                _log("⚠ No se encontraron platillos nuevos (todos ya existen).", "warn")
                ttk.Button(prog, text="Cerrar", command=prog.destroy).pack(pady=6)
                return
            _log(f"\n{'─'*50}", "info")
            _log(f"✅  Total de platillos nuevos encontrados: {len(todos)}", "ok")
            _log("Selecciona cuáles agregar al catálogo:", "info")

            # listbox de selección
            lb_frame = tk.Frame(prog, bg=C_DARK); lb_frame.pack(fill="x", padx=16, pady=4)
            lb = tk.Listbox(lb_frame, font=FT_SMALL, selectmode="multiple",
                            bg=C_WHITE, fg=C_TEXT, relief="solid", bd=1, height=8)
            lb.pack(fill="x")
            for p in todos:
                lb.insert("end", f"{p['nombre']}  [{p['tiempo']}]  ({len(p['ingredientes'])} ingr.)")
            lb.select_set(0, "end")

            def _agregar():
                sel = lb.curselection()
                agregados = 0
                for i in sel:
                    p = todos[i]
                    from modelos import Platillo as _Pl, Ingrediente as _Ing
                    ings = [_Ing(nombre=ig["nombre"],
                                 cantidad=ig.get("cantidad"),
                                 unidad=ig.get("unidad",""))
                            for ig in p.get("ingredientes",[])]
                    self.catalogo.agregar_platillo(_Pl(
                        id=p["id"], nombre=p["nombre"], tiempo=p["tiempo"],
                        ingredientes=ings, video=p.get("video", False),
                        nota=p.get("nota")))
                    agregados += 1
                self.catalogo.guardar()
                self.root.after(0, self._cargar_catalogo_tree)
                self.set_status(f"✔ {agregados} platillos extraídos de DOCX y guardados en el JSON.")
                prog.destroy()
                messagebox.showinfo("Listo",
                    f"Se agregaron {agregados} platillos al catálogo.\n"
                    f"Guardados directamente en:\n{self.catalogo.ruta}")

            bf_fin = tk.Frame(prog, bg=C_DARK); bf_fin.pack(fill="x", padx=16, pady=(0,10))
            ttk.Button(bf_fin, text="Cancelar", style="Outline.TButton",
                       command=prog.destroy).pack(side="right", padx=4)
            ttk.Button(bf_fin, text=f"✔ Agregar seleccionados al JSON",
                       style="Green.TButton", command=_agregar).pack(side="right", padx=4)

        threading.Thread(target=_run, daemon=True).start()

    # ── editar platillo existente ─────────────────────────────────────────── #
    def _dialogo_editar_platillo(self):
        sel = self._tree_cat.selection()
        if not sel:
            messagebox.showinfo("Selección", "Selecciona un platillo del catálogo primero.")
            return
        # buscar por iid (puede ser el id real o el fallback _pN)
        iid = sel[0]
        platillo = next((x for x in self.catalogo.platillos if x.id == iid), None)
        if not platillo:
            # fallback: buscar por nombre si el iid fue modificado
            platillo = next((x for x in self.catalogo.platillos
                             if x.nombre == self._tree_cat.item(iid, "values")[0]), None)
        if not platillo:
            messagebox.showerror("Error", "No se pudo identificar el platillo seleccionado.")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Editar — {platillo.nombre}")
        dlg.geometry("560x640"); dlg.configure(bg=C_BG); dlg.grab_set(); dlg.resizable(True, True)

        # ── encabezado ──────────────────────────────────────────────────── #
        hdr_e = tk.Frame(dlg, bg=C_DARK, height=46); hdr_e.pack(fill="x"); hdr_e.pack_propagate(False)
        tk.Label(hdr_e, text="✏  Editar platillo", bg=C_DARK, fg=C_WHITE,
                 font=FT_H3).pack(side="left", padx=14, pady=10)

        frm = tk.Frame(dlg, bg=C_BG, padx=18, pady=10); frm.pack(fill="both", expand=True)

        def lbl_entry(parent, label, valor="", width=38):
            r = tk.Frame(parent, bg=C_BG); r.pack(fill="x", pady=4)
            tk.Label(r, text=label, bg=C_BG, fg=C_TEXT, font=FT_BODY,
                     width=14, anchor="w").pack(side="left")
            v = tk.StringVar(value=valor)
            e = ttk.Entry(r, textvariable=v, width=width, font=FT_BODY)
            e.pack(side="left", fill="x", expand=True)
            return v, e

        # ── ID ──────────────────────────────────────────────────────────── #
        v_id, e_id = lbl_entry(frm, "ID:", platillo.id)
        lbl_id_err = tk.Label(frm, text="", bg=C_BG, fg=C_ERROR, font=FT_SMALL)
        lbl_id_err.pack(anchor="w", padx=(116, 0))

        def _validar_id(*_):
            nuevo_id = v_id.get().strip()
            if not nuevo_id:
                lbl_id_err.config(text="⚠ El ID no puede estar vacío.")
                return False
            if nuevo_id != platillo.id:
                conflicto = next((p for p in self.catalogo.platillos
                                  if p.id == nuevo_id and p is not platillo), None)
                if conflicto:
                    lbl_id_err.config(text=f"⛔ ID ya usado por: \"{conflicto.nombre}\"")
                    return False
            lbl_id_err.config(text="")
            return True

        v_id.trace_add("write", _validar_id)

        # ── Nombre ──────────────────────────────────────────────────────── #
        v_nombre, _ = lbl_entry(frm, "Nombre:", platillo.nombre)
        lbl_nom_err = tk.Label(frm, text="", bg=C_BG, fg=C_ERROR, font=FT_SMALL)
        lbl_nom_err.pack(anchor="w", padx=(116, 0))

        # ── Nota ────────────────────────────────────────────────────────── #
        v_nota, _ = lbl_entry(frm, "Nota al pie:", platillo.nota or "")

        # ── Tiempo ──────────────────────────────────────────────────────── #
        r_t = tk.Frame(frm, bg=C_BG); r_t.pack(fill="x", pady=4)
        tk.Label(r_t, text="Tiempo:", bg=C_BG, fg=C_TEXT, font=FT_BODY,
                 width=14, anchor="w").pack(side="left")
        v_tiempo = tk.StringVar(value=platillo.tiempo)
        for val in ("desayuno", "colacion", "comida", "cena"):
            ttk.Radiobutton(r_t, text=val, variable=v_tiempo, value=val).pack(side="left", padx=4)

        # ── Video ───────────────────────────────────────────────────────── #
        r_v = tk.Frame(frm, bg=C_BG); r_v.pack(fill="x", pady=4)
        v_video = tk.BooleanVar(value=platillo.video)
        ttk.Checkbutton(r_v, text="📹  Tiene video instructivo", variable=v_video).pack(side="left")

        # ── Ingredientes ────────────────────────────────────────────────── #
        tk.Label(frm, text='Ingredientes — "Nombre | cantidad | unidad"',
                 font=FT_H3, bg=C_BG, fg=C_DARK).pack(anchor="w", pady=(10, 2))
        tk.Label(frm, text='Ejemplo:  Pechuga de pollo | 180 | gramos     '
                           '(deja cantidad vacía para "al gusto")',
                 bg=C_BG, fg=C_MUTED, font=FT_SMALL).pack(anchor="w")
        txt_ing = tk.Text(frm, height=9, font=FT_MONO, relief="solid", bd=1,
                          bg=C_WHITE, fg=C_TEXT, undo=True)
        txt_ing.pack(fill="both", expand=True, pady=(4, 0))

        # pre-llenar ingredientes en el mismo formato de entrada
        for ing in platillo.ingredientes:
            cant_str = str(ing.cantidad) if ing.cantidad is not None else ""
            txt_ing.insert("end", f"{ing.nombre} | {cant_str} | {ing.unidad}\n")

        # ── botones ─────────────────────────────────────────────────────── #
        bf = tk.Frame(dlg, bg=C_BG, padx=18, pady=10); bf.pack(fill="x")

        def _guardar():
            nuevo_id    = v_id.get().strip()
            nuevo_nombre = v_nombre.get().strip()

            # validaciones
            if not nuevo_id:
                messagebox.showerror("ID inválido", "El ID no puede estar vacío.", parent=dlg)
                return
            if not nuevo_nombre:
                messagebox.showerror("Nombre vacío", "El nombre no puede estar vacío.", parent=dlg)
                return
            # conflicto de ID con OTRO platillo
            if nuevo_id != platillo.id:
                conflicto = next((p for p in self.catalogo.platillos
                                  if p.id == nuevo_id and p is not platillo), None)
                if conflicto:
                    messagebox.showerror(
                        "ID duplicado",
                        f"El ID \"{nuevo_id}\" ya está siendo usado por:\n\n"
                        f"  • {conflicto.nombre} [{conflicto.tiempo}]\n\n"
                        f"Elige un ID diferente.", parent=dlg)
                    return
            # conflicto de nombre con OTRO platillo
            if nuevo_nombre.lower() != platillo.nombre.lower():
                conflicto_nom = next((p for p in self.catalogo.platillos
                                      if p.nombre.lower() == nuevo_nombre.lower()
                                      and p is not platillo), None)
                if conflicto_nom:
                    if not messagebox.askyesno(
                        "Nombre similar",
                        f"Ya existe un platillo llamado \"{conflicto_nom.nombre}\".\n"
                        f"¿Deseas guardar de todas formas?", parent=dlg):
                        return

            # parsear ingredientes
            ings_nuevos = []
            for linea in txt_ing.get("1.0", "end").splitlines():
                partes = [x.strip() for x in linea.split("|")]
                if not partes[0]: continue
                try:
                    cant = float(partes[1]) if len(partes) > 1 and partes[1] else None
                except ValueError:
                    cant = None
                unid = partes[2] if len(partes) > 2 else ""
                ings_nuevos.append(Ingrediente(nombre=partes[0], cantidad=cant, unidad=unid))

            # aplicar cambios directamente al objeto
            platillo.id          = nuevo_id
            platillo.nombre      = nuevo_nombre
            platillo.tiempo      = v_tiempo.get()
            platillo.video       = v_video.get()
            platillo.nota        = v_nota.get().strip() or None
            platillo.ingredientes = ings_nuevos

            self.catalogo.guardar()
            self._cargar_catalogo_tree()
            self._on_select_platillo()   # refrescar panel de detalle
            self.set_status(f"✔ Platillo \"{platillo.nombre}\" actualizado.")
            dlg.destroy()

        ttk.Button(bf, text="Cancelar", style="Outline.TButton",
                   command=dlg.destroy).pack(side="right", padx=4)
        ttk.Button(bf, text="💾  Guardar cambios", style="Green.TButton",
                   command=_guardar).pack(side="right", padx=4)

        # foco inicial en el campo nombre
        e_id.focus_set()

    def _refrescar_catalogo_completo(self):
        """Recarga el JSON y actualiza la vista del catálogo."""
        self.catalogo.cargar()
        self._cargar_catalogo_tree()
        self.set_status(f"↺ Catálogo refrescado — {len(self.catalogo.platillos)} platillos")

    def _importar_csv_catalogo(self):
        """Importa platillos desde un CSV (mismo formato de exportación) directamente al JSON."""
        import csv as _csv
        ruta = filedialog.askopenfilename(
            title="Importar platillos desde CSV",
            filetypes=[("CSV", "*.csv"), ("Todos", "*")])
        if not ruta: return
        try:
            nombres_existentes = {p.nombre.lower() for p in self.catalogo.platillos}
            ids_existentes     = {p.id for p in self.catalogo.platillos}
            platillos_tmp: dict = {}  # pid → {"platillo":…, "ings":[]}
            with open(ruta, "r", encoding="utf-8-sig") as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    nombre = row.get("Nombre","").strip()
                    if not nombre: continue
                    tiempo = row.get("Tiempo","comida").strip().lower()
                    pid    = row.get("ID","").strip() or nombre.lower().replace(" ","_")[:30]
                    if nombre.lower() in nombres_existentes:
                        continue  # ya existe, saltar
                    if pid not in platillos_tmp:
                        # generar pid único
                        pid_u, cnt = pid, 0
                        while pid_u in ids_existentes or pid_u in {v["pid"] for v in platillos_tmp.values()}:
                            cnt += 1; pid_u = f"{pid}_{cnt}"
                        platillos_tmp[nombre] = {
                            "pid":  pid_u,
                            "nombre": nombre,
                            "tiempo": tiempo,
                            "video":  row.get("Video","").strip().lower() in ("sí","si","true","1"),
                            "nota":   row.get("Nota","").strip() or None,
                            "ings":   []
                        }
                    ing_nombre = row.get("Ingrediente","").strip()
                    if ing_nombre:
                        try: cant = float(row.get("Cantidad","")) if row.get("Cantidad","").strip() else None
                        except: cant = None
                        platillos_tmp[nombre]["ings"].append(
                            Ingrediente(nombre=ing_nombre, cantidad=cant,
                                        unidad=row.get("Unidad","").strip()))
            if not platillos_tmp:
                messagebox.showinfo("Sin platillos nuevos",
                    "Todos los platillos del CSV ya están en el catálogo."); return
            # confirmar con preview
            dlg = tk.Toplevel(self.root)
            dlg.title("Importar desde CSV"); dlg.geometry("480x380")
            dlg.configure(bg=C_BG); dlg.grab_set()
            tk.Label(dlg, text=f"Se encontraron {len(platillos_tmp)} platillos nuevos:",
                     bg=C_BG, fg=C_DARK, font=FT_H3).pack(anchor="w",padx=14,pady=(12,4))
            lb = tk.Listbox(dlg, font=FT_SMALL, selectmode="multiple",
                            bg=C_WHITE, fg=C_TEXT, relief="solid", bd=1)
            lb.pack(fill="both", expand=True, padx=14, pady=4)
            nombres_csv = list(platillos_tmp.keys())
            for nm in nombres_csv:
                lb.insert("end", f"{nm}  [{platillos_tmp[nm]['tiempo']}]  "
                          f"({len(platillos_tmp[nm]['ings'])} ingr.)")
            lb.select_set(0, "end")
            def _ok():
                sel = lb.curselection()
                agregados = 0
                for i in sel:
                    nm = nombres_csv[i]
                    d  = platillos_tmp[nm]
                    self.catalogo.agregar_platillo(Platillo(
                        id=d["pid"], nombre=d["nombre"], tiempo=d["tiempo"],
                        ingredientes=d["ings"], video=d["video"], nota=d["nota"]))
                    agregados += 1
                self.catalogo.guardar(); self._cargar_catalogo_tree(); dlg.destroy()
                self.set_status(f"✔ {agregados} platillos importados desde CSV al JSON.")
                messagebox.showinfo("Importado", f"{agregados} platillos agregados al catálogo.")
            bf = tk.Frame(dlg,bg=C_BG); bf.pack(fill="x",padx=14,pady=8)
            ttk.Button(bf,text="Cancelar",style="Outline.TButton",command=dlg.destroy).pack(side="right",padx=4)
            ttk.Button(bf,text="Agregar al catálogo.json",style="Green.TButton",command=_ok).pack(side="right",padx=4)
        except Exception as e:
            messagebox.showerror("Error al importar CSV", str(e))

    def _dialogo_agregar_platillo(self):
        dlg=tk.Toplevel(self.root); dlg.title("Agregar platillo")
        dlg.geometry("500x560"); dlg.configure(bg=C_BG); dlg.grab_set(); dlg.resizable(False,False)
        tk.Label(dlg,text="Nuevo platillo",font=FT_TITLE,bg=C_BG,fg=C_DARK).pack(pady=(16,6),padx=18,anchor="w")
        frm=tk.Frame(dlg,bg=C_BG,padx=18); frm.pack(fill="x")
        def row_e(label):
            r=tk.Frame(frm,bg=C_BG); r.pack(fill="x",pady=4)
            tk.Label(r,text=label,bg=C_BG,fg=C_TEXT,font=FT_BODY,width=14,anchor="w").pack(side="left")
            v=tk.StringVar(); ttk.Entry(r,textvariable=v,width=32,font=FT_BODY).pack(side="left"); return v
        v_nombre=row_e("Nombre:"); v_nota=row_e("Nota al pie:")
        r2=tk.Frame(frm,bg=C_BG); r2.pack(fill="x",pady=4)
        tk.Label(r2,text="Tiempo:",bg=C_BG,fg=C_TEXT,font=FT_BODY,width=14,anchor="w").pack(side="left")
        v_tiempo=tk.StringVar(value="comida")
        for val in ("desayuno","colacion","comida","cena"):
            ttk.Radiobutton(r2,text=val,variable=v_tiempo,value=val).pack(side="left",padx=3)
        r3=tk.Frame(frm,bg=C_BG); r3.pack(fill="x",pady=4)
        v_video=tk.BooleanVar(value=False)
        ttk.Checkbutton(r3,text="Tiene video",variable=v_video).pack(side="left")
        tk.Label(dlg,text='Ingredientes — "Nombre | cantidad | unidad"',font=FT_H3,bg=C_BG,fg=C_DARK).pack(anchor="w",padx=18,pady=(10,2))
        tk.Label(dlg,text="Deja cantidad vacía para 'al gusto'.",bg=C_BG,fg=C_MUTED,font=FT_SMALL).pack(anchor="w",padx=18)
        txt=tk.Text(dlg,height=8,font=FT_MONO,relief="solid",bd=1,bg=C_WHITE,fg=C_TEXT)
        txt.pack(fill="x",padx=18,pady=6)
        txt.insert("end","Pechuga de pollo | 180 | gramos\nAceite de oliva | 1 | cc\n")
        def guardar():
            nombre=v_nombre.get().strip()
            if not nombre: messagebox.showerror("Error","El nombre es obligatorio.",parent=dlg); return
            ings=[]
            for linea in txt.get("1.0","end").splitlines():
                partes=[x.strip() for x in linea.split("|")]
                if not partes[0]: continue
                try: cant=float(partes[1]) if len(partes)>1 and partes[1] else None
                except: cant=None
                unid=partes[2] if len(partes)>2 else ""
                ings.append(Ingrediente(nombre=partes[0],cantidad=cant,unidad=unid))
            pid=nombre.lower().replace(" ","_")[:30]
            self.catalogo.agregar_platillo(Platillo(id=pid,nombre=nombre,tiempo=v_tiempo.get(),
                                                    ingredientes=ings,video=v_video.get(),
                                                    nota=v_nota.get().strip() or None))
            self.catalogo.guardar(); self._cargar_catalogo_tree()
            self.set_status(f"'{nombre}' agregado al catálogo."); dlg.destroy()
        bf=tk.Frame(dlg,bg=C_BG); bf.pack(fill="x",padx=18,pady=10)
        ttk.Button(bf,text="Cancelar",style="Outline.TButton",command=dlg.destroy).pack(side="right",padx=4)
        ttk.Button(bf,text="Guardar",style="Green.TButton",command=guardar).pack(side="right",padx=4)

    # ════════════════════════════════════════════════════════════════════════ #
    #  PANEL CONFIGURACIÓN                                                     #
    # ════════════════════════════════════════════════════════════════════════ #
