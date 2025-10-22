import sys
import os

# Agrega la carpeta padre (la raíz del proyecto) al Python path.
# Esto asegura que "app" sea un módulo accesible.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))