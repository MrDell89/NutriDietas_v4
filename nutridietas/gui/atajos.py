# -*- coding: utf-8 -*-
"""
atajos.py  —  NutriDietas
==========================
Módulo SEPARADO que define:

  1. Atajos de teclado   → clase Atajos
  2. Acciones masivas    → clase AccionesMasivas
  3. Función de entrada  → registrar(app)

Se importa desde gui.py con:
    import atajos
    atajos.registrar(self)          # self = instancia de NutriApp

NO importa gui.py. Recibe la instancia de la app como parámetro para
evitar importaciones circulares.
"""

import os
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from nutridietas import config
from nutridietas.nucleo import pacientes as gp
from nutridietas.nucleo.catalogo import Catalogo
from nutridietas.nucleo import dieta_individual as di
from nutridietas.salida import generador_docx as gen


# ═══════════════════════════════════════════════════════════════════════════ #
#  ATAJOS DE TECLADO                                                          #
# ═══════════════════════════════════════════════════════════════════════════ #
class Atajos:
    """
    Registra todos los atajos de teclado sobre la ventana raíz.

    Mapa de atajos:
        Ctrl+1   →  Ir a panel Pacientes
        Ctrl+2   →  Ir a panel Dieta Individual
        Ctrl+3   →  Ir a panel Dieta en Grupo
        Ctrl+4   →  Ir a panel Catálogo
        Ctrl+5   →  Ir a Configuración
        Ctrl+R   →  Recargar pacientes
        Ctrl+N   →  Nueva dieta individual (resetea el formulario)
        Ctrl+G   →  Ir a panel Grupo
        Ctrl+K   →  Autocompletar tabla activa
        Ctrl+L   →  Limpiar tabla activa
        Ctrl+T   →  Cambiar a pestaña Tabla
        Ctrl+M   →  Abrir ventana de Acciones Masivas
        Ctrl+E   →  Exportar catálogo a CSV
        Ctrl+P   →  Abrir carpeta del paciente seleccionado
        Ctrl+S   →  Generar dieta (según panel activo)
        Ctrl+B   →  Ir a Catálogo (buscar platillos)
        Ctrl+A   →  Seleccionar todo el texto (comportamiento nativo)
        F5       →  Refrescar panel actual
        Ctrl+?   →  Mostrar ventana de ayuda detallada
        Ctrl+Q   →  Salir
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self._masivas = AccionesMasivas(app)
        self._registrar()

    def _registrar(self):
        r = self.root
        bind = r.bind

        # ── navegación ──────────────────────────────────────────────────── #
        bind("<Control-Key-1>", lambda e: self.app.navegar("pacientes"))
        bind("<Control-Key-2>", lambda e: self.app.navegar("individual"))
        bind("<Control-Key-3>", lambda e: self.app.navegar("grupo"))
        bind("<Control-Key-4>", lambda e: self.app.navegar("catalogo"))
        bind("<Control-Key-5>", lambda e: self.app.navegar("config"))

        # ── acciones comunes ─────────────────────────────────────────────── #
        bind("<Control-r>",  lambda e: self._recargar())
        bind("<Control-R>",  lambda e: self._recargar())
        bind("<Control-n>",  lambda e: self._nueva_individual())
        bind("<Control-N>",  lambda e: self._nueva_individual())
        bind("<Control-g>",  lambda e: self._ir_grupo())
        bind("<Control-G>",  lambda e: self._ir_grupo())
        bind("<Control-s>",  lambda e: self._generar_activo())
        bind("<Control-S>",  lambda e: self._generar_activo())
        bind("<Control-p>",  lambda e: self._abrir_carpeta())
        bind("<Control-P>",  lambda e: self._abrir_carpeta())
        bind("<Control-b>",  lambda e: self.app.navegar("catalogo"))
        bind("<Control-B>",  lambda e: self.app.navegar("catalogo"))

        # ── tabla: limpiar / autocompletar / cambiar pestaña ────────────── #
        bind("<Control-l>",  lambda e: self._limpiar_tabla())
        bind("<Control-L>",  lambda e: self._limpiar_tabla())
        bind("<Control-k>",  lambda e: self._autocompletar_tabla())
        bind("<Control-K>",  lambda e: self._autocompletar_tabla())
        bind("<Control-t>",  lambda e: self._ir_a_tabla())
        bind("<Control-T>",  lambda e: self._ir_a_tabla())

        # ── acciones masivas y exportación ──────────────────────────────── #
        bind("<Control-m>",  lambda e: self._masivas.abrir_ventana())
        bind("<Control-M>",  lambda e: self._masivas.abrir_ventana())
        bind("<Control-e>",  lambda e: self._masivas.exportar_catalogo())
        bind("<Control-E>",  lambda e: self._masivas.exportar_catalogo())

        # ── Ctrl+A: seleccionar todo solo si hay widget de texto enfocado── #
        bind("<Control-a>",  lambda e: self._select_all(e))
        bind("<Control-A>",  lambda e: self._select_all(e))

        # ── utilidades ──────────────────────────────────────────────────── #
        bind("<F5>",         lambda e: self._refrescar_panel())
        bind("<Control-slash>",    lambda e: self._ayuda())
        bind("<Control-question>", lambda e: self._ayuda())
        bind("<Control-q>",  lambda e: r.destroy())
        bind("<Control-Q>",  lambda e: r.destroy())

    # ────────────────────────── CALLBACKS ────────────────────────────────── #
    def _recargar(self):
        self.app.recargar_pacientes()
        self.app.set_status("↺ Pacientes recargados (Ctrl+R)")

    def _nueva_individual(self):
        self.app.navegar("individual")
        # limpiar notas y seleccionar primer paciente
        try:
            self.app._txt_notas.delete("1.0", "end")
            self.app._spin_factor.set("1.0")
            self.app._var_col2.set(False)
            self.app._var_libre.set(False)
            self.app.set_status("Nueva dieta individual (Ctrl+N)")
        except Exception:
            pass

    def _ir_grupo(self):
        self.app.navegar("grupo")
        self.app.set_status("Panel grupo (Ctrl+G) — selecciona pacientes y compara")

    def _generar_activo(self):
        panel = self.app._panel_activo
        if panel == "individual":
            self.app.generar_individual()
        elif panel == "grupo":
            self.app.generar_grupo()
        else:
            self.app.set_status("Ctrl+S genera según el panel activo (Individual o Grupo)")

    def _abrir_carpeta(self):
        try:
            self.app._abrir_carpeta_paciente()
        except Exception:
            pass

    def _limpiar_tabla(self):
        self.app.limpiar_tabla_activa()

    def _autocompletar_tabla(self):
        self.app.autocompletar_tabla_activa()

    def _ir_a_tabla(self):
        self.app.ir_a_pestana_tabla()
        self.app.set_status("Ctrl+T — pestaña Tabla")

    def _select_all(self, event):
        w = event.widget
        try:
            if isinstance(w, tk.Text):
                w.tag_add("sel", "1.0", "end")
                return "break"
            elif isinstance(w, (tk.Entry, ttk.Entry, ttk.Combobox)):
                w.select_range(0, "end")
                return "break"
        except Exception:
            pass

    def _refrescar_panel(self):
        panel = self.app._panel_activo
        if panel == "pacientes":
            self.app.recargar_pacientes()
        elif panel == "catalogo":
            self.app._cargar_catalogo_tree()
        elif panel == "individual":
            self.app._actualizar_exclusiones()
        self.app.set_status(f"F5 — panel '{panel}' actualizado")

    def _ayuda(self):
        VentanaAyuda(self.root)


# ═══════════════════════════════════════════════════════════════════════════ #
#  ACCIONES MASIVAS                                                           #
# ═══════════════════════════════════════════════════════════════════════════ #
class AccionesMasivas:
    """
    Operaciones que afectan a MÚLTIPLES pacientes o archivos a la vez.

    Acciones disponibles:
        generar_todos_individual  →  genera una dieta Word por CADA paciente
        resumen_pacientes         →  exporta resumen TXT de todos los pacientes
        exportar_catalogo         →  exporta el catálogo de platillos a CSV
        abrir_ventana             →  abre la ventana de selección de acciones
    """

    def __init__(self, app):
        self.app = app

    # ─────────────────────────── VENTANA PRINCIPAL ───────────────────────── #
    def abrir_ventana(self):
        win = tk.Toplevel(self.app.root)
        win.title("Acciones Masivas — NutriDietas")
        win.geometry("520x440")
        win.configure(bg="#F4F7F6")
        win.grab_set()
        win.resizable(False, False)

        # header
        hdr = tk.Frame(win, bg="#072F25", height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  Acciones Masivas", bg="#072F25",
                 fg="white", font=("Segoe UI", 14, "bold")).pack(
                 side="left", padx=18, pady=12)

        tk.Label(win, text="Selecciona la operación que quieres ejecutar\n"
                           "sobre todos los pacientes o el catálogo.",
                 bg="#F4F7F6", fg="#0D0D0D",
                 font=("Segoe UI", 10), justify="left").pack(
                 anchor="w", padx=20, pady=(14, 8))

        # ── opciones de generación masiva ──────────────── #
        gen_lf = tk.LabelFrame(win, text="Generación masiva de dietas",
                               bg="#F4F7F6", fg="#072F25",
                               font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        gen_lf.pack(fill="x", padx=18, pady=(0, 10))

        self._var_col2_mas = tk.BooleanVar(value=False)
        self._var_libre_mas = tk.BooleanVar(value=True)

        row1 = tk.Frame(gen_lf, bg="#F4F7F6")
        row1.pack(fill="x", pady=2)
        ttk.Checkbutton(row1, text="Incluir Colación 2",
                        variable=self._var_col2_mas).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(row1, text="Comida libre el domingo",
                        variable=self._var_libre_mas).pack(side="left")

        s = ttk.Style()
        s.configure("Masiva.TButton", background="#1AA27E", foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=(10, 6))
        s.map("Masiva.TButton", background=[("active", "#148A6A")])

        ttk.Button(gen_lf,
                   text="🍽  Generar dieta individual para TODOS los pacientes",
                   style="Masiva.TButton",
                   command=lambda: self._iniciar_generar_todos(win)).pack(
                   fill="x", pady=(8, 0))

        # ── exportación ────────────────────────────────── #
        exp_lf = tk.LabelFrame(win, text="Exportación",
                               bg="#F4F7F6", fg="#072F25",
                               font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        exp_lf.pack(fill="x", padx=18, pady=(0, 10))

        for txt, cmd in [
            ("📋  Exportar catálogo a CSV",   self.exportar_catalogo),
            ("📄  Resumen de pacientes a TXT", self.resumen_pacientes),
        ]:
            ttk.Button(exp_lf, text=txt, style="Masiva.TButton",
                       command=cmd).pack(fill="x", pady=3)

        # ── botón cerrar ────────────────────────────────── #
        tk.Frame(win, bg="#F4F7F6", height=6).pack()
        ttk.Button(win, text="Cerrar", command=win.destroy,
                   style="Masiva.TButton").pack(pady=8)

    # ─────────────────────── GENERAR TODOS ───────────────────────────────── #
    def _iniciar_generar_todos(self, parent_win):
        pac_list = self.app.pacientes
        if not pac_list:
            messagebox.showinfo("Sin pacientes",
                                "No hay pacientes cargados.", parent=parent_win)
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Generar una dieta individual para cada uno de los "
            f"{len(pac_list)} pacientes?\n\n"
            f"Los archivos se guardarán en la carpeta de cada paciente.",
            parent=parent_win):
            return

        col2  = self._var_col2_mas.get()
        libre = self._var_libre_mas.get()
        cat   = self.app.catalogo

        prog_win = _VentanaProgreso(parent_win,
                                    titulo="Generando dietas…",
                                    total=len(pac_list))
        prog_win.abrir()

        def _run():
            exitos, errores = [], []
            for i, pac in enumerate(pac_list, 1):
                prog_win.actualizar(i, f"Generando: {pac.nombre}")
                try:
                    plan = di.construir(pac, cat,
                                        numero_plan=pac.num_planes + 1,
                                        incluir_colacion2=col2,
                                        comida_libre_domingo=libre)
                    destino = None
                    if pac.carpeta and os.path.isdir(pac.carpeta):
                        destino = os.path.join(pac.carpeta, plan.nombre_archivo())
                    ruta = gen.generar(plan, ruta_salida=destino)
                    exitos.append((pac.nombre, ruta))
                except Exception as e:
                    errores.append((pac.nombre, str(e)))

            self.app.root.after(0, lambda: _terminar(exitos, errores))

        def _terminar(exitos, errores):
            prog_win.cerrar()
            resumen = (f"✔ Generadas: {len(exitos)}\n"
                       f"✖ Errores:   {len(errores)}\n\n")
            if errores:
                resumen += "Pacientes con error:\n"
                resumen += "\n".join(f"  • {n}: {e}" for n, e in errores)
            self.app.set_status(
                f"Masivo: {len(exitos)} dietas generadas, {len(errores)} errores")
            messagebox.showinfo("Generación masiva completa", resumen)

        threading.Thread(target=_run, daemon=True).start()

    # ─────────────────────── EXPORTAR CATÁLOGO CSV ───────────────────────── #
    def exportar_catalogo(self):
        ruta = filedialog.asksaveasfilename(
            title="Exportar catálogo a CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*")],
            initialfile="catalogo_platillos.csv")
        if not ruta:
            return
        cat = self.app.catalogo
        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["ID", "Nombre", "Tiempo", "Video", "Nota",
                             "Ingrediente", "Cantidad", "Unidad"])
                for p in cat.platillos:
                    if not p.ingredientes:
                        w.writerow([p.id, p.nombre, p.tiempo,
                                    "Sí" if p.video else "No",
                                    p.nota or "", "", "", ""])
                    for ing in p.ingredientes:
                        w.writerow([p.id, p.nombre, p.tiempo,
                                    "Sí" if p.video else "No",
                                    p.nota or "",
                                    ing.nombre,
                                    ing.cantidad if ing.cantidad is not None else "",
                                    ing.unidad])
            self.app.set_status(f"✔ Catálogo exportado: {ruta}")
            messagebox.showinfo("Exportado", f"Catálogo exportado a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

    # ─────────────────────── RESUMEN PACIENTES TXT ───────────────────────── #
    def resumen_pacientes(self):
        pac_list = self.app.pacientes
        if not pac_list:
            messagebox.showinfo("Sin pacientes", "No hay pacientes cargados.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar resumen de pacientes",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*")],
            initialfile="resumen_pacientes.txt")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("RESUMEN DE PACIENTES — NutriDietas\n")
                f.write("=" * 50 + "\n\n")
                for p in pac_list:
                    f.write(f"PACIENTE: {p.nombre}\n")
                    f.write(f"  Planes generados : {p.num_planes}\n")
                    nd = ", ".join(p.no_deseados) if p.no_deseados else "(ninguno)"
                    f.write(f"  Evita            : {nd}\n")
                    pref = ", ".join(p.preferidos) if p.preferidos else "(ninguno)"
                    f.write(f"  Prefiere         : {pref}\n")
                    f.write(f"  Carpeta          : {p.carpeta or 'N/A'}\n")
                    f.write("\n")
            self.app.set_status(f"✔ Resumen exportado: {ruta}")
            messagebox.showinfo("Exportado", f"Resumen guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")


# ═══════════════════════════════════════════════════════════════════════════ #
#  VENTANA DE PROGRESO                                                        #
# ═══════════════════════════════════════════════════════════════════════════ #
class _VentanaProgreso:
    """Ventana modal con barra de progreso para operaciones largas."""

    def __init__(self, parent, titulo, total):
        self._parent = parent
        self._titulo = titulo
        self._total  = total
        self._win    = None

    def abrir(self):
        self._win = tk.Toplevel(self._parent)
        self._win.title(self._titulo)
        self._win.geometry("400x140")
        self._win.resizable(False, False)
        self._win.configure(bg="#F4F7F6")
        self._win.grab_set()
        self._win.protocol("WM_DELETE_WINDOW", lambda: None)  # no cerrable manualmente

        tk.Label(self._win, text=self._titulo, bg="#F4F7F6",
                 fg="#072F25", font=("Segoe UI", 11, "bold")).pack(
                 pady=(18, 6), padx=20, anchor="w")

        self._lbl = tk.Label(self._win, text="Iniciando…",
                             bg="#F4F7F6", fg="#6B8C82",
                             font=("Segoe UI", 9))
        self._lbl.pack(anchor="w", padx=20)

        self._bar = ttk.Progressbar(self._win, length=360,
                                    maximum=self._total, mode="determinate")
        self._bar.pack(pady=12, padx=20)
        self._win.update()

    def actualizar(self, paso, mensaje=""):
        if not self._win:
            return
        self._bar["value"] = paso
        self._lbl.config(text=f"{mensaje}  ({paso}/{self._total})")
        self._win.update()

    def cerrar(self):
        if self._win:
            self._win.grab_release()
            self._win.destroy()


# ═══════════════════════════════════════════════════════════════════════════ #
#  VENTANA DE AYUDA DE ATAJOS                                                 #
# ═══════════════════════════════════════════════════════════════════════════ #
class VentanaAyuda:
    ATAJOS = [
        ("── Navegación ──", ""),
        ("Ctrl+1", "Ir a panel Pacientes"),
        ("Ctrl+2", "Ir a panel Dieta Individual"),
        ("Ctrl+3", "Ir a panel Dieta en Grupo"),
        ("Ctrl+4", "Ir a panel Catálogo"),
        ("Ctrl+5", "Ir a Configuración"),
        ("Ctrl+B", "Ir a Catálogo (buscar platillos)"),
        ("Ctrl+G", "Ir a panel de Grupo"),
        ("Ctrl+T", "Cambiar a pestaña Tabla (Individual o Grupo)"),
        ("", ""),
        ("── Dietas ──", ""),
        ("Ctrl+N", "Nueva dieta individual (limpia el formulario)"),
        ("Ctrl+K", "Autocompletar tabla desde el catálogo"),
        ("Ctrl+L", "Limpiar tabla (individual o grupo)"),
        ("Ctrl+S", "Generar dieta del panel activo (PDF/Word)"),
        ("", ""),
        ("── Pacientes ──", ""),
        ("Ctrl+R", "Recargar lista de pacientes"),
        ("Ctrl+P", "Abrir carpeta del paciente seleccionado"),
        ("", ""),
        ("── Edición ──", ""),
        ("Ctrl+A", "Seleccionar todo el texto del campo activo"),
        ("", ""),
        ("── Catálogo y exportación ──", ""),
        ("Ctrl+E", "Exportar catálogo a CSV"),
        ("Ctrl+M", "Acciones masivas (generar todos, exportar…)"),
        ("", ""),
        ("── Utilidades ──", ""),
        ("F5",     "Refrescar / actualizar el panel actual"),
        ("Ctrl+?", "Mostrar esta ventana de ayuda"),
        ("Ctrl+Q", "Salir de la aplicación"),
    ]

    FLUJO = """\
╔══════════════════════════════════════════════════════════════╗
║              GUÍA DE FLUJO DE TRABAJO — NutriDietas          ║
╚══════════════════════════════════════════════════════════════╝

┌─ FLUJO 1: Dieta individual para un paciente ─────────────────
│
│  1. Ctrl+1  →  Panel Pacientes
│     • Los pacientes se cargan desde la carpeta configurada.
│     • Cada carpeta debe contener un archivo .docx de ficha
│       con las secciones "Alimentos que no le agradan:" y
│       "Alimentos preferidos:".
│
│  2. Doble-clic en el paciente  →  va a Dieta Individual
│
│  3. Ctrl+2 / pestaña "⚙ Opciones":
│     • Ajusta el Nº de plan y Factor de porción (1.0 = base).
│     • Revisa la lista de alimentos que evita.
│     • Agrega notas superiores si es necesario.
│     • Pulsa "↺ Actualizar" para ver qué platillos se excluyen.
│
│  4. Ctrl+T  →  Cambia a pestaña "📋 Tabla de Dieta"
│     Ctrl+K  →  Autocompletar (rellena toda la semana)
│     • Edita celda a celda si necesitas ajustes manuales.
│     • Shift+Rueda → scroll horizontal; Rueda → scroll vertical.
│     • Botón "☺ Libre" en Domingo-Comida para comida libre.
│
│  5. Ctrl+S  →  Generar PDF o Word
│     • Se guarda en la carpeta del paciente automáticamente.
│     • Si el plan ya existe, se te pregunta si sobreescribir.
│
└──────────────────────────────────────────────────────────────

┌─ FLUJO 2: Dieta en grupo ────────────────────────────────────
│
│  1. Ctrl+3  →  Panel Dieta en Grupo
│
│  2. Busca pacientes con el buscador (filtra en tiempo real).
│     Marca los pacientes del grupo o usa "✔ Todos".
│
│  3. Pulsa "🔍 Comparar gustos":
│     • Muestra qué alimentos evita el grupo unido.
│     • Lista los platillos aptos para TODOS los integrantes.
│     • Aparecen los spinboxes de factor de porción.
│
│  4. Ajusta los factores de porción por paciente.
│
│  5. Ctrl+T → pestaña Tabla, luego Ctrl+K para autocompletar.
│     • El menú es el mismo; las porciones se escalan al generar.
│
│  6. Ctrl+S → genera un PDF/Word por cada paciente del grupo.
│
└──────────────────────────────────────────────────────────────

┌─ FLUJO 3: Usar plantillas preestablecidas ───────────────────
│
│  1. Guarda archivos JSON de dietas en la carpeta "plantillas/"
│     del proyecto. Formato: {"nombre":"...", "celdas":{...}}
│     (el JSON que devuelve la tabla al guardar).
│
│  2. En la pestaña Tabla, pulsa "📂 Cargar plantilla".
│     • Selecciona del listado o busca un archivo manualmente.
│     • La tabla se rellena con el plan preestablecido.
│     • Edita lo que necesites y genera con Ctrl+S.
│
└──────────────────────────────────────────────────────────────

┌─ FLUJO 4: Gestión del catálogo ──────────────────────────────
│
│  Ctrl+4  →  Panel Catálogo
│  • "＋ Agregar"          → añade un platillo manualmente.
│  • "📥 Importar JSON"    → importa desde otro catalogo_platos.json.
│  • "📂 Importar plan"    → extrae platillos de un plan semanal JSON.
│  • Ctrl+E               → exporta todo el catálogo a CSV.
│  • Ctrl+M               → acciones masivas (generar todos los
│                            pacientes de una vez, exportar resumen).
│
└──────────────────────────────────────────────────────────────

┌─ CONSEJOS RÁPIDOS ───────────────────────────────────────────
│  • Ctrl+L limpia la tabla activa sin cerrar la ventana.
│  • F5 recarga pacientes y actualiza el árbol de exclusiones.
│  • Ctrl+R fuerza la recarga aunque ya estés en otro panel.
│  • En cualquier campo de texto, Ctrl+A selecciona todo.
│  • Rueda del ratón sobre la tabla: scroll vertical.
│    Shift+Rueda: scroll horizontal.
└──────────────────────────────────────────────────────────────
"""

    def __init__(self, parent):
        win = tk.Toplevel(parent)
        win.title("Ayuda — NutriDietas")
        win.geometry("700x680")
        win.configure(bg="#F4F7F6")
        win.resizable(True, True)
        win.grab_set()

        hdr = tk.Frame(win, bg="#072F25", height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="❓  Ayuda y atajos de teclado",
                 bg="#072F25", fg="white",
                 font=("Segoe UI", 13, "bold")).pack(
                 side="left", padx=16, pady=10)

        nb = ttk.Notebook(win); nb.pack(fill="both", expand=True, padx=10, pady=8)

        # ── pestaña atajos ────────────────────────────────── #
        tab_k = tk.Frame(nb, bg="#F4F7F6"); nb.add(tab_k, text="  ⌨ Atajos  ")
        canvas_k = tk.Canvas(tab_k, bg="#F4F7F6", highlightthickness=0)
        vsb_k = ttk.Scrollbar(tab_k, orient="vertical", command=canvas_k.yview)
        canvas_k.configure(yscrollcommand=vsb_k.set)
        vsb_k.pack(side="right", fill="y"); canvas_k.pack(fill="both", expand=True)
        frm = tk.Frame(canvas_k, bg="#F4F7F6", padx=20, pady=12)
        canvas_k.create_window((0,0), window=frm, anchor="nw")
        frm.bind("<Configure>", lambda e: canvas_k.configure(
            scrollregion=canvas_k.bbox("all")))
        canvas_k.bind("<Enter>", lambda e: canvas_k.bind_all(
            "<MouseWheel>", lambda ev: canvas_k.yview_scroll(int(-1*ev.delta/120),"units")))
        canvas_k.bind("<Leave>", lambda e: canvas_k.unbind_all("<MouseWheel>"))

        for tecla, desc in self.ATAJOS:
            row = tk.Frame(frm, bg="#F4F7F6")
            row.pack(fill="x", pady=2)
            if not tecla and not desc:
                tk.Frame(row, bg="#C4DDD6", height=1).pack(fill="x", pady=3)
                continue
            if desc == "":
                tk.Label(row, text=tecla, bg="#F4F7F6", fg="#0B5C46",
                         font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6,0))
                continue
            lbl_k = tk.Label(row, text=tecla,
                             bg="#E6F5EF", fg="#072F25",
                             font=("Consolas", 9, "bold"),
                             width=14, anchor="center",
                             relief="solid", bd=1, padx=4)
            lbl_k.pack(side="left")
            tk.Label(row, text=f"  {desc}",
                     bg="#F4F7F6", fg="#0D0D0D",
                     font=("Segoe UI", 10)).pack(side="left")

        # ── pestaña flujo de trabajo ──────────────────────── #
        tab_f = tk.Frame(nb, bg="#F4F7F6"); nb.add(tab_f, text="  📋 Flujo de trabajo  ")
        from tkinter import scrolledtext as st
        txt_flujo = st.ScrolledText(tab_f, font=("Consolas", 9),
                                    bg="#072F25", fg="#A8D5C5",
                                    relief="flat", wrap="word",
                                    state="normal", padx=12, pady=8)
        txt_flujo.pack(fill="both", expand=True, padx=8, pady=8)
        txt_flujo.insert("end", self.FLUJO)
        txt_flujo.config(state="disabled")

        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=8)


# ═══════════════════════════════════════════════════════════════════════════ #
#  PUNTO DE ENTRADA — llamado desde gui.py                                   #
# ═══════════════════════════════════════════════════════════════════════════ #
def registrar(app):
    """
    Registra todos los atajos y acciones masivas sobre la instancia de la app.
    Llamado automáticamente al arrancar NutriApp.
    """
    Atajos(app)
