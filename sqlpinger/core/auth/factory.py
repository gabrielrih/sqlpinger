from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.auth.sql_auth import SqlAuth
from sqlpinger.core.auth.azure_ad import AzureADInteractive
from sqlpinger.core.auth.windows_auth import WindowsAuth


class AuthStrategyFactory:
    @staticmethod
    def create(auth: str, driver: str, timeout_in_seconds: int, username: str = '', password: str = '') -> AuthStrategy:
        auth = auth.lower()
        if auth == 'sql':
            if not username or not password:
                raise ValueError("SQL authentication requires both username and password")
            return SqlAuth(username, password, driver, timeout_in_seconds)
        if auth == 'windows':
            return WindowsAuth(driver, timeout_in_seconds)
        if auth == 'azure-ad':
            return AzureADInteractive(driver, timeout_in_seconds)
        raise NotImplementedError(f"Authentication method '{auth}' is not supported")
