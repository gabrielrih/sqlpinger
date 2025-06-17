from enum import Enum
from typing import List

from sqlpinger.core.auth.base import AuthStrategy
from sqlpinger.core.auth.sql_auth import SqlAuth
from sqlpinger.core.auth.azure_ad import AzureADInteractive
from sqlpinger.core.auth.windows_auth import WindowsAuth


class AuthTypes(Enum):
    SQL = 'sql'
    WINDOWS = 'windows'
    AZURE_AD = 'azure-ad'

    @classmethod
    def to_list(cls) -> List[str]:
        return [ type.value for type in AuthTypes ]


class AuthStrategyFactory:
    @staticmethod
    def create(auth: str, driver: str, timeout_in_seconds: int, username: str = '', password: str = '') -> AuthStrategy:
        auth = auth.lower()
        if auth == AuthTypes.SQL.value:
            if not username or not password:
                raise ValueError("SQL authentication requires both username and password")
            return SqlAuth(username, password, driver, timeout_in_seconds)
        if auth == AuthTypes.WINDOWS.value:
            return WindowsAuth(driver, timeout_in_seconds)
        if auth == AuthTypes.AZURE_AD.value:
            return AzureADInteractive(driver, timeout_in_seconds)
        raise NotImplementedError(f"Authentication method '{auth}' is not supported")
