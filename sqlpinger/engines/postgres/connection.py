import psycopg2

from sqlpinger.core.connection import CONNECTION_HEALTHY_MESSAGE, LazyConnectionManager


class PostgresConnectionManager(LazyConnectionManager):
    def connect(self) -> None:
        self.conn = psycopg2.connect(self.conn_str, connect_timeout=self.timeout)
        self.logger.info(CONNECTION_HEALTHY_MESSAGE)

    def is_connected(self) -> bool:
        return self.conn is not None and self.conn.closed == 0
