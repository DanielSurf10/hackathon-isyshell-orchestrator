import asyncio
from typing import Any

from .base import NotificationChannel


class AlertDispatcher:
    def __init__(self, channels: list[NotificationChannel] | None = None) -> None:
        self.channels = channels or []

    def register(self, channel: NotificationChannel) -> None:
        self.channels.append(channel)

    async def dispatch(self, payload: dict[str, Any]) -> None:
        if not self.channels:
            return

        await asyncio.gather(
            *(channel.send(payload) for channel in self.channels),
            return_exceptions=True,
        )
