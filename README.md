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
- La librería `python-docx`:

```bash
pip install -r requirements.txt
```

## 2. Estructura del proyecto (modular)

```
DietasApp/
├── main.py              Menú principal (punto de entrada)
├── config.py           Configuración: rutas, colores, fuentes, medidas
├── utilidades.py       Fracciones, normalización de texto, escalado de porciones
├── modelos.py          Clases de datos: Paciente, Platillo, PlanSemanal, ...
├── catalogo.py         Base de datos de platillos (carga/consulta/guardado)
├── pacientes.py        Lectura de carpetas y fichas de pacientes (.docx)
├── generador_docx.py   Creación del Word con el formato exacto
├── dieta_individual.py Lógica de dieta individual (evita lo no deseado)
├── dieta_grupal.py     Lógica de dieta en grupo (mismo menú, distintas porciones)
├── datos/
│   └── catalogo_platos.json   Catálogo de platillos (editable)
├── recursos/
│   └── logo.png        Logo del nutriólogo (se inserta en cada dieta)
├── salidas/            Dietas generadas (si el paciente no tiene carpeta)
└── Pacientes/          Carpetas de pacientes (DEMO incluida)
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

Edita `config.py` y cambia:

```python
CARPETA_PACIENTES = r"C:\Users\TuUsuario\OneDrive\Pacientes"
```

O cámbialo temporalmente desde la **opción 5 (Configuración)** del menú.

## 5. Ejecutar

```bash
cd DietasApp
python main.py
```

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

Todo lo visual y las rutas están en `config.py`:
- Colores (`COLOR_VERDE_ENCABEZADO`, `COLOR_VERDE_TITULO`, ...).
- Fuente (`FUENTE_PRINCIPAL = "Century Gothic"`).
- Anchos de columna, márgenes, tamaños de letra.
- Firma del nutriólogo (`FIRMA`).

---

**Nota:** la carpeta `Pacientes/` incluida es solo una **demostración** para que
puedas probar el programa de inmediato. Apunta `CARPETA_PACIENTES` a tu carpeta
real cuando empieces a usarlo.
