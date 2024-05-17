from properties.properties import (
    NotificationChannelBaseProperties,
    TelegramNotificationProperties,
)
from notifications.interfaces.notifcation_channel import INotificationChannel
from notifications.channels.telegram_notification_channel import (
    TelegramNotificationChannel,
)


class NotificationService:
    def __init__(self, properties: NotificationChannelBaseProperties) -> None:
        self._channel = self._get_channel(properties)

    def _get_channel(
        self, properties: NotificationChannelBaseProperties
    ) -> INotificationChannel:
        if isinstance(properties, TelegramNotificationProperties):
            return TelegramNotificationChannel(properties)

        raise ValueError("ERROR: The communication channel does not exist.")

    def send_notification(self, title: str, message: str) -> None:
        self._channel.send_message(title, message)
