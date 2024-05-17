import asyncio
import telegram
from notifications.interfaces.notifcation_channel import INotificationChannel
from notifications.properties.properties import TelegramNotificationProperties


class TelegramNotificationChannel(INotificationChannel):
    def __init__(self, properties: TelegramNotificationProperties) -> None:
        self._channel_id = properties.chat_id
        self._token = properties.token
        self._bot = telegram.Bot(self._token)

    async def async_send_message(self, title: str, message: str) -> None:
        async with self._bot:
            await self._bot.send_message(
                text=f"{title}\n{message}", chat_id=self._channel_id
            )

    def send_message(self, title: str, message: str) -> None:
        asyncio.run(self.async_send_message(title, message))
