from flask import Blueprint, render_template, request, redirect, url_for, flash
from .db import database
from flask_login import login_user, logout_user, login_required, current_user
from .utils.utils import is_valid_input
from functools import wraps

main = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_funcion(*args, **kwars):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("No tienes permiso para realizar esta accion.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwars)
    return decorated_funcion
@main.route("/")
def index():
    valid_tables = ["user", "account", "transactions"] 
    return render_template("index.html", tables_for_select = valid_tables)
@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesion exitosamente.", "info")
    return redirect(url_for("main.index"))
@main.route("/register")
def register():
    if current_user.is_authenticated:
        flash("Ya has iniciado sesión. No necesitas registrarte de nuevo.", "info")
        return redirect(url_for("main.index"))
    return render_template("register.html")
@main.route("/register", methods=["POST"])
def register_user():
    id_user = request.form.get("id_usuario")
    name = request.form.get("nombre")
    password = request.form.get("password")
    if not id_user or not name or not password:
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for("main.register"))
    try:
        database.register_user(id_user, name, password)
        flash("¡Registro exitoso! Ya puede iniciar sesion.", "success")
        return redirect(url_for("main.login"))
    except database.DuplicateItemError as e:
        flash(str(e), "error")
        return redirect(url_for("main.register"))
    except Exception as e:
        print(f"Error inesperado: {e}")
        flash("Ocurrió un error inesperado al registrar el usuario.", "error")
        return redirect(url_for("main.register"))
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        id_user = request.form.get("id_usuario")    
        password = request.form.get("password")
        user = database.get_user(id_user)
        if user and user.check_password(password):
            login_user(user)
            flash("Inicio de sesion exitoso", "success")
            return redirect(url_for("main.index"))
        flash("Cedula o contraseña incorrecta.", "error")
    return render_template("login.html")
@main.route("/view/", methods=["GET"])
@login_required
def view_table():
    table_name = request.args.get("ver_tabla")      
    if not table_name:
        flash("No se ha especificado ninguna tabla para ver.")
        return redirect(url_for("main.index"))    
    if table_name not in ["user", "account", "transactions"]:
        flash("Tabla no válida.", "error")
        return redirect(url_for("main.index"))
    id_user = None
    if current_user.role != "admin":
        if table_name == "user":
            flash("No tienes permiso para ver esta tabla.", "error")
            return redirect(url_for("main.index"))        
        if table_name in ["account", "transactions"]:
            id_user = current_user.id
    try:
        data, column_name, error_message = database.get_table_data(table_name, id_user)
        if error_message:
            flash(error_message, "error")
            return redirect(url_for("main.index"))        
        return render_template("dynamic_table_view.html", table_name = table_name.capitalize(), data=data, column_name = column_name)
    except Exception as e:
        print(f"Error general en la vista de tabla: {e}")
        flash("Error al cargar los datos de la tabla.", "error")
        return redirect(url_for("main.index"))
@main.route("/my_transactions/")
@login_required
def my_transactions():
    data, columns, error = database.get_user_transactions(current_user.id)
    if error:
        flash(error, "error")
        return redirect(url_for("main.index"))
    return render_template("view_data.html", data=data, columns=columns, table_name="transactions")
@main.route("/delete_user/", methods = ["POST"])
@login_required
@admin_required
def delete_user():
    id_usuario_borrar = is_valid_input(request.form.get("id_usuario_borrar"))
    if id_usuario_borrar is None:
        flash("Error: El ID de usuario no es válido.", "error")
        return redirect(url_for("main.index"))
    try:                             
        database.delete_user(id_usuario_borrar)
        flash(f"Usuario {id_usuario_borrar} eliminado con exito.", "success")
        return redirect(url_for("main.view_table", ver_tabla="user"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        print(f"Error inesperado al eliminar usuario: {e}")
        flash("Ocurrió un error inesperado al eliminar el usuario. Inténtalo de nuevo.", "error")
        return redirect(url_for("main.index"))
@main.route("/update_user/", methods = ["POST"])
@login_required
@admin_required
def update_user():            
    id_user = is_valid_input(request.form.get("id_usuario"))
    new_name = request.form.get("nombre")
    if id_user is None:
        flash("Error: La cedula debe ser un numero valido.", "error")
        return redirect(url_for("main.index"))   
    if not new_name:
        flash("Error: Faltan el nuevo nombre en el formulario.", "error")
        return redirect(url_for("main.index"))
    try:        
        database.update_user(id_user, new_name)
        flash(f"Usuario con cedula '{id_user}' acutualizado con exito.", "success")
        return redirect(url_for("main.view_table", ver_tabla = "user"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))    
    except Exception as e:
        print(f"Error inesperado al modificar usuario: {e}")
        flash("Ocurrio un error inesperado al modificar el usuario. Intentalo de nuevo.", "error")
        return redirect(url_for("main.index"))
@main.route("/insert_account/", methods=["POST"])
@login_required
@admin_required
def insert_account():
    id_user = is_valid_input(request.form.get("id_usuario"))
    amount = is_valid_input(request.form.get("monto"), is_float=True)
    account_type = request.form.get("tipo_cuenta")
    if id_user is None:
        flash("Error: El ID del usuario no es un número válido.", "error")
        return redirect(url_for("main.index"))
    if amount is None:
        flash("Error: El monto no es un número válido.", "error")
        return redirect(url_for("main.index"))
    if not account_type:
        flash("Error: Faltan datos para crear la cuenta.", "error")
        return redirect(url_for("main.index"))
    try:        
        database.insert_account(id_user, amount, account_type)
        flash(f"Se inserto la cuenta para el usuario '{id_user}' correctamente", "success")
        return redirect(url_for("main.view_table", ver_tabla="account"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        print(f"Error inesperado al insertar la cuenta: {e}")
        flash("Ocurrió un error inesperado al insertar la cuenta. Inténtalo de nuevo.", "error")
        return redirect(url_for("main.index"))   
@main.route("/insert_transaction/", methods=["POST"])
@login_required
def insert_transaction():    
    id_account = is_valid_input(request.form.get("id_account"))
    amount = is_valid_input(request.form.get("amount"), is_float=True)
    type_transaction = request.form.get("type_transaction")
    if id_account is None:
        flash("Error: El ID de la cuenta deben ser un número válido.", "error")
        return redirect(url_for("main.index"))
    if amount is None:
        flash("Error: El monto de la cuenta deben se un número válido.", "error")
        return redirect(url_for("main.index"))        
    if not type_transaction:
        flash("Error: Tipo de la transaccion invalido.", "error")
        return redirect(url_for("main.index"))
    try:        
        database.insert_transaction(id_account, amount, type_transaction, current_user.id)
        flash(f"Transaccion de {type_transaction} completada con exito.", "success")
        return redirect(url_for("main.view_table", ver_tabla="transactions"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        print("Error inesperado al insertar la transacción: {e}")
        flash("Ocurrió un error inesperado al insertar la transacción.", "error")
        return redirect(url_for("main.index"))
@main.route("/delete_account/", methods=["POST"])
@login_required
def delete_account():
    id_account = is_valid_input(request.form.get("id_account"))
    if id_account is None:
        flash("Error: El ID de la cuenta no fue proporcionado.", "error")
        return redirect(url_for("main.index"))
    try:        
        database.delete_account(id_account, current_user.id, current_user.role)
        flash(f"La cuenta con ID '{id_account}' fue eliminada con exito", "success")
        return redirect(url_for("main.view_table", ver_tabla="account")) 
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))    
    except Exception as e:
        print(f"Error inesperado al eliminar la cuenta: {e}")
        flash("Ocurrió un error inesperado al eliminar la cuenta.", "error")
        return redirect(url_for("main.index"))
@main.route("/update_account/", methods=["POST"])
@login_required
@admin_required
def update_account():
    id_account = is_valid_input(request.form.get("id_account"))
    new_amount = is_valid_input(request.form.get("new_amount"))
    if id_account is None:
        flash("Error: El ID de la cuenta debe ser números válidos.", "error")
        return redirect(url_for("main.index"))
    if new_amount is None:
        flash("Error: El nuevo monto debe ser números válidos.", "error")
        return redirect(url_for("main.index"))
    try:
        database.update_account(id_account, new_amount)
        flash(f"La cuenta numero '{id_account}' fue actualizada con exito.", "success")
        return redirect(url_for("main.view_table", ver_tabla="account"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))    
    except Exception as e:
        print(f"Error inesperado al modificar la cuenta: {e}")
        flash("Ocurrió un error inesperado al modificar la cuenta. Inténtalo de nuevo.", "error")
        return redirect(url_for("main.index"))
@main.route("/update_transaction/", methods = ["POST"])
@login_required
@admin_required
def update_transaction():    
    id_transaction = is_valid_input(request.form.get("id_transaction"))
    new_amount = is_valid_input(request.form.get("new_amount"))
    new_type = request.form.get("new_type")
    if id_transaction is None:
        flash("Error: El ID de la transacción debe ser números válidos.", "error")
        return redirect(url_for("main.index"))
    if new_amount is None:
        flash("Error: El nuevo monto debe ser un número válido.", "error")
        return redirect(url_for("main.index"))
    if not new_type:
        flash("Error: Falta el tipo de transaction.", "error")
        return redirect(url_for("main.index"))
    try:
        database.update_transaction(id_transaction, new_amount, new_type)
        flash(f"La transaccion {id_transaction} fue actualizada con exito.", "success")
        return redirect(url_for("main.view_table", ver_tabla="transactions"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        print(f"Error inesperado al modificar la transacción: {e}")
        flash("Ocurrió un error inesperado al modificar la transacción.", "error")
        return redirect(url_for("main.index"))
@main.route("/delete_transaction/", methods = ["POST"])
@login_required
@admin_required
def delete_transaction():
    transaction_id = is_valid_input(request.form.get("transaction_id"))
    print(f"ID de transacción recibido: '{transaction_id}'")
    if transaction_id is None:
        flash("Error: El ID de la transacción debe ser un número válido.", "error")
        return redirect(url_for("main.index"))
    try:
        database.delete_transaction(transaction_id)
        flash(f"La transacción {transaction_id} fue eliminada con éxito.", "success")
        return redirect(url_for("main.view_table", ver_tabla="transactions"))
    except database.ItemNotFoundError as e:
        flash(str(e), "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        print(f"Error inesperado al eliminar la transacción: {e}")
        flash("Ocurrió un error inesperado al eliminar la transacción. Inténtalo de nuevo.", "error")    
        return redirect(url_for("main.index"))
@main.route("/profile/", methods=["GET","POST"])
@login_required
def profile():
    if request.method == "POST":
        new_name = request.form.get("new_name")
        current_password = request.form.get("current_password")        
        new_password = request.form.get("new_password")
        if not current_password:
            flash(f"Necesitas proporcionar tu contraseña actual para actualizar tu perfil", "error")
            return redirect(url_for("main.profile"))
        if not current_user.check_password(current_password):
            flash(f"Contraseña actual incorrecta.", "error")
            return redirect(url_for("main.profile"))
        try:
            database.update_user_profile(current_user.id, new_name, new_password)
            flash("Perfil actualizado con éxito.", "success")
            return redirect(url_for("main.profile"))
        except (database.ItemNotFoundError, ValueError) as e:
            flash(str(e), "error")
            return redirect(url_for("main.profile"))
        except Exception as e:
            print(f"Error inesperado: {e}")
            flash("Ocurrio un error inesperado al actualizar tu perfil.", "error")
            return redirect(url_for("main.profile"))
    return render_template("profile.html")
@main.route("/admin_dashboard/")
@admin_required
def admin_dashboard():
    admin_tables = ["user", "account", "transaction"]
    return render_template("admin_dashboard.html", admin_tables=admin_tables)

if __name__ == '__main__':    
    main.run(debug=True)
