from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    @abstractmethod
    def get_connection_string(self, server: str, database: str) -> str:
        pass
