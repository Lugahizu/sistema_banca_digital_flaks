from flask_login import UserMixin
import sqlite3
import werkzeug.security

class DatabaseConnectionError(Exception):
    pass
class ItemNotFoundError(Exception):
    pass
class DuplicateItemError(Exception):
    pass
DATABASE_FILE = "lite.db"
_CURRENT_DB_PATH = DATABASE_FILE

class DatabaseManager:
    _active_conn = None
    def __init__(self, database_file):
        self.database_file = database_file
        self.conn = None
        self.cursor = None
    def __enter__(self):
        try:
            if self.database_file == ':memory:' and DatabaseManager._active_conn:
                self.conn = DatabaseManager._active_conn
            else:
                self.conn = sqlite3.connect(self.database_file)
                if self.database_file == ':memory:':
                    DatabaseManager._active_conn = self.conn
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = sqlite3.Row 
            self.cursor = self.conn.cursor()
            return self.cursor
        except sqlite3.OperationalError as e:
            raise DatabaseConnectionError(f"Error al conectar con la base de datos: {e}")
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.database_file != ':memory:':
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            if self.conn:
                self.conn.close()
        else:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
def connect_db(db_path):
    global _CURRENT_DB_PATH
    _CURRENT_DB_PATH = db_path
    return True
def close_connection():
    global _CURRENT_DB_PATH
    if DatabaseManager._active_conn:
        DatabaseManager._active_conn.close()
        DatabaseManager._active_conn = None
    _CURRENT_DB_PATH = DATABASE_FILE
    return True
def initialize_db():
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur:            
            cur.execute("CREATE TABLE IF NOT EXISTS user (id_user TEXT PRIMARY KEY, name TEXT, password_hash TEXT, role TEXT DEFAULT 'cliente')")
            cur.execute("CREATE TABLE IF NOT EXISTS account (id_account INTEGER PRIMARY KEY, id_user TEXT, amount REAL, type TEXT, FOREIGN KEY (id_user) REFERENCES user (id_user) ON DELETE CASCADE)")
            cur.execute("CREATE TABLE IF NOT EXISTS transactions (id_transaction INTEGER PRIMARY KEY, id_account INTEGER, amount REAL, type TEXT, id_user TEXT, FOREIGN KEY (id_account) REFERENCES account (id_account) ON DELETE CASCADE)")
            return True, "Tablas creadas con exito"
    except sqlite3.OperationalError as e:
            raise DatabaseConnectionError(f"Error al crear las tablas: {e}")
    except sqlite3.Error as e:
            raise Exception(f"Error inesperado en la base de datos: {e}")    
def register_user(id_user, name, password):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur:
            cur.execute("SELECT id_user FROM user WHERE id_user = ?", (id_user,))
            existing_user = cur.fetchone()
            if existing_user:
                raise DuplicateItemError(f"El usuario con ID '{id_user}' ya existe.")
            password_hash = werkzeug.security.generate_password_hash(password)
            cur.execute("INSERT INTO user (id_user, name, password_hash, role) VALUES(?, ?, ?, ?)", (id_user, name, password_hash, "cliente"))
            return True, f"Se insertó al usuario con cédula '{id_user}' correctamente."
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise DuplicateItemError(f"El usuario con ID '{id_user}' ya existe.")
    except sqlite3.Error as e:        
        raise Exception(f"Error en la base de datos al registrar usuario: {e}")    
def get_table_data(table_name, id_user=None):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            valid_tables = ["user", "account", "transactions"]
            if table_name not in valid_tables:            
                raise ValueError(f"Tabla '{table_name}' no permitida")
            query = f"SELECT * FROM {table_name}"
            params = []
            if id_user and table_name in ["account", "transactions"]:
                query += f" WHERE id_user = ?"
                params.append(id_user)
            cur.execute(query, tuple(params))        
            rows = cur.fetchall()
            column_names = [description[0] for description in cur.description]
            data_list = []
            for row in rows:
                data_list.append(dict(row))            
            return data_list, column_names, None
    except ValueError as ve:
        return None, None, f"Error: {ve}"
    except sqlite3.Error as e:        
        return None, None, f"Error en la base de datos: {e}"
def get_user_transactions(id_user):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT t.* FROM transactions t INNER JOIN account a ON t.id_account = a.id_account WHERE a.id_user = ?", (id_user,))
            rows = cur.fetchall()
            column_names = [description[0] for description in cur.description]
            data_list = [dict(row) for row in rows]
            return data_list, column_names, None
    except sqlite3.Error as e:
        return None, None, f"Error en la base de datos: {e}"
def delete_user(id_user):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT id_user FROM user WHERE id_user = ?", (id_user,))
            existing_user = cur.fetchone()
            if not existing_user:
                raise ItemNotFoundError(f"El usuario con id {id_user} no existe.")
            cur.execute("DELETE FROM user WHERE id_user = ?", (id_user,))            
            return True, f"Usuario {id_user} eliminado con exito"
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos al eliminar usuario: {e}")
def update_user(id_user, new_name):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("UPDATE user SET name = ? WHERE id_user = ?", (new_name, id_user))
            if not cur.rowcount > 0:
                raise ItemNotFoundError(f"Usuario con cedula {id_user} no encontrado") 
            return True
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos: {e}")
def insert_account(id_user, amount, acc_type):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT id_user FROM user WHERE id_user = ?", (id_user,))
            existing_user = cur.fetchone()
            if not existing_user:
                raise ItemNotFoundError(f"Error: El usuario con ID '{id_user}' no existe:")
            cur.execute("INSERT INTO account (id_user, amount, type) VALUES(?, ?, ?)", (id_user, amount, acc_type))
            return True, f"Se inserto la cuenta para el usuario '{id_user}' correctamente."
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos al insertar la cuenta.")
def update_account(id_account, new_amount):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("UPDATE account SET amount = ? WHERE id_account = ?", (new_amount, id_account))
            if not cur.rowcount > 0:
                raise ItemNotFoundError(f"Numero de cuenta {id_account} no encontrado")
            return True, f"Se actualizo la cuenta numero {id_account}"
    except sqlite3.Error as e:
            raise Exception(f"Error en la base de datos: {e}")
def delete_account(id_account, id_user, user_role):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur:
            if user_role != "admin":
                cur.execute("SELECT id_account FROM account WHERE id_account = ? AND id_user = ?", (id_account, id_user))
                existing_account = cur.fetchone()
                if not existing_account:
                    raise ItemNotFoundError(f"La cuenta '{id_account}' no existe o no te pertenece")
            cur.execute("DELETE FROM account WHERE id_account = ?", (id_account,))
            if cur.rowcount == 0:
                raise ItemNotFoundError(f"La cuenta '{id_account}' no existe o no te pertenece")
            return True, f"La cuenta '{id_account}' fue eliminada con exito."
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos: {e}")
def insert_transaction(account_id, amount, type_transaction, id_user):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT amount FROM account WHERE id_account = ? AND id_user = ?", (account_id, id_user))
            account_data = cur.fetchone()
            if not account_data:
                raise ItemNotFoundError(f"Error: La cuenta especificada {account_id} no existe o no te pertenece.")
            current_balance = account_data[0]
            new_balance = 0
            if type_transaction == "deposito":
                new_balance = current_balance + amount
            elif type_transaction == "retiro":
                if current_balance < amount:
                    raise ValueError("Error: Saldo insuficiente para realizar el retiro.") 
                new_balance = current_balance - amount
            else:
                raise ValueError("Error: Tipo de transacción no válido. Solo se permiten 'deposito' o 'retiro'.")
            cur.execute("UPDATE account SET amount = ? WHERE id_account = ? AND id_user = ?", (new_balance, account_id, id_user))
            cur.execute("INSERT INTO transactions (id_account, amount, type, id_user) VALUES (?, ?, ?, ?)", (account_id, amount, type_transaction, id_user))
            return True, f"Transacción de {type_transaction} completada con éxito. Nuevo saldo: {new_balance}"
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos al insertar la transacción: {e}")
def update_transaction(id_transaction, new_amount = None, new_type = None):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT id_transaction FROM transactions WHERE id_transaction = ?", (id_transaction,))
            existing_transaction = cur.fetchone()
            if not existing_transaction:
                raise ItemNotFoundError(f"La transacción con ID '{id_transaction}' no existe.")
            updates = []
            params = []        
            if new_amount is not None:
                updates.append("amount = ?")
                params.append(new_amount)
            if new_type is not None:
                updates.append("type = ?")
                params.append(new_type)              
            if not updates:
                return True, f"No se proporcionaron campos para actualizar la transacción {id_transaction}."
            query = f"UPDATE transactions SET {', '.join(updates)} WHERE id_transaction = ?"
            params.append(id_transaction)
            cur.execute(query, tuple(params))            
            return True, f"Transaccion {id_transaction} actualizada con exito"
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos al actualizar la transacción: {e}")
def delete_transaction(id_transaction):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            cur.execute("SELECT id_account, amount, type FROM transactions WHERE id_transaction = ?", (id_transaction,)) 
            transaction_data = cur.fetchone()
            if not transaction_data:
                raise ItemNotFoundError(f"La transaccion con ID '{id_transaction}' no existe.")      
            id_account, amount, transaction_type = transaction_data
            cur.execute("SELECT amount FROM account WHERE id_account = ?", (id_account,))
            account_balance_data = cur.fetchone()
            if not account_balance_data:
                raise ItemNotFoundError(f"La cuenta con ID '{id_account}' asociada a la transacion no existe.")
            account_balance = account_balance_data[0]
            new_balance = 0
            if transaction_type == "deposito":
                new_balance = account_balance - amount
            elif transaction_type == "retiro":
                new_balance = account_balance + amount
            else:
                raise ValueError("Tipo de transacción no válido para reversión.")
            cur.execute("UPDATE account SET amount = ? WHERE id_account = ?", (new_balance, id_account))
            cur.execute("DELETE FROM transactions WHERE id_transaction = ?", (id_transaction,))
            return True, f"La transacción {id_transaction} fue eliminada con éxito."
    except sqlite3.Error as e:
            raise Exception(f"Error en la base de datos: {e}")
def update_user_profile(id_user, new_name = None, new_password = None):
    try:
        with DatabaseManager(_CURRENT_DB_PATH) as cur: 
            updates = []
            params = []
            if new_name:
                updates.append("name = ?")
                params.append(new_name)
            if new_password:
                new_password_hash = werkzeug.security.generate_password_hash(new_password)
                updates.append("password_hash = ?")
                params.append(new_password_hash)
            if not updates:
                raise ValueError("No se proporcionaron datos para actualizar.")
            query = f"UPDATE user SET {",".join(updates)} WHERE id_user = ?"
            params.append(id_user)
            cur.execute(query, tuple(params))
            if cur.rowcount == 0:
                raise ItemNotFoundError(f"El usuario con ID '{id_user}' no fue encontrado.")        
            return True, f"Perfil actualizado con éxito."
    except sqlite3.Error as e:
        raise Exception(f"Error en la base de datos al actualizar el perfil: {e}")
class User(UserMixin):
    def __init__(self, id_user, name, password_hash, role):
        self.id = id_user
        self.name = name
        self.password_hash = password_hash
        self.role = role
    def check_password(self, password):
        return werkzeug.security.check_password_hash(self.password_hash, password)
def get_user(id_user):
    with DatabaseManager(_CURRENT_DB_PATH) as cur: 
        cur.execute("SELECT id_user, name, password_hash, role FROM user WHERE id_user = ?", (id_user,))
        user_data = cur.fetchone()
        if user_data:
            return User(*user_data)
        return None
def get_all_users():
    with DatabaseManager(_CURRENT_DB_PATH) as cur:
        cur.execute("SELECT * FROM user")
        rows = cur.fetchall()
        return [User(*dict(row).values()) for row in rows]
def get_account(id_account):
    with DatabaseManager(_CURRENT_DB_PATH) as cur:
        cur.execute("SELECT id_account, id_user, amount,type FROM account WHERE id_account = ?", (id_account,))
        account_data = cur.fetchone()
        if account_data:
            return type('Account', (object,), {'id': account_data[0], 'user_id': account_data[1], 'balance': account_data[2], 'type': account_data[3]})
        return None
def update_user_name(id_user, new_name):
    return update_user(id_user, new_name)            
