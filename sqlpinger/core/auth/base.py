from abc import ABC, abstractmethod
from typing import List
from enum import Enum


class AuthStrategy(ABC):
    @abstractmethod
    def get_connection_string(self, server: str, database: str) -> str: pass


class ListableEnum(Enum):
    @classmethod
    def to_list(cls) -> List[str]:
        return [t.value for t in cls]
