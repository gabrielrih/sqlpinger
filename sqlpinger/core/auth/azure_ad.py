from sqlpinger.core.auth.base import AuthStrategy


class AzureADInteractive(AuthStrategy):
    def __init__(self, driver: str, timeout_in_seconds: int):
        self.driver = driver
        self.timeout_in_seconds = timeout_in_seconds

    def get_connection_string(self, server: str, database: str) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Authentication=ActiveDirectoryInteractive;"
            f"Connection Timeout={self.timeout_in_seconds};"
        )
