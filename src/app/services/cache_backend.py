from abc import ABC, abstractmethod
from typing import Optional

class CacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, data: bytes, expire: int = None) -> None:
        """Set value in cache with optional expiration"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        pass