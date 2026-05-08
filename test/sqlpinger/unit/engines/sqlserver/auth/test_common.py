from unittest import TestCase
from pytest import raises

from sqlpinger.engines.sqlserver.auth.common import SqlServerAuthStrategyFactory, SqlServerAuthTypes
from sqlpinger.engines.sqlserver.auth.sql_auth import SqlAuth
from sqlpinger.engines.sqlserver.auth.windows_auth import WindowsAuth
from sqlpinger.engines.sqlserver.auth.azure_ad import AzureADInteractive


class TestSqlServerAuthStrategyFactory(TestCase):
    def test_create_when_sql_authentication(self):
        auth_strategy = SqlServerAuthStrategyFactory.create(
            auth=SqlServerAuthTypes.SQL.value, driver='any_here', username='username', password='password', timeout_in_seconds=10
        )
        self.assertIsInstance(auth_strategy, SqlAuth)

    def test_create_when_sql_authentication_missing_inputs(self):
        with raises(ValueError) as exc:
            SqlServerAuthStrategyFactory.create(
                auth=SqlServerAuthTypes.SQL.value, driver='any_here', timeout_in_seconds=10
            )
        error_message: str = str(exc.value)
        self.assertEqual(error_message, "SQL authentication requires both username and password")

    def test_create_when_windows_authentication(self):
        auth_strategy = SqlServerAuthStrategyFactory.create(
            auth=SqlServerAuthTypes.WINDOWS.value, driver='any_here', timeout_in_seconds=10
        )
        self.assertIsInstance(auth_strategy, WindowsAuth)

    def test_create_when_azure_ad(self):
        auth_strategy = SqlServerAuthStrategyFactory.create(
            auth=SqlServerAuthTypes.AZURE_AD.value, driver='any_here', timeout_in_seconds=10
        )
        self.assertIsInstance(auth_strategy, AzureADInteractive)

    def test_invalid_auth_method(self):
        invalid_auth = 'any'
        with raises(NotImplementedError) as exc:
            SqlServerAuthStrategyFactory.create(auth=invalid_auth, driver='any', timeout_in_seconds=10)
        error_message: str = str(exc.value)
        self.assertEqual(error_message, f"Authentication method '{invalid_auth}' is not supported")
