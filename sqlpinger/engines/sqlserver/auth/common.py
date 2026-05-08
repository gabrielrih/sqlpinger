from sqlpinger.core.auth.base import AuthStrategy, ListableEnum
from sqlpinger.engines.sqlserver.auth.sql_auth import SqlAuth
from sqlpinger.engines.sqlserver.auth.azure_ad import AzureADInteractive
from sqlpinger.engines.sqlserver.auth.windows_auth import WindowsAuth


class SqlServerAuthTypes(ListableEnum):
    SQL = 'sql'
    WINDOWS = 'windows'
    AZURE_AD = 'azure-ad'


class SqlServerAuthStrategyFactory:
    @staticmethod
    def create(auth: str, driver: str, timeout_in_seconds: int, username: str = '', password: str = '') -> AuthStrategy:
        auth = auth.lower()
        if auth == SqlServerAuthTypes.SQL.value:
            if not username or not password:
                raise ValueError("SQL authentication requires both username and password")
            return SqlAuth(username, password, driver, timeout_in_seconds)
        if auth == SqlServerAuthTypes.WINDOWS.value:
            return WindowsAuth(driver, timeout_in_seconds)
        if auth == SqlServerAuthTypes.AZURE_AD.value:
            return AzureADInteractive(driver, timeout_in_seconds)
        raise NotImplementedError(f"Authentication method '{auth}' is not supported")
