from unittest import TestCase
from unittest.mock import MagicMock, call

from keyring.errors import KeyringError, PasswordDeleteError

from sqlpinger.core.credentials import (
    DEFAULT_USERNAME_ACCOUNT,
    CredentialStoreError,
    DefaultCredentialStore,
    DefaultCredentials,
)


class TestDefaultCredentialStore(TestCase):
    def setUp(self):
        self.keyring = MagicMock()
        self.store = DefaultCredentialStore(keyring_backend=self.keyring)

    def test_set_default_stores_password_and_username_marker(self):
        self.keyring.get_password.return_value = None

        self.store.set_default("mssql", "user", "secret")

        self.keyring.get_password.assert_called_once_with("sqlpinger:mssql", DEFAULT_USERNAME_ACCOUNT)
        self.keyring.set_password.assert_has_calls([
            call("sqlpinger:mssql", "user", "secret"),
            call("sqlpinger:mssql", DEFAULT_USERNAME_ACCOUNT, "user"),
        ])
        self.keyring.delete_password.assert_not_called()

    def test_set_default_removes_previous_user_password(self):
        self.keyring.get_password.return_value = "old_user"

        self.store.set_default("pg", "new_user", "secret")

        self.keyring.delete_password.assert_called_once_with("sqlpinger:pg", "old_user")

    def test_get_default_returns_credentials(self):
        self.keyring.get_password.side_effect = ["user", "secret"]

        result = self.store.get_default("mssql")

        self.assertEqual(result, DefaultCredentials(username="user", password="secret"))
        self.keyring.get_password.assert_has_calls([
            call("sqlpinger:mssql", DEFAULT_USERNAME_ACCOUNT),
            call("sqlpinger:mssql", "user"),
        ])

    def test_get_default_returns_none_when_username_marker_is_missing(self):
        self.keyring.get_password.return_value = None

        result = self.store.get_default("mssql")

        self.assertIsNone(result)
        self.keyring.get_password.assert_called_once_with("sqlpinger:mssql", DEFAULT_USERNAME_ACCOUNT)

    def test_get_default_returns_none_when_password_is_missing(self):
        self.keyring.get_password.side_effect = ["user", None]

        result = self.store.get_default("mssql")

        self.assertIsNone(result)

    def test_clear_default_deletes_password_and_username_marker(self):
        self.keyring.get_password.return_value = "user"

        removed = self.store.clear_default("pg")

        self.assertTrue(removed)
        self.keyring.delete_password.assert_has_calls([
            call("sqlpinger:pg", "user"),
            call("sqlpinger:pg", DEFAULT_USERNAME_ACCOUNT),
        ])

    def test_clear_default_ignores_missing_entries(self):
        self.keyring.get_password.return_value = "user"
        self.keyring.delete_password.side_effect = PasswordDeleteError("missing")

        removed = self.store.clear_default("pg")

        self.assertFalse(removed)

    def test_keyring_errors_are_wrapped_with_actionable_message(self):
        self.keyring.get_password.side_effect = KeyringError("backend unavailable")

        with self.assertRaises(CredentialStoreError) as context:
            self.store.get_default("mssql")

        self.assertIn("Secure credential storage is unavailable", str(context.exception))
        self.assertIn("backend unavailable", str(context.exception))

    def test_unsupported_engine_raises_credential_store_error(self):
        with self.assertRaises(CredentialStoreError) as context:
            self.store.get_default("mysql")

        self.assertIn("Unsupported credentials engine", str(context.exception))
