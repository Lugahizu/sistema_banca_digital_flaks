import unittest
import os
from app import create_app
from app.db import database
from app.db import ItemNotFoundError, DuplicateItemError

class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'DATABASE_URL': ':memory:'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        database.connect_db(':memory:')
        database.initialize_db()
    def tearDown(self):
        self.app_context.pop()
        database.close_connection()
    def test_a_user_can_be_registered_and_retrieved(self):        
        user_id = "12345678"
        name = "Test User"
        password = "test_password"
        resul = database.register_user(user_id, name, password)
        self.assertTrue(resul, "El registro del usuario deberia ser exitoso.")
        user = database.get_user(user_id)
        self.assertIsNotNone(user, "El usuario debe ser encontrado.")
        self.assertEqual(user.id, user_id)
        self.assertEqual(user.name, name)
        self.assertTrue(user.check_password(password), "La contraseña debe ser correcta.")
    def test_user_can_be_deleted(self):
        database.initialize_db()
        user_id = "999"
        database.register_user(user_id, "To Delete", "hash")
        result, message = database.delete_user(user_id)
        self.assertTrue(result, "La eliminacion debe ser exitosa.")
        deleted_user = database.get_user(user_id)
        self.assertIsNone(deleted_user, "El usuario no debe ser encontrado despues de la eliminacion.")
    def test_user_name_can_be_updated(self):
        database.initialize_db()
        user_id = "888"
        old_name = "Old Name"
        new_name = "New Name"
        database.register_user(user_id, old_name, "hash")
        result = database.update_user_name(user_id, new_name)
        self.assertTrue(result, "La actualizacion debe ser exitosa.")
        updated_user = database.get_user(user_id)
        self.assertEqual(updated_user.name, new_name, "El nombre debe ser actualizado.")
    def test_account_creation_and_retrieval(self):
        database.initialize_db()
        user_id = "777"
        initial_amount = 500.0
        database.register_user(user_id, "Account Holder", "hash")
        result, message = database.insert_account(user_id, initial_amount, "ahorros")
        self.assertTrue(result, "La insercion de cuenta debe ser exitosa.")
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        self.assertEqual(len(accounts), 1, "Solo debe haber una cuenta.")
        account_data = accounts[0]
        self.assertEqual(account_data["amount"], initial_amount)
        self.assertEqual(account_data["id_user"], user_id)
    def test_withdrawal_fails_on_insufficient_funds(self):
        database.initialize_db()
        user_id = "555"
        initial_amount = 50.0
        withdrawal_amount = 100.0
        database.register_user(user_id, "Spender", "hash")
        database.insert_account(user_id, initial_amount, 'savings')
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        account_id = accounts[0]['id_account']
        with self.assertRaises(ValueError) as context:
            database.insert_transaction(account_id, withdrawal_amount, 'retiro', user_id)
        self.assertIn("Saldo insuficiente", str(context.exception))
        updated_account = database.get_account(account_id)
        self.assertEqual(updated_account.balance, initial_amount, "El saldo debe permanecer inalterado.")
    def test_cannot_register_duplicate_user(self):
        database.initialize_db()
        user_id = "444"
        database.register_user(user_id, "Original User", "pass1")        
        with self.assertRaises(DuplicateItemError) as context:
            database.register_user(user_id, "Duplicate User", "pass2")
        self.assertIn(f"El usuario con ID '{user_id}' ya existe.", str(context.exception))
    def test_cannot_delete_nonexistent_user(self):
        database.initialize_db()
        non_existent_id = "000"
        with self.assertRaises(ItemNotFoundError) as context:
            database.delete_user(non_existent_id)
        self.assertIn(f"El usuario con id {non_existent_id} no existe.", str(context.exception))

    def test_deposit_transaction_updates_balance(self):
        database.initialize_db()
        user_id = "666"
        initial_amount = 100.0
        deposit_amount = 250.0
        database.register_user(user_id, "Depositor", "hash")
        database.insert_account(user_id, initial_amount, "savings")
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        account_id = accounts[0]["id_account"]
        result, message = database.insert_transaction(account_id, deposit_amount, "deposito", user_id)
        self.assertTrue(result, "La transaccion de deposito deberia ser exitosa.")
        update_account = database.get_account(account_id)
        expected_balance = initial_amount + deposit_amount
        self.assertEqual(update_account.balance, expected_balance, "El saldo debe ser el inicial más el depósito.")
        transactions, _, _ = database.get_table_data("transactions", id_user=user_id)
        self.assertEqual(len(transactions), 1, "Debe haber una transacción registrada.")
    def test_cannot_delete_other_user_account(self):
        database.initialize_db()
        user_a_id = "A_111"
        user_b_id = "B_222"
        database.register_user(user_a_id, "User A", "passA")
        database.register_user(user_b_id, "User B", "passB")
        database.insert_account(user_b_id, 500.0, "checking")
        accounts_b, _, _ = database.get_table_data("account", id_user=user_b_id)
        account_b_id = accounts_b[0]["id_account"]
        user_a_role = "cliente"
        with self.assertRaises(ItemNotFoundError) as context:
            database.delete_account(account_b_id, user_a_id, user_a_role)
        self.assertIn(
            f"La cuenta '{account_b_id}' no existe o no te pertenece", 
            str(context.exception),
            "Debe fallar al intentar eliminar una cuenta ajena."
        )
        account_b_after_attempt = database.get_account (account_b_id)
        self.assertIsNotNone(
            account_b_after_attempt, 
            "La cuenta ajena no debe haber sido eliminada."
        ) 
    def test_transaction_can_be_updated(self):
        database.initialize_db()
        user_id = "T_UPD_1"
        initial_amount = 500.0
        transaction_amount = 100.0
        database.register_user(user_id, "Updater", "pass")
        database.insert_account(user_id, initial_amount, "savings")
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        account_id = accounts[0]["id_account"]
        database.insert_transaction(account_id, transaction_amount, "deposito", user_id)
        transactions, _, _ = database.get_table_data("transactions", id_user=user_id)
        transaction_id = transactions[0]['id_transaction']
        new_amount = 150.0
        new_type = "retiro"
        result, message = database.update_transaction(transaction_id, new_amount=new_amount, new_type=new_type)
        transactions_after, _, _ = database.get_table_data("transactions", id_user=user_id)
        updated_transaction = transactions_after[0]        
        self.assertEqual(updated_transaction['amount'], new_amount, "El monto de la transacción debe ser actualizado.")
        self.assertEqual(updated_transaction['type'], new_type, "El tipo de la transacción debe ser actualizado.")
        account_after_update = database.get_account(account_id)
        expected_balance_after_deposit = initial_amount + transaction_amount # 600.0
        self.assertEqual(account_after_update.balance, expected_balance_after_deposit, "La actualización de la transacción no debe afectar el saldo de la cuenta.")
    def test_transaction_deletion_reverses_balance(self):
        database.initialize_db()
        user_id = "T_DEL_1"
        initial_amount = 200.0
        deposit_amount = 100.0        
        database.register_user(user_id, "Deleter", "pass")
        database.insert_account(user_id, initial_amount, "checking")
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        account_id = accounts[0]["id_account"]
        database.insert_transaction(account_id, deposit_amount, "deposito", user_id)
        transactions, _, _ = database.get_table_data("transactions", id_user=user_id)
        transaction_id = transactions[0]['id_transaction']
        current_balance = database.get_account(account_id).balance
        self.assertEqual(current_balance, 300.0, "El saldo inicial debe ser 300.0.")
        result, message = database.delete_transaction(transaction_id)
        self.assertTrue(result, "La eliminación de la transacción debe ser exitosa.")
        expected_balance_after_reversal = initial_amount 
        account_after_delete = database.get_account(account_id)
        self.assertEqual(
            account_after_delete.balance, 
            expected_balance_after_reversal, 
            "El saldo debe revertirse al estado previo a la transacción eliminada."
        )
        transactions_after_delete, _, _ = database.get_table_data("transactions", id_user=user_id)
        self.assertEqual(len(transactions_after_delete), 0, "La transacción debe ser eliminada de la tabla.")
    def test_admin_can_delete_any_account(self):
        database.initialize_db()
        admin_id = "ADMIN_1"
        user_id = "USER_2"
        database.register_user(admin_id, "The Admin", "admin_pass")
        database.register_user(user_id, "Regular User", "user_pass")
        database.insert_account(user_id, 1000.0, "checking")
        accounts, _, _ = database.get_table_data("account", id_user=user_id)
        account_to_delete_id = accounts[0]["id_account"]        
        admin_role = "admin"
        result, message = database.delete_account(
            account_to_delete_id, 
            admin_id, 
            admin_role
        )        
        self.assertTrue(result, "El administrador debe poder eliminar cualquier cuenta.")        
        deleted_account = database.get_account(account_to_delete_id)
        self.assertIsNone(deleted_account, "La cuenta del usuario debe haber sido eliminada por el administrador.")
    def test_user_profile_can_be_updated_fully(self):
        database.initialize_db()
        user_id = "PROFILE_1"
        old_name = "Old Name"
        old_password = "old_password"
        new_name = "New Name"
        new_password = "new_strong_password"
        database.register_user(user_id, old_name, old_password)
        result, message = database.update_user_profile(
            user_id, 
            new_name=new_name, 
            new_password=new_password
        )
        self.assertTrue(result, "La actualización completa del perfil debe ser exitosa.")
        updated_user = database.get_user(user_id)
        self.assertEqual(updated_user.name, new_name, "El nombre del usuario debe ser actualizado.")
        self.assertTrue(
            updated_user.check_password(new_password), 
            "La nueva contraseña debe ser válida y estar hasheada correctamente."
        )
        self.assertFalse(
            updated_user.check_password(old_password),
            "La contraseña anterior ya no debe ser válida."
        )
    def test_delete_user_deletes_accounts(self):
        database.initialize_db()
        user_id = "CASCADE_3"
        database.register_user(user_id, "User with Accounts", "pass")
        database.insert_account(user_id, 100.0, "checking")
        database.insert_account(user_id, 200.0, "savings")
        initial_accounts, _, _ = database.get_table_data("account", id_user=user_id)
        self.assertEqual(len(initial_accounts), 2, "Debe haber 2 cuentas creadas.")
        database.delete_user(user_id)
        deleted_user = database.get_user(user_id)
        self.assertIsNone(deleted_user, "El usuario debe ser eliminado.")
        remaining_accounts, _, _ = database.get_table_data("account", id_user=user_id)
        self.assertEqual(len(remaining_accounts), 0, "Las cuentas del usuario deben eliminarse automáticamente (CASCADE).")
    def test_get_account_not_found(self):
        database.initialize_db()
        non_existent_account_id = 9999
        account = database.get_account(non_existent_account_id)
        self.assertIsNone(account, "Buscar una cuenta inexistente debe devolver None.")
