from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.auth.sql_auth import SqlAuth
from sqlpinger.core.auth.azure_ad import AzureADInteractive


class AuthStrategyFactory:
    @staticmethod
    def create(auth: str, driver: str, username: str = '', password: str = '') -> AuthStrategy:
        auth = auth.lower()
        if auth == 'sql':
            if not username or not password:
                raise ValueError("SQL authentication requires both username and password")
            return SqlAuth(username, password, driver)
        if auth == 'azure-ad':
            return AzureADInteractive(driver)
        raise NotImplementedError(f"Authentication method '{auth}' is not supported")
