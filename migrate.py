# migrate.py
import sqlite3

def connect():
    # Usa la misma función que tu aplicación para asegurar la conexión
    return sqlite3.connect('mi_banco.db') 

def migrate_db():
    conn = None
    try:
        conn = connect()
        cur = conn.cursor()

        print("Intentando agregar la columna 'role' a la tabla 'user'...")
        cur.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'cliente'")
        conn.commit()
        print("Columna 'role' agregada con éxito.")
        return True, "Migración exitosa."
    except sqlite3.OperationalError as e:
        # Captura el error si la columna ya existe
        print(f"La columna 'role' ya existe. No se necesita migración. {e}")
        return False, "La columna ya existe."
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        print(f"Error en la base de datos durante la migración: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    migrate_db()