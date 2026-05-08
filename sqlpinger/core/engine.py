from abc import ABC, abstractmethod

from sqlpinger.core.connection import ConnectionManager


class Engine(ABC):
    @abstractmethod
    def build_heartbeat_sql(self, seconds: int) -> str: ...

    @abstractmethod
    def create_connection_manager(self, conn_str: str, timeout: int) -> ConnectionManager: ...
