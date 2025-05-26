from sqlpinger.core.auth.base import AuthStrategy


class AzureADInteractive(AuthStrategy):
    def __init__(self, driver: str):
        self.driver = driver

    def get_connection_string(self, server: str, database: str) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Authentication=ActiveDirectoryInteractive;"
        )
