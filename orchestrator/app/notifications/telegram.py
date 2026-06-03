import os
from typing import Any

import httpx

from .base import NotificationChannel


class TelegramNotificationChannel(NotificationChannel):
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    def _build_message(self, payload: dict[str, Any]) -> str:
        script_id = payload.get("script_id", "-")
        target_container = payload.get("target_container", "-")
        status = payload.get("status", "-")
        output_error_log = payload.get("output_error_log", "") or "-"
        timestamp = payload.get("timestamp", "-")

        return (
            "\n"
            "[IsyShell Alert]\n"
            f"Script: {script_id}\n"
            f"Container: {target_container}\n"
            f"Status: {status}\n"
            f"Timestamp: {timestamp}\n"
            f"Error: {output_error_log}"
        )

    async def send(self, payload: dict[str, Any]) -> None:
        if not self.bot_token or not self.chat_id:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        message = self._build_message(payload)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
            )
            response.raise_for_status()
