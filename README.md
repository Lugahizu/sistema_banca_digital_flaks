# Sistema de Banca Digital (Backend Python/Flask)

## Descripción

Implementación de una aplicación web de banca funcional con enfoque en la **seguridad, la integridad transaccional y el testing unitario**. Este proyecto simula las operaciones básicas de una entidad bancaria (registro de clientes, login, depósitos, retiros y validación de roles de administrador).

## Tecnologías

* **Backend:** Python 3.x, Flask (Micro-framework)
* **Base de Datos:** SQLite3 (Persistencia de datos transaccionales)
* **Frontend:** Jinja2 (Templates para HTML dinámico)
* **Seguridad/Auth:** Flask-Login, `werkzeug.security` (hashing de contraseñas)
* **Testing:** Módulo `unittest`

## Características Clave

* **Control de Acceso Basado en Roles (RBAC):** Separación de funcionalidades de `cliente` y `administrador` mediante un decorador personalizado.
* **Integridad Transaccional:** Funciones de depósito y retiro que validan el saldo y garantizan la consistencia de los datos.
* **Pruebas Unitarias Robustas:** Más de 15 tests que cubren el 100% de la lógica de negocio.
* **Autenticación Segura:** Implementación de `Flask-Login` para gestión de sesiones y *hashing* de contraseñas para proteger las credenciales.
## Ejecución Local

### Requisitos

Asegúrese de tener instalado Python 3.x y `pip`.

### Instalación

1.  Clone el repositorio:
    ```bash
    git clone [https://github.com/Lugahizu/sistema_banca_digital_flaks.git](https://github.com/Lugahizu/sistema_banca_digital_flaks.git)
    cd sistema_banca_digital_flaks
    ```
2.  Instale las dependencias (necesitas crear un archivo `requirements.txt` en tu proyecto con las librerías):
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecute la aplicación:
    ```bash
    python app.py
    ```
4.  Acceda a la aplicación en su navegador en `http://127.0.0.1:5000/`.

### Cómo Ejecutar Tests

Ejecute los tests unitarios para validar la lógica de negocio:
```bash
python tests.py