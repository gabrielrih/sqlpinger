import psycopg2

from sqlpinger.core.connection import ConnectionManager
from sqlpinger.util.logger import Logger


class PostgresConnectionManager(ConnectionManager):
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
        self.conn = psycopg2.connect(self.conn_str, connect_timeout=self.timeout)
        self.logger.info("✅ Connection is healthy")

    def is_connected(self) -> bool:
        return self.conn is not None and self.conn.closed == 0

    def disconnect(self) -> None:
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
