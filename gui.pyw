# -*- coding: utf-8 -*-
"""
gui.py  —  NutriDietas (Interfaz Gráfica)
=========================================
Ejecuta:  python gui.py
"""

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

# ── Paleta (desde config: única fuente de verdad) ───────────────────────────── #
C_GREEN   = config.ui(config.COLOR_VERDE_ENCABEZADO)
C_DARK    = config.ui(config.COLOR_VERDE_TITULO)
C_HOVER   = config.ui(config.COLOR_HOVER)
C_ACTIVE  = config.ui(config.COLOR_ACTIVE)
C_BG      = config.ui(config.COLOR_FONDO)
C_WHITE   = config.ui(config.COLOR_BLANCO)
C_BORDER  = config.ui(config.COLOR_BORDE_UI)
C_TEXT    = config.ui(config.COLOR_TEXTO)
C_MUTED   = config.ui(config.COLOR_TEXTO_TENUE)
C_ERROR   = config.ui(config.COLOR_ERROR)
C_SIDEBAR = config.ui(config.COLOR_SIDEBAR)
C_ACCENT  = config.ui(config.COLOR_ACENTO)

FT_TITLE = ("Segoe UI", 15, "bold"); FT_H3 = ("Segoe UI", 10, "bold")
FT_BODY  = ("Segoe UI", 10);        FT_SMALL = ("Segoe UI", 9)
FT_BTN   = ("Segoe UI", 10, "bold"); FT_NAV = ("Segoe UI", 11)
FT_MONO  = ("Consolas", 9)


# ═══════════════════════════════════════════════════════════════════════════ #
class NutriApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NutriDietas — Lic. Juan Pablo Espino")
        self.root.geometry("1280x780"); self.root.minsize(960, 620)
        self.root.configure(bg=C_BG)

        self.catalogo   = Catalogo()
        self.pacientes  = []
        self._panel_activo = None
        self._nav_btns  = {}; self._panels = {}
        self._grupo_checks  = {}; self._grupo_factores = {}
        self._status_text   = tk.StringVar(value="Listo")

        try:
            self._setup_estilos()
            self._build_header()
            self._build_statusbar()
            self._build_body()
            try:
                import atajos; atajos.registrar(self)
            except ImportError: pass
            self.root.after(120, self._carga_inicial)
        except Exception as err:
            import traceback
            detalle = traceback.format_exc()
            print("ERROR AL INICIAR:\n", detalle)   # log en consola para debug
            # NO hacer raise — mostrar error pero dejar la ventana abierta
            messagebox.showerror("Error al iniciar",
                f"{err}\n\nEl programa intentará continuar.\n"
                f"Revisa la consola para el detalle completo.")

    # ── ESTILOS ───────────────────────────────────────────────────────────── #
    def _setup_estilos(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Treeview", background=C_WHITE, foreground=C_TEXT,
                    fieldbackground=C_WHITE, font=FT_BODY, rowheight=26)
        s.configure("Treeview.Heading", background=C_DARK, foreground=C_WHITE,
                    font=FT_H3, relief="flat")
        s.map("Treeview", background=[("selected", C_GREEN)],
              foreground=[("selected", C_WHITE)])
        s.map("Treeview.Heading", background=[("active", C_HOVER)])
        for nom, bg, fg in [("Green",C_GREEN,"white"),
                            ("Dark",C_DARK,"white"),
                            ("Outline",C_BG,C_DARK)]:
            s.configure(f"{nom}.TButton", background=bg, foreground=fg,
                        font=FT_BTN, padding=(10,5), relief="flat",
                        borderwidth=0 if nom!="Outline" else 1,
                        focuscolor="none")
        s.map("Green.TButton",   background=[("active",C_HOVER)])
        s.map("Dark.TButton",    background=[("active",C_SIDEBAR)])
        s.map("Outline.TButton", background=[("active",C_ACCENT)])
        s.configure("TNotebook", background=C_BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=C_BORDER, foreground=C_TEXT,
                    font=FT_BODY, padding=(12,5))
        s.map("TNotebook.Tab", background=[("selected",C_GREEN)],
              foreground=[("selected",C_WHITE)])
        s.configure("TLabelframe", background=C_BG, bordercolor=C_BORDER)
        s.configure("TLabelframe.Label", background=C_BG,
                    foreground=C_DARK, font=FT_H3)

    # ── HEADER ────────────────────────────────────────────────────────────── #
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C_DARK, height=54)
        hdr.pack(fill="x", side="top"); hdr.pack_propagate(False)
        tk.Label(hdr, text="NutriDietas", bg=C_DARK, fg=C_WHITE,
                 font=("Segoe UI",17,"bold")).pack(side="left",padx=(18,6),pady=8)
        tk.Label(hdr, text="Lic. Juan Pablo Espino", bg=C_DARK, fg="#8ECFBF",
                 font=FT_BODY).pack(side="left",pady=8)
        for txt,cmd in [("⚙  Config",lambda:self.navegar("config")),
                        ("✖  Salir",self.root.destroy)]:
            tk.Button(hdr, text=txt, bg=C_SIDEBAR, fg=C_WHITE,
                      font=FT_SMALL, bd=0, cursor="hand2", padx=10, pady=5,
                      activebackground=C_HOVER, activeforeground=C_WHITE,
                      command=cmd).pack(side="right",padx=4,pady=8)

    # ── STATUS BAR ───────────────────────────────────────────────────────── #
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=C_DARK, height=26)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)
        self._lbl_status = tk.Label(bar, textvariable=self._status_text,
                                    bg=C_DARK, fg="#8ECFBF",
                                    font=FT_SMALL, anchor="w", padx=12)
        self._lbl_status.pack(side="left", fill="y")
        tk.Label(bar, text="Ctrl+? = ayuda  |  Ctrl+K = autocompletar  |  Ctrl+L = limpiar  |  Ctrl+M = masivas",
                 bg=C_DARK, fg="#3A6A5E", font=FT_SMALL,
                 anchor="e", padx=12).pack(side="right", fill="y")

    def set_status(self, msg, color=None):
        self._status_text.set(msg)
        self._lbl_status.config(fg=color or "#8ECFBF")
        self.root.update_idletasks()

    # ── BODY ──────────────────────────────────────────────────────────────── #
    def _build_body(self):
        body = tk.Frame(self.root, bg=C_BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self.content = tk.Frame(body, bg=C_BG)
        self.content.pack(fill="both", expand=True, side="left")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        for nombre, builder in [
            ("pacientes",  self._panel_pacientes),
            ("individual", self._panel_individual),
            ("grupo",      self._panel_grupo),
            ("catalogo",   self._panel_catalogo),
            ("config",     self._panel_config),
        ]:
            f = builder()
            f.grid(row=0, column=0, sticky="nsew")
            self._panels[nombre] = f
        self.navegar("pacientes")

    # ── SIDEBAR ───────────────────────────────────────────────────────────── #
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C_SIDEBAR, width=192)
        sb.pack(fill="y", side="left"); sb.pack_propagate(False)
        tk.Frame(sb, bg=C_SIDEBAR, height=10).pack()
        for key, icon, label in [
            ("pacientes","👥","Pacientes"),
            ("individual","🍽","Dieta Individual"),
            ("grupo","👫","Dieta en Grupo"),
            ("catalogo","📋","Catálogo"),
            ("config","⚙","Configuración"),
        ]:
            frm = tk.Frame(sb, bg=C_SIDEBAR, cursor="hand2"); frm.pack(fill="x",pady=1)
            lbl = tk.Label(frm, text=f"  {icon}  {label}", bg=C_SIDEBAR, fg=C_WHITE,
                           font=FT_NAV, anchor="w", padx=8, pady=9)
            lbl.pack(fill="x")
            self._nav_btns[key] = (frm, lbl)
            for w in (frm, lbl):
                w.bind("<Button-1>", lambda e,k=key: self.navegar(k))
                w.bind("<Enter>",    lambda e,k=key: self._nav_hover(k,True))
                w.bind("<Leave>",    lambda e,k=key: self._nav_hover(k,False))
        tk.Frame(sb,bg=C_DARK,height=1).pack(fill="x",pady=(16,4))
        tk.Label(sb, text="python gui.py", bg=C_SIDEBAR, fg="#3A6A5E",
                 font=("Segoe UI",8)).pack(side="bottom",pady=6)

    def _nav_hover(self,key,entering):
        if key == self._panel_activo: return
        c = C_HOVER if entering else C_SIDEBAR
        frm,lbl = self._nav_btns[key]; frm.config(bg=c); lbl.config(bg=c)

    def navegar(self, panel):
        for k,(frm,lbl) in self._nav_btns.items():
            active = k == panel
            c = C_GREEN if active else C_SIDEBAR
            frm.config(bg=c); lbl.config(bg=c)
        self._panels[panel].tkraise()
        self._panel_activo = panel
        # Sin auto-recarga en cada navegación — usa el botón ↺ Recargar

    # ════════════════════════════════════════════════════════════════════════ #
    #  PANEL PACIENTES                                                         #
    # ════════════════════════════════════════════════════════════════════════ #
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
        from modelos import PlanSemanal
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
    def _panel_grupo(self):
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
        tk.Label(tb_top2, text="Mismo platillo para todos, porciones individuales al generar.",
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
        nd_union=list(set(nd for p in grupo for nd in p.no_deseados))
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
        self.set_status("✔ Tabla de grupo autocompletada — puedes ajustar antes de generar.")

    def generar_grupo(self, fmt="pdf"):
        if not self._grupo_factores:
            messagebox.showinfo("Paso previo","Usa 'Comparar gustos' primero."); return
        grupo=[]
        for nombre,(p,var) in self._grupo_factores.items():
            p.factor_porcion=var.get(); grupo.append(p)
        try: num=int(self._spin_plan_gr.get()); col2=self._var_col2_gr.get()
        except: messagebox.showerror("Error","Número de plan inválido."); return

        celdas_manual=self._tabla_gr.get_celdas()
        tiene_contenido=any(d for fila in celdas_manual.values() for d in fila if d)

        self._btn_gen_grupo.config(state="disabled")
        self.set_status(f"Generando {len(grupo)} dietas ({fmt.upper()})…")

        def _run():
            try:
                rutas=[]
                for pac in grupo:
                    ext = generadores.extension(fmt)
                    from modelos import PlanSemanal
                    plan_tmp=PlanSemanal(paciente=pac,numero_plan=num,
                                        notas_superiores=["Dieta en grupo."],celdas={})
                    nombre_base=plan_tmp.nombre_archivo().replace(".docx",ext)
                    destino=None
                    if pac.carpeta and os.path.isdir(pac.carpeta):
                        destino=os.path.join(pac.carpeta,nombre_base)
                    if tiene_contenido:
                        # misma tabla, factor individual
                        celdas_pac = {}
                        for dia in config.DIAS:
                            fila_pac=[]
                            for ci,datos in enumerate(celdas_manual.get(dia,[])):
                                if not datos: fila_pac.append({})
                                else:
                                    from modelos import Platillo,Ingrediente
                                    ings_nuevos=[]
                                    p_tmp=Platillo(id="tmp",nombre=datos.get("titulo",""),
                                                   tiempo=config.COLUMNAS[ci]["tiempo"])
                                    raw_ings=datos.get("ingredientes",[])
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
    def _panel_config(self):
        f=tk.Frame(self.content,bg=C_BG); tk.Frame(f,bg=C_BG,height=20).pack()
        tk.Label(f,text="⚙  Configuración",font=FT_TITLE,bg=C_BG,fg=C_DARK).pack(anchor="w",padx=26,pady=(0,14))
        def campo(parent,label,getter,setter,es_dir=True):
            r=tk.Frame(parent,bg=C_BG); r.pack(fill="x",pady=6)
            tk.Label(r,text=label,bg=C_BG,fg=C_TEXT,font=FT_BODY,width=22,anchor="w").pack(side="left")
            var=tk.StringVar(value=getter()); ttk.Entry(r,textvariable=var,font=FT_SMALL,width=40).pack(side="left",padx=(0,6))
            def _b(v=var,s=setter,d=es_dir):
                r2=(filedialog.askdirectory() if d else filedialog.askopenfilename(filetypes=[("PNG","*.png"),("Todos","*")]))
                if r2: v.set(r2); s(r2)
            ttk.Button(r,text="📂",style="Outline.TButton",command=_b,width=3).pack(side="left")
        lf=ttk.LabelFrame(f,text="Rutas",padding=10); lf.pack(fill="x",padx=26,pady=(0,12))
        campo(lf,"Carpeta de pacientes:",lambda:config.CARPETA_PACIENTES,lambda v:setattr(config,"CARPETA_PACIENTES",v))
        campo(lf,"Carpeta de salidas:",lambda:config.CARPETA_SALIDAS,lambda v:setattr(config,"CARPETA_SALIDAS",v))
        campo(lf,"Logo (PNG):",lambda:config.RUTA_LOGO,lambda v:setattr(config,"RUTA_LOGO",v),es_dir=False)
        lf2=ttk.LabelFrame(f,text="Firma",padding=10); lf2.pack(fill="x",padx=26,pady=(0,12))
        self._var_firma=tk.StringVar(value=config.FIRMA)
        ttk.Entry(lf2,textvariable=self._var_firma,font=FT_BODY,width=52).pack(fill="x")
        def _ap():
            config.FIRMA=self._var_firma.get().strip()
            self.set_status("✔ Config aplicada para esta sesión.")
            messagebox.showinfo("Config","Aplicada.\nPara permanente: edita config.py.")
        def _recargar_cfg():
            self.navegar("pacientes")
            self.recargar_pacientes()
            self.set_status("↺ Recargando pacientes desde nueva ruta…")
        bf=tk.Frame(f,bg=C_BG); bf.pack(fill="x",padx=26,pady=(0,10))
        ttk.Button(bf,text="✔  Aplicar",style="Green.TButton",command=_ap).pack(side="right",ipadx=8,ipady=4)
        ttk.Button(bf,text="↺  Recargar pacientes ahora",style="Outline.TButton",
                   command=_recargar_cfg).pack(side="left",ipadx=8,ipady=4)
        lf3=ttk.LabelFrame(f,text="Atajos de teclado",padding=10); lf3.pack(fill="x",padx=26)
        tk.Label(lf3,text=(
            "Ctrl+1/2/3/4/5  →  Navegar entre paneles\n"
            "Ctrl+R          →  Recargar pacientes\n"
            "Ctrl+N          →  Nueva dieta individual\n"
            "Ctrl+S          →  Generar (panel activo)\n"
            "Ctrl+K          →  Autocompletar tabla\n"
            "Ctrl+L          →  Limpiar tabla\n"
            "Ctrl+T          →  Cambiar a pestaña Tabla\n"
            "Ctrl+M          →  Acciones masivas\n"
            "Ctrl+E          →  Exportar catálogo CSV\n"
            "Ctrl+A          →  Seleccionar todo el texto\n"
            "F5              →  Refrescar panel\n"
            "Ctrl+?          →  Ayuda detallada\n"
            "Ctrl+Q          →  Salir"),
            bg=C_BG,fg=C_TEXT,font=FT_MONO,justify="left").pack(anchor="w")
        return f

    # ── CARGA INICIAL (en hilo para no bloquear arranque) ─────────────────── #
    def _carga_inicial(self):
        self.set_status("⏳ Cargando pacientes al inicio…")
        self._lbl_cargando.config(text="⏳ Cargando…")
        threading.Thread(target=self._recargar_bg, daemon=True).start()
    def run(self): self.root.mainloop()


# ══ helper: construir PlanSemanal desde celdas del editor ══════════════════ #
# El armado real vive en planes.plan_desde_celdas_manual (un solo lugar,
# con tests). Se conserva este alias para no tocar los sitios de llamada.
def _plan_desde_celdas(paciente, celdas_manual, numero_plan, notas):
    return planes.plan_desde_celdas_manual(paciente, celdas_manual,
                                           numero_plan, notas=notas)


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
    )
    app = NutriApp(); app.run()
