# -*- coding: utf-8 -*-
"""
main.py  —  NutriDietas
=======================
Aplicacion de consola para generar dietas en Word con el formato del
Lic. Juan Pablo Espino.

Modulos del proyecto:
    config.py          configuracion (rutas, colores, fuentes, medidas)
    utilidades.py      fracciones, normalizacion de texto, escalado de porciones
    modelos.py         clases de datos (Paciente, Platillo, PlanSemanal, ...)
    catalogo.py        base de datos de platillos (JSON)
    pacientes.py       lectura de carpetas y fichas de pacientes
    generador_docx.py  creacion del Word con el formato exacto
    dieta_individual.py logica de dieta individual (evita lo no deseado)
    dieta_grupal.py    logica de dieta en grupo (mismo menú, distintas porciones)
    main.py            este menu principal

Ejecuta:  python main.py
"""

import os
import sys

import config
import pacientes as gp
from catalogo import Catalogo
from modelos import Platillo, Ingrediente
import dieta_individual as di
import dieta_grupal as dgrupo
import generador_docx as gen


# --------------------------------------------------------------------------- #
#  Utilidades de consola
# --------------------------------------------------------------------------- #
def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def titulo(texto):
    print("=" * 64)
    print(f"  {texto}")
    print("=" * 64)


def pausa():
    input("\nPresiona ENTER para continuar...")


def pedir_int(mensaje, minimo=None, maximo=None, permitir_vacio=False):
    while True:
        v = input(mensaje).strip()
        if permitir_vacio and v == "":
            return None
        try:
            n = int(v)
        except ValueError:
            print("  → Escribe un número válido.")
            continue
        if minimo is not None and n < minimo:
            print(f"  → Debe ser >= {minimo}.")
            continue
        if maximo is not None and n > maximo:
            print(f"  → Debe ser <= {maximo}.")
            continue
        return n


def pedir_float(mensaje, defecto=1.0):
    v = input(mensaje).strip().replace(",", ".")
    if v == "":
        return defecto
    try:
        return float(v)
    except ValueError:
        print("  → Valor inválido, se usa", defecto)
        return defecto


# --------------------------------------------------------------------------- #
#  Cargar pacientes (con aviso si no hay carpeta)
# --------------------------------------------------------------------------- #
def obtener_pacientes():
    lista = gp.listar_pacientes()
    if not lista:
        print(f"\n  No se encontraron pacientes en:\n    {config.CARPETA_PACIENTES}")
        print("  Revisa la ruta en config.py (CARPETA_PACIENTES) o usa la")
        print("  opción 5 del menú para cambiarla.\n")
    return lista


def elegir_paciente(lista):
    for i, p in enumerate(lista, start=1):
        evita = f"  (evita: {', '.join(p.no_deseados)})" if p.no_deseados else ""
        print(f"  {i:>2}. {p.nombre}{evita}")
    n = pedir_int("\nNúmero de paciente (0 = cancelar): ", minimo=0, maximo=len(lista))
    if n == 0:
        return None
    return lista[n - 1]


def editar_no_deseados(paciente):
    print(f"\nAlimentos que evita actualmente {paciente.nombre}:")
    print("  " + (", ".join(paciente.no_deseados) if paciente.no_deseados else "(ninguno)"))
    extra = input("Agregar más (separados por coma) o ENTER para dejar igual: ").strip()
    if extra:
        for x in extra.split(","):
            x = x.strip()
            if x:
                paciente.no_deseados.append(x)


# --------------------------------------------------------------------------- #
#  OPCION 1: Listar pacientes
# --------------------------------------------------------------------------- #
def menu_listar():
    limpiar()
    titulo("PACIENTES REGISTRADOS")
    lista = obtener_pacientes()
    if not lista:
        pausa(); return
    for i, p in enumerate(lista, start=1):
        print(f"\n  {i:>2}. {p.nombre}   (planes existentes: {p.num_planes})")
        if p.no_deseados:
            print(f"      Evita: {', '.join(p.no_deseados)}")
        if p.preferidos:
            print(f"      Prefiere: {', '.join(p.preferidos)}")
    pausa()


# --------------------------------------------------------------------------- #
#  OPCION 2: Dieta individual
# --------------------------------------------------------------------------- #
def menu_individual(catalogo):
    limpiar()
    titulo("GENERAR DIETA INDIVIDUAL")
    lista = obtener_pacientes()
    if not lista:
        pausa(); return
    paciente = elegir_paciente(lista)
    if not paciente:
        return

    editar_no_deseados(paciente)

    # mostrar platillos excluidos
    excluidos = di.reporte_excluidos(paciente, catalogo)
    if excluidos:
        print("\nPlatillos que se EXCLUIRÁN por lo que no le gusta:")
        for p, palabra in excluidos:
            print(f"  - {p.nombre}  (contiene: {palabra})")

    print()
    num = pedir_int(f"Número de plan/semana [{paciente.num_planes + 1}]: ",
                    minimo=1, permitir_vacio=True) or (paciente.num_planes + 1)
    fac = pedir_float("Factor de porción (1.0 = base, 1.2 = +20%): [1.0] ", 1.0)
    paciente.factor_porcion = fac
    col2 = input("¿Incluir Colación 2? (s/N): ").strip().lower() == "s"
    libre = input("¿Comida libre el domingo? (s/N): ").strip().lower() == "s"

    notas = []
    print("Notas para la parte superior (ENTER vacío para terminar):")
    while True:
        n = input("  nota> ").strip()
        if not n:
            break
        notas.append(n)

    plan = di.construir(paciente, catalogo, numero_plan=num,
                        incluir_colacion2=col2, comida_libre_domingo=libre,
                        notas=notas)

    # guardar dentro de la carpeta del paciente si existe; si no, en salidas
    destino = None
    if paciente.carpeta and os.path.isdir(paciente.carpeta):
        destino = os.path.join(paciente.carpeta, plan.nombre_archivo())
    ruta = gen.generar(plan, ruta_salida=destino)
    print(f"\n  ✔ Dieta generada:\n    {ruta}")
    pausa()


# --------------------------------------------------------------------------- #
#  OPCION 3: Dieta en grupo
# --------------------------------------------------------------------------- #
def menu_grupo(catalogo):
    limpiar()
    titulo("GENERAR DIETA EN GRUPO")
    lista = obtener_pacientes()
    if not lista:
        pausa(); return

    print("Selecciona los pacientes del grupo.")
    for i, p in enumerate(lista, start=1):
        print(f"  {i:>2}. {p.nombre}")
    crudo = input("\nNúmeros separados por coma (ej. 1,3,4): ").strip()
    indices = []
    for x in crudo.split(","):
        x = x.strip()
        if x.isdigit():
            k = int(x)
            if 1 <= k <= len(lista):
                indices.append(k - 1)
    if len(indices) < 2:
        print("  → Necesitas al menos 2 pacientes para un grupo.")
        pausa(); return

    grupo = [lista[i] for i in indices]

    # ---- comparacion de gustos ----
    reporte = dgrupo.comparar_gustos(grupo, catalogo)
    limpiar()
    titulo("COMPARACIÓN DE GUSTOS DEL GRUPO")
    print("Integrantes:", ", ".join(p.nombre for p in grupo))
    union = reporte["no_deseados_union"]
    print("\nAlimentos no deseados (unión del grupo):")
    print("  " + (", ".join(sorted(union)) if union else "(ninguno)"))

    print("\nPlatillos que TODOS pueden comer:")
    for col in config.COLUMNAS:
        t = col["tiempo"]
        nombres = [p.nombre for p in reporte["comunes"][t]]
        # evitar repetir el mismo tiempo dos veces (colacion)
    vistos = set()
    for col in config.COLUMNAS:
        t = col["tiempo"]
        if t in vistos:
            continue
        vistos.add(t)
        nombres = [p.nombre for p in reporte["comunes"][t]]
        print(f"  [{t}] " + (", ".join(nombres) if nombres else "(ninguno apto)"))

    if reporte["conflictos"]:
        print("\nPlatillos con conflicto (no se usarán):")
        for p, choca in reporte["conflictos"]:
            quienes = "; ".join(f"{n} → {pal}" for n, pal in choca)
            print(f"  - {p.nombre}: {quienes}")

    if input("\n¿Continuar y generar las dietas? (S/n): ").strip().lower() == "n":
        return

    # ---- factores de porcion por paciente ----
    print("\nFactor de porción de cada paciente (ENTER = 1.0):")
    for p in grupo:
        p.factor_porcion = pedir_float(f"  {p.nombre}: ", 1.0)

    num = pedir_int("Número de plan/semana [1]: ", minimo=1,
                    permitir_vacio=True) or 1
    col2 = input("¿Incluir Colación 2? (s/N): ").strip().lower() == "s"

    planes = dgrupo.construir_grupo(grupo, catalogo, numero_plan=num,
                                    incluir_colacion2=col2)

    print()
    for pac, plan in planes:
        destino = None
        if pac.carpeta and os.path.isdir(pac.carpeta):
            destino = os.path.join(pac.carpeta, plan.nombre_archivo())
        ruta = gen.generar(plan, ruta_salida=destino)
        print(f"  ✔ {pac.nombre} (porción x{pac.factor_porcion}):\n      {ruta}")
    pausa()


# --------------------------------------------------------------------------- #
#  OPCION 4: Catalogo de platillos
# --------------------------------------------------------------------------- #
def menu_catalogo(catalogo):
    while True:
        limpiar()
        titulo("CATÁLOGO DE PLATILLOS")
        for col in config.COLUMNAS:
            pass
        # mostrar por tiempo
        vistos = set()
        for col in config.COLUMNAS:
            t = col["tiempo"]
            if t in vistos:
                continue
            vistos.add(t)
            print(f"\n  >>> {t.upper()}")
            for p in catalogo.por_tiempo(t):
                marca = " (Video)" if p.video else ""
                print(f"     - {p.nombre}{marca}  [{len(p.ingredientes)} ingredientes]")
        print("\n  ------------------------------------------------")
        print("  1. Agregar platillo")
        print("  2. Ver ingredientes de un platillo")
        print("  0. Volver")
        op = input("\n  Opción: ").strip()
        if op == "1":
            agregar_platillo(catalogo)
        elif op == "2":
            ver_ingredientes(catalogo)
        elif op == "0":
            return


def agregar_platillo(catalogo):
    limpiar()
    titulo("AGREGAR PLATILLO")
    nombre = input("Nombre del platillo: ").strip()
    if not nombre:
        return
    print("Tiempo: 1) desayuno  2) colacion  3) comida  4) cena")
    mapa = {"1": "desayuno", "2": "colacion", "3": "comida", "4": "cena"}
    tiempo = mapa.get(input("Elige: ").strip(), "comida")
    video = input("¿Tiene video? (s/N): ").strip().lower() == "s"
    nota = input("Nota al pie (opcional): ").strip() or None

    ingredientes = []
    print("\nIngredientes (deja el nombre vacío para terminar).")
    print("Para cantidad libre/al gusto deja la cantidad vacía.")
    while True:
        n = input("  ingrediente> ").strip()
        if not n:
            break
        c = input("    cantidad (ej. 1, 0.5, 180): ").strip().replace(",", ".")
        u = input("    unidad (ej. pieza, taza, gramos): ").strip()
        cant = None
        if c:
            try:
                cant = float(c)
            except ValueError:
                cant = None
        ingredientes.append(Ingrediente(nombre=n, cantidad=cant, unidad=u))

    pid = nombre.lower().replace(" ", "_")[:30]
    catalogo.agregar_platillo(
        Platillo(id=pid, nombre=nombre, tiempo=tiempo,
                 ingredientes=ingredientes, video=video, nota=nota)
    )
    catalogo.guardar()
    print("\n  ✔ Platillo agregado y guardado en el catálogo.")
    pausa()


def ver_ingredientes(catalogo):
    nombre = input("\nNombre (o parte) del platillo: ").strip()
    encontrados = catalogo.buscar(nombre)
    if not encontrados:
        print("  → No se encontró.")
        pausa(); return
    for p in encontrados:
        print(f"\n  {p.nombre}  [{p.tiempo}]")
        for ing in p.ingredientes:
            print("    • " + ing.render())
        if p.nota:
            print("    (nota:", p.nota + ")")
    pausa()


# --------------------------------------------------------------------------- #
#  OPCION 5: Configuracion
# --------------------------------------------------------------------------- #
def menu_config():
    limpiar()
    titulo("CONFIGURACIÓN")
    print(f"  Carpeta de pacientes actual:\n    {config.CARPETA_PACIENTES}")
    print(f"\n  Carpeta de salidas:\n    {config.CARPETA_SALIDAS}")
    print(f"\n  Logo:\n    {config.RUTA_LOGO}  "
          f"({'existe' if os.path.exists(config.RUTA_LOGO) else 'NO existe'})")
    nueva = input("\nNueva ruta de carpeta de pacientes (ENTER = dejar igual): ").strip()
    if nueva:
        if os.path.isdir(nueva):
            config.CARPETA_PACIENTES = nueva
            print("  ✔ Ruta actualizada para esta sesión.")
            print("  (Para que sea permanente, edítala en config.py)")
        else:
            print("  → Esa carpeta no existe.")
    pausa()


# --------------------------------------------------------------------------- #
#  MENU PRINCIPAL
# --------------------------------------------------------------------------- #
def main():
    catalogo = Catalogo()
    while True:
        limpiar()
        titulo("NutriDietas  —  Lic. Juan Pablo Espino")
        print("""
  1. Ver pacientes
  2. Generar dieta INDIVIDUAL  (evita lo que no le gusta)
  3. Generar dieta EN GRUPO    (mismo menú, porciones distintas)
  4. Catálogo de platillos
  5. Configuración
  0. Salir
""")
        op = input("  Elige una opción: ").strip()
        if op == "1":
            menu_listar()
        elif op == "2":
            menu_individual(catalogo)
        elif op == "3":
            menu_grupo(catalogo)
        elif op == "4":
            menu_catalogo(catalogo)
        elif op == "5":
            menu_config()
        elif op == "0":
            print("\n  ¡Hasta pronto!\n")
            sys.exit(0)
        else:
            print("  → Opción no válida.")
            pausa()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Interrumpido. ¡Hasta pronto!\n")
