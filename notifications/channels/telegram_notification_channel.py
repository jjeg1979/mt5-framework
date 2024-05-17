from notifications.interfaces.notifcation_channel import INotificationChannel
from notifications.properties.properties import TelegramNotificationProperties


class TelegramNotificationChannel(INotificationChannel):
    def __init__(self, properties: TelegramNotificationProperties) -> None:
        self._channel_id = properties.chat_id
        self._token = properties.token

    def send_message(self, title: str, message: str) -> None:
        ...
