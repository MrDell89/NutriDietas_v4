# -*- coding: utf-8 -*-
"""Panel de configuración de la GUI."""

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


class PanelConfigMixin:
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
