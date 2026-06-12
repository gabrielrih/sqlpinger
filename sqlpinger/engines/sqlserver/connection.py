import pyodbc

from sqlpinger.core.connection import CONNECTION_HEALTHY_MESSAGE, LazyConnectionManager


class SqlServerConnectionManager(LazyConnectionManager):
    def connect(self) -> None:
        self.conn = pyodbc.connect(self.conn_str, timeout=self.timeout)
        self.logger.info(CONNECTION_HEALTHY_MESSAGE)

    def is_connected(self) -> bool:
        return self.conn is not None and not self.conn.closed
