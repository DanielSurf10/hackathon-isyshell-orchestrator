from abc import ABC, abstractmethod
from typing import Any


class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError
