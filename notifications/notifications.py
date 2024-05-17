from notifications.interfaces.notifcation_channel import INotificationChannel
from properties.properties import (
    NotificationChannelBaseProperties,
    TelegramNotificationProperties,
)


class NotificationService:
    def __init__(self, channel: INotificationChannel) -> None:
        self._channel = channel

    def _get_channel(
        self, properties: NotificationChannelBaseProperties
    ) -> INotificationChannel:
        if isinstance(properties, TelegramNotificationProperties):
            ...
        raise NotImplementedError("ERROR: Communication Channel not implemented")

    def send_notification(self, title: str, message: str) -> None:
        self._channel.send_message(title, message)
