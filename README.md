# NutriDietas

Aplicación en **Python** para generar dietas en **Word** con el formato del
Lic. Juan Pablo Espino. Permite:

- Crear dietas **individuales** evitando automáticamente los alimentos que no le
  agradan al paciente.
- Crear dietas **en grupo**: varios pacientes comen **lo mismo**, cambiando
  **solo las porciones** según el factor de cada uno.
- Leer la información de los pacientes desde sus carpetas y fichas de Word.
- Mantener un **catálogo de platillos** ampliable.

El Word generado replica el formato original: página carta horizontal, logo
arriba a la derecha, título en verde, tabla con cabeceras y columna de días en
verde (#1AA27E), nombres de platillos en verde oscuro y firma al pie.

---

## 1. Requisitos

- Python 3.9 o superior.
- Las librerías `python-docx` (Word) y `reportlab` (PDF):

```bash
pip install -r requirements.txt
```

## 2. Estructura del proyecto (paquete)

El código vive en el paquete `nutridietas/`, organizado por capas. Los datos,
recursos y los lanzadores quedan en la raíz.

```
NutriDietas/
├── gui.pyw                  Lanzador de la interfaz gráfica (entrada recomendada)
├── main.py                  Lanzador del menú de consola (entrada alternativa)
├── pyproject.toml           Metadatos del proyecto y configuración de pytest
├── requirements.txt         Dependencias de ejecución (python-docx, reportlab)
├── requirements-dev.txt     Dependencias de desarrollo (pytest)
│
├── nutridietas/             Paquete principal
│   ├── config.py            Configuración: rutas, colores, fuentes, medidas
│   ├── nucleo/              Lógica de dominio (sin dependencias de UI)
│   │   ├── modelos.py        Clases de datos: Paciente, Platillo, PlanSemanal…
│   │   ├── utilidades.py     Fracciones, normalización, escalado de porciones
│   │   ├── catalogo.py       Catálogo de platillos (carga/consulta/guardado)
│   │   ├── pacientes.py      Lectura de carpetas y fichas de pacientes (.docx)
│   │   ├── planes.py         Construcción del plan desde el editor visual
│   │   ├── dieta_individual.py  Lógica de dieta individual
│   │   └── dieta_grupal.py      Lógica de dieta en grupo
│   ├── salida/             Generación de archivos
│   │   ├── generadores.py    Fachada: elige el formato (Word/PDF)
│   │   ├── generador_docx.py Creación del Word con el formato exacto
│   │   └── generador_pdf.py  Creación del PDF (reportlab)
│   ├── gui/               Interfaz gráfica (Tkinter)
│   │   ├── app.py            Ventana principal (NutriApp = composición de paneles)
│   │   ├── tema.py           Paleta de colores y tipografía
│   │   ├── tabla_dieta.py    Widget: editor visual de la tabla 6×8
│   │   ├── atajos.py         Atajos de teclado y acciones masivas
│   │   └── paneles/         Un módulo (mixin) por panel
│   │       ├── pacientes.py  individual.py  grupo.py
│   │       └── tabla.py      catalogo.py    config.py
│   ├── cli/
│   │   └── menu.py           Menú de consola
│   └── herramientas/
│       └── extractor_planes_alimenticios.py  Convierte .docx de planes a JSON
│
├── datos/
│   └── catalogo_platos.json   Catálogo de platillos (editable)
├── plantillas/
│   └── ejemplo_plantilla.json  Plantilla de menú reutilizable
├── recursos/
│   └── logo.png             Logo del nutriólogo (se inserta en cada dieta)
├── tests/                   Pruebas (pytest)
├── salidas/                 Dietas generadas (si el paciente no tiene carpeta)
└── Pacientes/               Carpetas de pacientes (NO se versiona; ver nota final)
```

## 3. Cómo se organizan los pacientes

Igual que en tu sistema actual: una carpeta por paciente, dentro:

```
Pacientes/
└── 19 Rafael Cortes Zapot/
    ├── Rafael Cortes Zapot.docx              <- FICHA (información del paciente)
    ├── 1er Plan alimenticio Rafael.docx      <- dieta semana 1
    ├── 2do Plan alimenticio Rafael.docx      <- dieta semana 2
    └── ...
```

Regla que usa el programa:
- El archivo **sin** la frase "plan alimenticio" es la **ficha**.
- Los archivos **con** "plan alimenticio" son **dietas**.

De la ficha se leen automáticamente los **"Alimentos que no le agradan / no
acostumbra"** para excluirlos de las dietas.

## 4. Apuntar a tus pacientes reales

Edita `nutridietas/config.py` y cambia:

```python
CARPETA_PACIENTES = r"C:\Users\TuUsuario\OneDrive\Pacientes"
```

O cámbialo temporalmente desde la **opción 5 (Configuración)** del menú.

## 5. Ejecutar

**Interfaz gráfica (recomendada):**

```bash
python gui.pyw
```

**Menú de consola (alternativa):**

```bash
python main.py
```

Ambas comparten la misma lógica y el mismo catálogo; solo cambia la forma
de interactuar. El resto de esta sección describe el flujo del menú de consola.

Menú principal:

```
1. Ver pacientes
2. Generar dieta INDIVIDUAL  (evita lo que no le gusta)
3. Generar dieta EN GRUPO    (mismo menú, porciones distintas)
4. Catálogo de platillos
5. Configuración
0. Salir
```

### Dieta individual (opción 2)
1. Elige al paciente.
2. Puedes agregar más alimentos a evitar.
3. El programa te muestra qué platillos se excluyen y por qué.
4. Eliges número de semana, factor de porción, si incluyes Colación 2 y comida
   libre el domingo, y notas superiores.
5. El Word se guarda **dentro de la carpeta del paciente**.

### Dieta en grupo (opción 3)
1. Selecciona varios pacientes (ej. `1,3,4`).
2. El programa muestra una **comparación de gustos**: qué pueden comer todos y
   qué platillos chocan y con quién.
3. Indicas el **factor de porción** de cada paciente.
4. Se genera un Word por paciente, **con el mismo menú** pero con **porciones
   ajustadas** a cada uno.

### Catálogo (opción 4)
Puedes ver y **agregar platillos** nuevos con sus ingredientes y porciones.
Cada ingrediente tiene cantidad y unidad para que las porciones se puedan
escalar (ej. 180 gramos × 1.3 = 235 gramos).

## 6. Cómo escala las porciones

- Gramos / ml: se redondean al múltiplo de 5 más cercano.
- Piezas, tazas, cucharadas: se redondean a 1/4 y se muestran como fracciones
  (1/2, 3/4, 1 1/4, etc.).
- Ingredientes "al gusto" o de texto libre (ej. "1/2 lata o 3/4 lata") no se
  escalan.

## 7. Personalización rápida

Todo lo visual y las rutas están en `nutridietas/config.py`:
- Colores (`COLOR_VERDE_ENCABEZADO`, `COLOR_VERDE_TITULO`, ...).
- Fuente (`FUENTE_PRINCIPAL = "Century Gothic"`).
- Anchos de columna, márgenes, tamaños de letra.
- Firma del nutriólogo (`FIRMA`).
- Icono de la app (`RUTA_ICONO` → `recursos/icono.ico`).

## 8. Compilar a ejecutable (.exe)

El icono de la marca está en `recursos/` (`icono.svg` fuente, `icono_1024.png`
y `icono.ico` multitamaño). Para generar el ejecutable con su icono:

```bash
pip install -r requirements-dev.txt   # incluye pyinstaller
pyinstaller NutriDietas.spec
```

El resultado queda en `dist/NutriDietas/NutriDietas.exe`. Las carpetas
`datos/`, `recursos/` y `plantillas/` se copian junto al `.exe` para que el
catálogo, el logo y las plantillas sigan siendo editables. `config.py` detecta
si la app está compilada y busca esos datos al lado del ejecutable.

> Para regenerar el `.ico` desde un PNG nuevo:
> ```python
> from PIL import Image
> Image.open("recursos/icono_1024.png").convert("RGBA").save(
>     "recursos/icono.ico",
>     sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
> ```

---

**Nota sobre los datos de pacientes (privacidad):**
La carpeta `Pacientes/` contiene información personal y de salud, por lo que
**no se versiona** (está en `.gitignore`). Mantenla solo en tu equipo o apunta
`CARPETA_PACIENTES` en `config.py` a tu carpeta real (por ejemplo, en OneDrive).
Si necesitas una carpeta de prueba, crea una con datos ficticios.
