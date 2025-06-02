from sqlpinger.core.auth.base import AuthStrategy


class WindowsAuth(AuthStrategy):
    ''' Connection using the current Windows user '''
    def __init__(self, driver: str, timeout_in_seconds: int):
        self.driver = driver
        self.timeout_in_seconds = timeout_in_seconds

    def get_connection_string(self, server: str, database: str) -> str:
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
            f"Connection Timeout={self.timeout_in_seconds};"
        )
