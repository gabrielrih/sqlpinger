from abc import ABC, abstractmethod

from sqlpinger.util.logger import Logger


CONNECTION_HEALTHY_MESSAGE = "Connection is healthy"


class ConnectionManager(ABC):
    @abstractmethod
    def execute(self, sql: str) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> None: ...


class LazyConnectionManager(ConnectionManager):
    def __init__(self, conn_str: str, timeout: int) -> None:
        self.conn_str = conn_str
        self.timeout = timeout
        self.conn = None
        self.logger = Logger.get_logger(self.__class__.__module__)

    def execute(self, sql: str) -> None:
        if not self.is_connected():
            self.connect()
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
        finally:
            try:
                cursor.close()
            except Exception as exc:
                self.logger.debug(f"Error while closing cursor: {exc}")

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    def disconnect(self) -> None:
        if not self.conn:
            return

        try:
            self.conn.close()
        except Exception as exc:
            self.logger.debug(f"Error while closing connection: {exc}")
        finally:
            self.conn = None
