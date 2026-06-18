# Coloca la raíz del proyecto en sys.path para que los tests puedan importar
# los módulos del programa (config, utilidades, modelos, ...) sin instalarlo.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
