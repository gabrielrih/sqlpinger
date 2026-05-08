from urllib.parse import quote

from sqlpinger.core.auth.base import AuthStrategy


class PostgresSqlAuth(AuthStrategy):
    def __init__(self, username: str, password: str, port: int, sslmode: str, timeout_in_seconds: int):
        self.username = username
        self.password = password
        self.port = port
        self.sslmode = sslmode
        self.timeout_in_seconds = timeout_in_seconds

    def get_connection_string(self, server: str, database: str) -> str:
        user = quote(self.username, safe='')
        pwd = quote(self.password, safe='')
        db = quote(database, safe='')
        return (
            f"postgresql://{user}:{pwd}@{server}:{self.port}/{db}"
            f"?connect_timeout={self.timeout_in_seconds}&sslmode={self.sslmode}"
        )
