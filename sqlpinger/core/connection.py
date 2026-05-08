from abc import ABC, abstractmethod


class ConnectionManager(ABC):
    @abstractmethod
    def execute(self, sql: str) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> None: ...
