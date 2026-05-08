from sqlpinger.core.auth.base import AuthStrategy, ListableEnum
from sqlpinger.engines.postgres.auth.sql_auth import PostgresSqlAuth


class PostgresAuthTypes(ListableEnum):
    SQL = 'sql'


class PostgresAuthStrategyFactory:
    @staticmethod
    def create(auth: str, timeout_in_seconds: int,
               username: str = '', password: str = '',
               port: int = 5432, sslmode: str = 'require') -> AuthStrategy:
        auth = auth.lower()
        if auth == PostgresAuthTypes.SQL.value:
            if not username or not password:
                raise ValueError("PostgreSQL SQL authentication requires both username and password")
            return PostgresSqlAuth(
                username=username,
                password=password,
                port=port,
                sslmode=sslmode,
                timeout_in_seconds=timeout_in_seconds,
            )
        raise NotImplementedError(f"Authentication method '{auth}' is not supported")
