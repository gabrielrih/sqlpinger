from unittest import TestCase
from pytest import raises

from sqlpinger.engines.postgres.auth.common import PostgresAuthStrategyFactory, PostgresAuthTypes
from sqlpinger.engines.postgres.auth.sql_auth import PostgresSqlAuth


class TestPostgresAuthStrategyFactory(TestCase):
    def test_create_when_sql_authentication(self):
        auth_strategy = PostgresAuthStrategyFactory.create(
            auth=PostgresAuthTypes.SQL.value,
            timeout_in_seconds=10,
            username='username',
            password='password',
        )
        self.assertIsInstance(auth_strategy, PostgresSqlAuth)

    def test_create_when_sql_authentication_missing_inputs(self):
        with raises(ValueError) as exc:
            PostgresAuthStrategyFactory.create(
                auth=PostgresAuthTypes.SQL.value,
                timeout_in_seconds=10,
            )
        error_message: str = str(exc.value)
        self.assertEqual(error_message, "PostgreSQL SQL authentication requires both username and password")

    def test_invalid_auth_method_windows(self):
        invalid_auth = 'windows'
        with raises(NotImplementedError) as exc:
            PostgresAuthStrategyFactory.create(
                auth=invalid_auth,
                timeout_in_seconds=10,
                username='u',
                password='p',
            )
        error_message: str = str(exc.value)
        self.assertEqual(error_message, f"Authentication method '{invalid_auth}' is not supported")

    def test_invalid_auth_method_azure_ad(self):
        invalid_auth = 'azure-ad'
        with raises(NotImplementedError) as exc:
            PostgresAuthStrategyFactory.create(
                auth=invalid_auth,
                timeout_in_seconds=10,
                username='u',
                password='p',
            )
        error_message: str = str(exc.value)
        self.assertEqual(error_message, f"Authentication method '{invalid_auth}' is not supported")
