import unittest
from app import create_app
from app.db import database
from flask import url_for

TEST_USER_ID = "1234"
TEST_NAME = "TestUser"
TEST_PASSWORD = "password123"

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'DATABASE_URL': ':memory:',
            'SERVER_NAME': 'test.app',
            'SECRET_KEY': 'clave_secreta_para_testing'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()        
        database.connect_db(':memory:')
        database.initialize_db()
    def tearDown(self):
        self.app_context.pop()
        database.close_connection()
    def register_test_user(self, user_id=TEST_USER_ID, password=TEST_PASSWORD, name=TEST_NAME):
        return database.register_user(user_id, name, password)
    def login(self, user_id, password):
        return self.client.post(
            url_for('main.login'),
            data={'id_usuario': user_id, 'password':password},
            follow_redirects=True
        )
    def test_register_success(self):
        data = {
            'id_usuario': '9876',
            'nombre': 'New Registrant',
            'password': 'safe_password'
        }
        response = self.client.post(
            url_for('main.register_user'),
            data=data,
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registro exitoso!", response.data)
        user = database.get_user(data["id_usuario"])
        self.assertIsNotNone(user, "El usuario debe existir en la base de datos.")
        self.assertEqual(user.name, data['nombre'])
    def test_login_success(self):
        self.register_test_user()
        response = self.login(TEST_USER_ID, TEST_PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hola, TestUser!", response.data, "Debe mostrar el saludo del usuario logueado.")
        self.assertIn(b"Bienvenido a tu banca personal", response.data, "Debe estar en el dashboard del cliente.")
