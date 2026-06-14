# -*- coding: utf-8 -*-
"""
gui.pyw  —  NutriDietas (Interfaz Gráfica)
==========================================
Ventana principal. NutriApp se compone de un mixin por panel, definidos en
los módulos gui_*.py (pacientes, individual, grupo, tabla, catálogo, config).
La paleta de colores y la tipografía viven en gui_tema.py.

Ejecuta:  python gui.pyw
"""

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
from nutridietas.gui.paneles.pacientes import PanelPacientesMixin
from nutridietas.gui.paneles.individual import PanelIndividualMixin
from nutridietas.gui.paneles.grupo import PanelGrupoMixin
from nutridietas.gui.paneles.tabla import TablaMixin
from nutridietas.gui.paneles.catalogo import PanelCatalogoMixin
from nutridietas.gui.paneles.config import PanelConfigMixin


class NutriApp(PanelPacientesMixin, PanelIndividualMixin, PanelGrupoMixin,
               TablaMixin, PanelCatalogoMixin, PanelConfigMixin):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NutriDietas — Lic. Juan Pablo Espino")
        self.root.geometry("1280x780"); self.root.minsize(960, 620)
        self.root.configure(bg=C_BG)
        self._aplicar_icono()

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
                from nutridietas.gui import atajos; atajos.registrar(self)
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

    # ── ICONO ─────────────────────────────────────────────────────────────── #
    def _aplicar_icono(self):
        """Pone el icono de la app en la ventana (barra de título / taskbar).

        Usa el .ico en Windows; si falla, intenta el PNG como respaldo. Nunca
        es fatal: si no hay icono, la app sigue funcionando igual.
        """
        import logging
        log = logging.getLogger(__name__)
        try:
            if os.path.exists(config.RUTA_ICONO):
                self.root.iconbitmap(config.RUTA_ICONO)
                return
        except Exception:
            log.warning("No se pudo aplicar el .ico: %s",
                        config.RUTA_ICONO, exc_info=True)
        # Respaldo: PNG vía iconphoto (multiplataforma)
        png = os.path.join(config.CARPETA_RECURSOS, "icono_1024.png")
        try:
            if os.path.exists(png):
                self._icono_img = tk.PhotoImage(file=png)
                self.root.iconphoto(True, self._icono_img)
        except Exception:
            log.warning("No se pudo aplicar el icono PNG: %s", png, exc_info=True)

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

    def _carga_inicial(self):
        self.set_status("⏳ Cargando pacientes al inicio…")
        self._lbl_cargando.config(text="⏳ Cargando…")
        threading.Thread(target=self._recargar_bg, daemon=True).start()
    def run(self): self.root.mainloop()


def main():
    """Configura el logging y arranca la interfaz grafica."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s: %(message)s",
    )
    app = NutriApp(); app.run()


if __name__ == "__main__":
    main()
