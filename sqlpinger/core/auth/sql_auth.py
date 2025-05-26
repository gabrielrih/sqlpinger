from sqlpinger.core.auth.base import AuthStrategy


class SqlAuth(AuthStrategy):
    def __init__(self, username: str, password: str, driver: str):
        self.username = username
        self.password = password
        self.driver = driver

    def get_connection_string(self, server: str, database: str) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        )
