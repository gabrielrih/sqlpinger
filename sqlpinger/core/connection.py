import pyodbc

from sqlpinger.util.logger import Logger


class ConnectionManager:
    def __init__(self, conn_str: str, timeout: int):
        self.conn_str = conn_str
        self.timeout = timeout
        self.conn = None
        self.logger = Logger.get_logger(__name__)

    def execute(self, sql: str) -> None:
        if not self.is_connected():
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute(sql)

    def connect(self):
        self.conn = pyodbc.connect(self.conn_str, timeout=self.timeout)
        self.logger.info("✅ Connection is healthy")

    def is_connected(self) -> bool:
        return self.conn is not None and not self.conn.closed

    def disconnect(self) -> None:
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
