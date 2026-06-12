from abc import ABC, abstractmethod
from enum import Enum


class AuthStrategy(ABC):
    @abstractmethod
    def get_connection_string(self, server: str, database: str) -> str: ...


class ListableEnum(Enum):
    @classmethod
    def to_list(cls) -> list[str]:
        return [t.value for t in cls]
