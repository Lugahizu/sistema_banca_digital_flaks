# create_db.py
import sqlite3
# Asegúrate de importar tu función de creación de tablas
from app.db.database import create_table

def run_create_table():
    # Llama a la función principal que crea las tablas
    success, message = create_table()
    if success:
        print(f"Éxito: {message}")
    else:
        print(f"Fallo: {message}")

if __name__ == '__main__':
    run_create_table()